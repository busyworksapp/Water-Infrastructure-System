"""Comprehensive error handling and API response utilities."""
import logging
from typing import Any, Dict, Optional
from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
import traceback

logger = logging.getLogger(__name__)


class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[Dict] = None
    timestamp: str = None
    request_id: Optional[str] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class APIError(Exception):
    """Base exception for API errors"""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class ValidationException(APIError):
    """Exception for validation errors"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details
        )


class NotFoundError(APIError):
    """Exception for not found errors"""
    def __init__(self, resource: str, resource_id: Optional[str] = None):
        message = f"{resource} not found"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND"
        )


class UnauthorizedError(APIError):
    """Exception for authentication errors"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED"
        )


class ForbiddenError(APIError):
    """Exception for authorization errors"""
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN"
        )


class ConflictError(APIError):
    """Exception for conflict errors"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            details=details
        )


class DatabaseError(APIError):
    """Exception for database errors"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details=details
        )


class ExternalServiceError(APIError):
    """Exception for external service errors (MQTT, S3, Redis, etc.)"""
    def __init__(self, service: str, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=f"{service} service error: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details or {"service": service}
        )


class RateLimitError(APIError):
    """Exception for rate limiting"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMITED"
        )


def create_error_response(
    error: Exception,
    request_id: Optional[str] = None,
    include_traceback: bool = False
) -> JSONResponse:
    """
    Create standardized error response
    
    Args:
        error: Exception that occurred
        request_id: Optional request ID for tracking
        include_traceback: Whether to include stack trace (development only)
    
    Returns:
        JSONResponse with standardized error format
    """
    if isinstance(error, APIError):
        response_data = {
            "success": False,
            "message": error.message,
            "error": {
                "code": error.error_code,
                "details": error.details
            },
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }
        status_code = error.status_code
    
    elif isinstance(error, ValidationError):
        response_data = {
            "success": False,
            "message": "Validation failed",
            "error": {
                "code": "VALIDATION_ERROR",
                "details": {
                    "errors": error.errors()
                }
            },
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    
    else:
        # Generic error handling
        response_data = {
            "success": False,
            "message": str(error) or "Internal server error",
            "error": {
                "code": "INTERNAL_ERROR",
                "details": {}
            },
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Log unexpected errors
        logger.error(
            f"Unhandled exception: {type(error).__name__}: {str(error)}",
            exc_info=True
        )
    
    # Add traceback in development
    if include_traceback and isinstance(error, Exception):
        response_data["error"]["traceback"] = traceback.format_exc()
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


def create_success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK,
    request_id: Optional[str] = None
) -> Dict:
    """
    Create standardized success response
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        request_id: Optional request ID for tracking
    
    Returns:
        Dictionary with standardized response format
    """
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id
    }


class InputSanitizer:
    """Utility for sanitizing user input"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize string input
        
        Args:
            value: String to sanitize
            max_length: Maximum allowed length
        
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            raise ValidationException("Invalid string input")
        
        # Remove leading/trailing whitespace
        value = value.strip()
        
        # Check length
        if max_length and len(value) > max_length:
            raise ValidationException(f"String exceeds maximum length of {max_length}")
        
        # Prevent empty strings
        if not value:
            raise ValidationException("String cannot be empty")
        
        return value
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize email address"""
        email = InputSanitizer.sanitize_string(email.lower(), max_length=255)
        
        # Basic email validation
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValidationException("Invalid email format")
        
        return email
    
    @staticmethod
    def sanitize_id(id_value: str, pattern: Optional[str] = None) -> str:
        """
        Sanitize ID input
        
        Args:
            id_value: ID to sanitize
            pattern: Optional regex pattern to validate against
        
        Returns:
            Sanitized ID
        """
        id_value = InputSanitizer.sanitize_string(id_value, max_length=100)
        
        # Check for SQL injection patterns
        dangerous_chars = ["'", '"', ";", "--", "/*", "*/"]
        if any(char in id_value for char in dangerous_chars):
            raise ValidationException("Invalid characters in ID")
        
        if pattern:
            import re
            if not re.match(pattern, id_value):
                raise ValidationException(f"ID format invalid (pattern: {pattern})")
        
        return id_value
    
    @staticmethod
    def sanitize_integer(value: Any, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
        """
        Sanitize integer input
        
        Args:
            value: Value to convert to int
            min_val: Minimum allowed value
            max_val: Maximum allowed value
        
        Returns:
            Sanitized integer
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationException("Invalid integer input")
        
        if min_val is not None and int_value < min_val:
            raise ValidationException(f"Value below minimum of {min_val}")
        
        if max_val is not None and int_value > max_val:
            raise ValidationException(f"Value exceeds maximum of {max_val}")
        
        return int_value
    
    @staticmethod
    def sanitize_float(value: Any, min_val: Optional[float] = None, max_val: Optional[float] = None) -> float:
        """Sanitize float input"""
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValidationException("Invalid float input")
        
        if min_val is not None and float_value < min_val:
            raise ValidationException(f"Value below minimum of {min_val}")
        
        if max_val is not None and float_value > max_val:
            raise ValidationException(f"Value exceeds maximum of {max_val}")
        
        return float_value
    
    @staticmethod
    def sanitize_json(obj: Any) -> Any:
        """
        Recursively sanitize JSON object
        
        Args:
            obj: Object to sanitize
        
        Returns:
            Sanitized object
        """
        if isinstance(obj, dict):
            return {k: InputSanitizer.sanitize_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [InputSanitizer.sanitize_json(item) for item in obj]
        elif isinstance(obj, str):
            return InputSanitizer.sanitize_string(obj, max_length=10000)
        elif isinstance(obj, (int, float, bool, type(None))):
            return obj
        else:
            raise ValidationException(f"Unsupported JSON type: {type(obj)}")
