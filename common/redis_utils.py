import uuid
import json
from fastapi import HTTPException
from redis.asyncio import Redis

async def create_session(redis: Redis, user_id: int) -> str:
    session_id = str(uuid.uuid4())
    await redis.set(f"session:{session_id}", str(user_id), ex=86400)
    return session_id

async def get_user_id_from_session(redis: Redis, session_id: str | None) -> int:
    if not session_id:
        raise HTTPException(status_code=401, detail="Unauthorized: No session token provided")
    user_id_str = await redis.get(f"session:{session_id}")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid session")
    return int(user_id_str)

async def set_presence(redis: Redis, user_id: int, online: bool):
    if online:
        await redis.set(f"presence:{user_id}", "1", ex=60)
    else:
        await redis.delete(f"presence:{user_id}")

async def publish_notify(redis: Redis, user_id: int, message: str):
    await redis.publish(f"notify:{user_id}", message)
