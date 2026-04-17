import uuid
import asyncio
from fastapi import APIRouter, HTTPException, status
from models.schemas import NotificationRequest, NotificationStatusResponse
from db.session import db
from services.notification_service import process_notification_task
from core.logging_config import logger

router = APIRouter()

@router.post("/requests", status_code=status.HTTP_201_CREATED)
async def create_request(notification: NotificationRequest):
    request_id = str(uuid.uuid4())
    db[request_id] = {
        "status": "queued",
        "data": notification.model_dump()
    }
    logger.info(f"Solicitud creada: {request_id}")
    return {"id": request_id}

@router.post("/requests/{id}/process", status_code=status.HTTP_202_ACCEPTED)
async def process_request(id: str):
    if id not in db:
        raise HTTPException(status_code=404, detail="Request not found")

    if db[id]["status"] in ["processing", "sent"]:
        return {"id": id, "status": db[id]["status"]}

    asyncio.create_task(process_notification_task(id))
    return {"id": id, "status": "queued"}

@router.get("/requests/{id}", response_model=NotificationStatusResponse)
async def get_request_status(id: str):
    if id not in db:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"id": id, "status": db[id]["status"]}
