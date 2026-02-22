"""User preferences API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user_preference import UserPreference

router = APIRouter(prefix="/api/v1/preferences", tags=["preferences"])

class PreferenceUpdate(BaseModel):
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    alert_severity_filter: Optional[List[str]] = None
    alert_types_filter: Optional[List[str]] = None
    default_municipality_id: Optional[str] = None
    dashboard_refresh_interval: Optional[int] = None
    theme: Optional[str] = None
    default_map_zoom: Optional[int] = None
    default_map_center: Optional[dict] = None

@router.get("/")
def get_preferences(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get user preferences"""
    prefs = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id
    ).first()
    
    if not prefs:
        # Create default preferences
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    return {
        "email_notifications": prefs.email_notifications,
        "sms_notifications": prefs.sms_notifications,
        "push_notifications": prefs.push_notifications,
        "alert_severity_filter": prefs.alert_severity_filter,
        "alert_types_filter": prefs.alert_types_filter,
        "default_municipality_id": prefs.default_municipality_id,
        "dashboard_refresh_interval": prefs.dashboard_refresh_interval,
        "theme": prefs.theme,
        "default_map_zoom": prefs.default_map_zoom,
        "default_map_center": prefs.default_map_center
    }

@router.put("/")
def update_preferences(
    updates: PreferenceUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update user preferences"""
    prefs = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id
    ).first()
    
    if not prefs:
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)
    
    # Update fields
    for field, value in updates.dict(exclude_unset=True).items():
        setattr(prefs, field, value)
    
    db.commit()
    db.refresh(prefs)
    
    return {"message": "Preferences updated"}

@router.post("/reset")
def reset_preferences(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Reset preferences to defaults"""
    prefs = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id
    ).first()
    
    if prefs:
        db.delete(prefs)
        db.commit()
    
    return {"message": "Preferences reset to defaults"}
