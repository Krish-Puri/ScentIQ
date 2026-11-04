"""SCENTIQ Standard API Response Envelope.
Strictly conforms to PRD Section 13.1.
"""
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field
from app.core.logging import request_id_ctx

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None


class Meta(BaseModel):
    request_id: str = Field(default_factory=lambda: request_id_ctx.get() or "")
    next_cursor: Optional[str] = None
    total: Optional[int] = None


class ResponseEnvelope(BaseModel, Generic[T]):
    data: Optional[T] = None
    meta: Meta = Field(default_factory=Meta)
    errors: List[ErrorDetail] = Field(default_factory=list)

    @classmethod
    def success(cls, data: T, request_id: str = "", next_cursor: Optional[str] = None, total: Optional[int] = None):
        req_id = request_id or request_id_ctx.get() or ""
        return cls(
            data=data,
            meta=Meta(request_id=req_id, next_cursor=next_cursor, total=total),
            errors=[],
        )

    @classmethod
    def error(cls, code: str, message: str, field: Optional[str] = None, request_id: str = ""):
        req_id = request_id or request_id_ctx.get() or ""
        return cls(
            data=None,
            meta=Meta(request_id=req_id),
            errors=[ErrorDetail(code=code, message=message, field=field)],
        )
