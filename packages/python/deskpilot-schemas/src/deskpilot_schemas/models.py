from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateConversationRequest(StrictModel):
    device_id: UUID
    initial_message: str = Field(min_length=1, max_length=4000)


class SendMessageRequest(StrictModel):
    content: str = Field(min_length=1, max_length=4000)


class ConsentRequest(StrictModel):
    scope: Literal["diagnostic", "remediation", "remote_session"]
    decision: Literal["granted", "denied"]
    expires_at: datetime
