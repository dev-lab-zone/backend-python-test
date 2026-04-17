from typing import Literal
from pydantic import BaseModel, Field

class NotificationRequest(BaseModel):
    to: str = Field(..., example="user@example.com")
    message: str = Field(..., example="Hello there!")
    type: Literal["email", "sms", "push"] = Field(..., example="email")

class NotificationStatusResponse(BaseModel):
    id: str
    status: Literal["queued", "processing", "sent", "failed"]
