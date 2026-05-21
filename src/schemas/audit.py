from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int
    target_user_id: int
    action: str
    detail: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
