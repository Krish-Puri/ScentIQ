"""SCENTIQ Standard Error Categories and Application Exceptions.
Conforms to PRD Section 13.1 and 13.2 specifications.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    CONSTRAINT_UNSATISFIED = "CONSTRAINT_UNSATISFIED"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"


class AppException(HTTPException):
    """Base application exception with structured error code and field details."""

    def __init__(
        self,
        status_code: int,
        code: ErrorCode,
        message: str,
        field: Optional[str] = None,
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.field = field
        self.details = details or []


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", field: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.NOT_FOUND,
            message=message,
            field=field,
        )


class ConflictError(AppException):
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.CONFLICT,
            message=message,
            field=field,
        )


class ValidationError(AppException):
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[List[Dict[str, Any]]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            field=field,
            details=details,
        )


class ForbiddenError(AppException):
    def __init__(self, message: str = "Operation not permitted"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.FORBIDDEN,
            message=message,
        )


class AuthRequiredError(AppException):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.AUTH_REQUIRED,
            message=message,
        )


class ConstraintUnsatisfiedError(AppException):
    def __init__(self, message: str = "No candidates meet specified hard constraints"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=ErrorCode.CONSTRAINT_UNSATISFIED,
            message=message,
        )

