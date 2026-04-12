import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Cookie
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from redis.asyncio import Redis

from common.db import SessionLocal, engine, Base
from common.models import User, Transfer, Notification
from common.redis_utils import get_user_id_from_session, publish_notify
from common.observability import instrument_fastapi

Base.metadata.create_all(bind=engine)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

redis: Redis | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis
    redis = Redis.from_url(REDIS_URL, decode_responses=True)
    yield
    if redis:
        await redis.close()

app = FastAPI(title="Transfer Service", lifespan=lifespan)
instrument_fastapi(app, "transfer-service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TransferReq(BaseModel):
    to_username: str
    amount: int

@app.post("/transfer")
async def transfer(body: TransferReq, session: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    """Transfer money between users"""
    user_id = await get_user_id_from_session(redis, session)

    if body.amount <= 0:
        raise HTTPException(400, "Amount must be > 0")

    # Fix Deadlock by ordering locks
    receiver_pre = db.execute(select(User).where(User.username == body.to_username)).scalar_one_or_none()
    if not receiver_pre:
        raise HTTPException(404, "Receiver not found")
        
    if receiver_pre.id == user_id:
        raise HTTPException(400, "Cannot transfer to yourself")

    first_id = min(user_id, receiver_pre.id)
    second_id = max(user_id, receiver_pre.id)

    db.execute(select(User).where(User.id == first_id).with_for_update()).scalar_one_or_none()
    db.execute(select(User).where(User.id == second_id).with_for_update()).scalar_one_or_none()

    sender = db.get(User, user_id)
    receiver = db.get(User, receiver_pre.id)

    if not sender:
        raise HTTPException(404, "Sender not found")

    if sender.balance < body.amount:
        raise HTTPException(400, "Insufficient balance")

    # Update balances + save transfer + notifications within transaction
    sender.balance -= body.amount
    receiver.balance += body.amount

    t = Transfer(from_user=sender.id, to_user=receiver.id, amount=body.amount)
    db.add(t)

    msg_sender = f"Bạn đã chuyển {body.amount} đến {receiver.username}"
    msg_receiver = f"Bạn nhận {body.amount} từ {sender.username}"

    db.add(Notification(user_id=sender.id, message=msg_sender))
    db.add(Notification(user_id=receiver.id, message=msg_receiver))

    db.commit()

    # Realtime push via redis pubsub (after commit to ensure data consistency)
    await publish_notify(redis, receiver.id, msg_receiver)

    return {"ok": True, "from": sender.username, "to": receiver.username, "amount": body.amount}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if redis:
            await redis.ping()
        db = SessionLocal()
        try:
            db.execute(select(1))
            db_status = "ok"
        except Exception:
            db_status = "error"
        finally:
            db.close()
        
        redis_status = "ok" if redis else "error"
        
        if db_status == "ok" and redis_status == "ok":
            return {"status": "healthy", "service": "transfer-service", "database": db_status, "redis": redis_status}
        else:
            raise HTTPException(503, detail={"status": "unhealthy", "database": db_status, "redis": redis_status})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(503, detail=f"Health check failed: {str(e)}")
