from typing import Any, Generic, TypeVar
from datetime import datetime, timezone
from pydantic import BaseModel, Field

T = TypeVar("T")

class AdminResponse(BaseModel, Generic[T]):
    success: bool = True
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: T | None = None
    error: dict[str, str] | None = None

def admin_success(data: Any) -> AdminResponse[Any]:
    return AdminResponse(success=True, data=data)

def admin_error(code: str, message: str) -> AdminResponse[Any]:
    return AdminResponse(success=False, error={"code": code, "message": message})
