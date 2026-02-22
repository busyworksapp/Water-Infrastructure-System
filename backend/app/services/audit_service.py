"""Enhanced audit logging service with middleware and comprehensive tracking"""

from typing import Any, Dict, Optional, Callable, List
from datetime import datetime, timedelta
import logging
import json
from functools import wraps

from sqlalchemy.orm import Session
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..models.audit import AuditLog
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


class AuditService:
    """Enhanced audit logging service"""
    
    # Endpoints to audit
    AUDITED_PATHS = [
        "/api/v1/devices",
        "/api/v1/sensors",
        "/api/v1/alerts",
        "/api/v1/incidents",
        "/api/v1/users",
        "/api/v1/roles",
        "/api/v1/municipalities",
        "/api/v1/pipelines",
        "/api/v1/admin",
    ]
    
    # Methods to log (write operations)
    AUDITED_METHODS = ["POST", "PUT", "DELETE", "PATCH"]
    
    def log(
        self,
        db: Session,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        description: Optional[str] = None,
        user_id: Optional[str] = None,
        municipality_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """
        Log an audit event to the database
        
        Args:
            db: Database session
            action: Action performed (create, read, update, delete, etc.)
            resource_type: Type of resource being acted upon
            resource_id: ID of the resource
            description: Human-readable description of action
            user_id: ID of the user performing the action
            municipality_id: ID of the municipality context
            ip_address: Client IP address
            user_agent: Client user agent string
            changes: Dictionary of changed fields
            metadata: Additional metadata as JSON
            status: Status of the action (success/failure)
            error_message: Error message if action failed
            
        Returns:
            AuditLog entry or None if logging failed
        """
        try:
            entry = AuditLog(
                user_id=user_id,
                municipality_id=municipality_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                changes=changes or {},
                metadata_json=metadata or {},
                status=status,
                error_message=error_message,
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)
            
            # Log to application logger
            log_msg = f"[AUDIT] {action} {resource_type}"
            if resource_id:
                log_msg += f" ({resource_id})"
            if user_id:
                log_msg += f" by user {user_id}"
            
            if status == "success":
                logger.info(log_msg)
            else:
                logger.warning(f"{log_msg}: {error_message}")
            
            return entry
        except Exception as exc:
            logger.warning(f"Audit log write failed: {exc}")
            return None
    
    def get_user_audit_trail(
        self,
        db: Session,
        user_id: int,
        limit: int = 100,
        days_back: int = 30,
    ) -> List[AuditLog]:
        """Get audit trail for a specific user"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        return db.query(AuditLog).filter(
            AuditLog.user_id == user_id,
            AuditLog.created_at >= cutoff_date,
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    def get_resource_history(
        self,
        db: Session,
        resource_type: str,
        resource_id: str,
    ) -> List[AuditLog]:
        """Get audit history for a specific resource"""
        return db.query(AuditLog).filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id,
        ).order_by(AuditLog.created_at.desc()).all()
    
    def get_failed_actions(
        self,
        db: Session,
        limit: int = 100,
        days_back: int = 7,
    ) -> List[AuditLog]:
        """Get failed audit actions for security review"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        return db.query(AuditLog).filter(
            AuditLog.status == "failure",
            AuditLog.created_at >= cutoff_date,
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    def get_action_summary(
        self,
        db: Session,
        days_back: int = 7,
    ) -> Dict[str, int]:
        """Get summary statistics of audit actions"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        actions = db.query(AuditLog.action, db.func.count()).filter(
            AuditLog.created_at >= cutoff_date,
        ).group_by(AuditLog.action).all()
        
        return {action: count for action, count in actions}
    
    @staticmethod
    def _extract_resource_type(path: str) -> str:
        """Extract resource type from API path"""
        parts = path.split("/")
        for i, part in enumerate(parts):
            if part == "api" and i + 2 < len(parts):
                return parts[i + 2]
        return "unknown"
    
    @staticmethod
    def _extract_resource_id(path: str) -> Optional[str]:
        """Extract resource ID from API path"""
        parts = path.split("/")
        if len(parts) > 4:
            candidate = parts[4]
            if candidate.isdigit():
                return candidate
        return None


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically log HTTP requests to audit log"""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request and log to audit log"""
        
        # Extract user info
        user_id = None
        if hasattr(request.state, "user"):
            user_id = request.state.user.id
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Get user agent
        user_agent = request.headers.get("user-agent", "unknown")[:255]
        
        # Check if path should be audited
        should_log = False
        for path in AuditService.AUDITED_PATHS:
            if path in request.url.path:
                should_log = True
                break
        
        should_log = should_log and request.method in AuditService.AUDITED_METHODS
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log write operations
            if should_log:
                resource_type = AuditService._extract_resource_type(request.url.path)
                resource_id = AuditService._extract_resource_id(request.url.path)
                status = "success" if response.status_code < 400 else "failure"
                error_msg = f"HTTP {response.status_code}" if response.status_code >= 400 else None
                
                db = SessionLocal()
                try:
                    audit_service.log(
                        db=db,
                        action=request.method.lower(),
                        resource_type=resource_type,
                        resource_id=resource_id,
                        user_id=user_id,
                        ip_address=client_ip,
                        user_agent=user_agent,
                        status=status,
                        error_message=error_msg,
                    )
                finally:
                    db.close()
            
            return response
            
        except Exception as e:
            # Log errors
            if should_log:
                db = SessionLocal()
                try:
                    audit_service.log(
                        db=db,
                        action=request.method.lower(),
                        resource_type=AuditService._extract_resource_type(request.url.path),
                        user_id=user_id,
                        ip_address=client_ip,
                        user_agent=user_agent,
                        status="failure",
                        error_message=str(e),
                    )
                except:
                    pass
                finally:
                    db.close()
            
            raise


def audit_log_action(action: str, resource_type: str):
    """
    Decorator for logging function calls to audit log
    
    Usage:
        @audit_log_action("create", "sensor")
        async def create_sensor(sensor_data: dict, user_id: int) -> Sensor:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = None
            error_msg = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error_msg = str(e)
                raise
            finally:
                user_id = kwargs.get("user_id")
                db = kwargs.get("db")
                
                if not db:
                    for arg in args:
                        if isinstance(arg, Session):
                            db = arg
                            break
                
                resource_id = None
                if result and hasattr(result, "id"):
                    resource_id = str(result.id)
                
                if db:
                    try:
                        changes = {}
                        if result and hasattr(result, "__dict__"):
                            for key, value in result.__dict__.items():
                                if not key.startswith("_"):
                                    changes[key] = str(value)
                        
                        audit_service.log(
                            db=db,
                            action=action,
                            resource_type=resource_type,
                            resource_id=resource_id,
                            user_id=user_id,
                            changes=changes if changes else None,
                            status="failure" if error_msg else "success",
                            error_message=error_msg,
                        )
                    except Exception as log_error:
                        logger.warning(f"Failed to log audit: {log_error}")
        
        return wrapper
    return decorator


# Global instance
audit_service = AuditService()
