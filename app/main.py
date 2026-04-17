from fastapi import FastAPI
from api.endpoints import router as api_router
from services.notification_service import client

app = FastAPI(title="Notification Service (Technical Test)")

app.include_router(api_router, prefix="/v1")

@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()
