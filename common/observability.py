from fastapi import FastAPI

def instrument_fastapi(app: FastAPI, service_name: str):
    @app.middleware("http")
    async def log_requests(request, call_next):
        response = await call_next(request)
        return response
