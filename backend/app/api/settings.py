from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import get_current_super_admin, get_current_user
from ..models.system import (
    DynamicRule,
    NotificationChannel,
    NotificationChannelType,
    SchemaExpansion,
    SystemSetting,
)
from ..models.user import User

router = APIRouter(prefix="/admin", tags=["Admin Settings"])


class CreateSettingRequest(BaseModel):
    key: str
    value: Any
    municipality_id: Optional[str] = None
    description: Optional[str] = None
    is_public: bool = False


class UpdateSettingRequest(BaseModel):
    value: Any
    description: Optional[str] = None
    is_public: Optional[bool] = None


class CreateChannelRequest(BaseModel):
    municipality_id: Optional[str] = None
    name: str
    channel_type: str
    config: dict = Field(default_factory=dict)


class UpdateChannelRequest(BaseModel):
    name: Optional[str] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None


class CreateRuleRequest(BaseModel):
    name: str
    description: Optional[str] = None
    municipality_id: Optional[str] = None
    rule_type: str
    sensor_type_id: Optional[str] = None
    conditions: list[dict] = Field(default_factory=list)
    condition_logic: str = "AND"
    alert_severity: str
    alert_type: str
    alert_template: dict = Field(default_factory=dict)
    priority: int = 100
    cooldown_seconds: int = 300


class UpdateRuleRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[list[dict]] = None
    condition_logic: Optional[str] = None
    alert_severity: Optional[str] = None
    alert_type: Optional[str] = None
    alert_template: Optional[dict] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    cooldown_seconds: Optional[int] = None


class CreateSchemaExpansionRequest(BaseModel):
    municipality_id: Optional[str] = None
    table_name: str
    columns_definition: list[dict] = Field(default_factory=list)
    notes: Optional[str] = None


@router.get("/settings")
async def get_settings(
    municipality_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(SystemSetting)
    if current_user.is_super_admin:
        if municipality_id:
            query = query.filter(SystemSetting.municipality_id == municipality_id)
    else:
        query = query.filter(
            (SystemSetting.is_public.is_(True))
            | (SystemSetting.municipality_id == current_user.municipality_id)
            | (SystemSetting.municipality_id.is_(None))
        )

    settings = query.order_by(SystemSetting.key.asc()).all()
    return [
        {
            "id": item.id,
            "municipality_id": item.municipality_id,
            "key": item.key,
            "value": item.value,
            "description": item.description,
            "is_public": item.is_public,
            "updated_at": item.updated_at.isoformat(),
        }
        for item in settings
    ]


@router.post("/settings")
async def create_setting(
    request: CreateSettingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    existing = (
        db.query(SystemSetting)
        .filter(
            SystemSetting.key == request.key,
            SystemSetting.municipality_id == request.municipality_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Setting key already exists in this scope")

    setting = SystemSetting(
        municipality_id=request.municipality_id,
        key=request.key,
        value=request.value,
        description=request.description,
        is_public=request.is_public,
    )
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return {"id": setting.id, "key": setting.key}


@router.put("/settings/{setting_id}")
async def update_setting(
    setting_id: str,
    request: UpdateSettingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    setting = db.query(SystemSetting).filter(SystemSetting.id == setting_id).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")

    setting.value = request.value
    if request.description is not None:
        setting.description = request.description
    if request.is_public is not None:
        setting.is_public = request.is_public
    setting.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Setting updated"}


@router.delete("/settings/{setting_id}")
async def delete_setting(
    setting_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    setting = db.query(SystemSetting).filter(SystemSetting.id == setting_id).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")

    db.delete(setting)
    db.commit()
    return {"message": "Setting deleted"}


@router.get("/notification-channels")
async def get_notification_channels(
    municipality_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(NotificationChannel)

    if not current_user.is_super_admin:
        query = query.filter(
            (NotificationChannel.municipality_id == current_user.municipality_id)
            | (NotificationChannel.municipality_id.is_(None))
        )
    elif municipality_id:
        query = query.filter(NotificationChannel.municipality_id == municipality_id)

    channels = query.order_by(NotificationChannel.name.asc()).all()
    return [
        {
            "id": channel.id,
            "municipality_id": channel.municipality_id,
            "name": channel.name,
            "channel_type": channel.channel_type.value,
            "config": channel.config,
            "is_active": channel.is_active,
            "created_at": channel.created_at.isoformat(),
        }
        for channel in channels
    ]


@router.post("/notification-channels")
async def create_notification_channel(
    request: CreateChannelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        if request.municipality_id not in (None, current_user.municipality_id):
            raise HTTPException(status_code=403, detail="Access denied")

    try:
        channel_type = NotificationChannelType(request.channel_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid channel type: {request.channel_type}")

    channel = NotificationChannel(
        municipality_id=request.municipality_id or current_user.municipality_id,
        name=request.name,
        channel_type=channel_type,
        config=request.config,
        is_active=True,
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return {"id": channel.id, "name": channel.name, "channel_type": channel.channel_type.value}


@router.put("/notification-channels/{channel_id}")
async def update_notification_channel(
    channel_id: str,
    request: UpdateChannelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    channel = db.query(NotificationChannel).filter(NotificationChannel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    if not current_user.is_super_admin and channel.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")

    for field, value in request.dict(exclude_unset=True).items():
        setattr(channel, field, value)

    channel.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Channel updated"}


@router.delete("/notification-channels/{channel_id}")
async def delete_notification_channel(
    channel_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    channel = db.query(NotificationChannel).filter(NotificationChannel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    db.delete(channel)
    db.commit()
    return {"message": "Channel deleted"}


@router.get("/rules")
async def get_dynamic_rules(
    municipality_id: Optional[str] = None,
    sensor_type_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(DynamicRule)

    if current_user.is_super_admin:
        if municipality_id:
            query = query.filter(DynamicRule.municipality_id == municipality_id)
    else:
        query = query.filter(
            (DynamicRule.municipality_id == current_user.municipality_id)
            | (DynamicRule.municipality_id.is_(None))
        )

    if sensor_type_id:
        query = query.filter(DynamicRule.sensor_type_id == sensor_type_id)
    if is_active is not None:
        query = query.filter(DynamicRule.is_active == is_active)

    rules = query.order_by(DynamicRule.priority.asc(), DynamicRule.created_at.desc()).all()
    return [
        {
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "municipality_id": rule.municipality_id,
            "rule_type": rule.rule_type,
            "sensor_type_id": rule.sensor_type_id,
            "conditions": rule.conditions,
            "condition_logic": rule.condition_logic,
            "alert_severity": rule.alert_severity,
            "alert_type": rule.alert_type,
            "alert_template": rule.alert_template,
            "is_active": rule.is_active,
            "priority": rule.priority,
            "cooldown_seconds": rule.cooldown_seconds,
            "created_at": rule.created_at.isoformat(),
        }
        for rule in rules
    ]


@router.post("/rules")
async def create_dynamic_rule(
    request: CreateRuleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    rule = DynamicRule(
        municipality_id=request.municipality_id,
        name=request.name,
        description=request.description,
        rule_type=request.rule_type,
        sensor_type_id=request.sensor_type_id,
        conditions=request.conditions,
        condition_logic=request.condition_logic.upper(),
        alert_severity=request.alert_severity.lower(),
        alert_type=request.alert_type.lower(),
        alert_template=request.alert_template,
        is_active=True,
        priority=request.priority,
        cooldown_seconds=request.cooldown_seconds,
        created_by=current_user.id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return {"id": rule.id, "name": rule.name}


@router.put("/rules/{rule_id}")
async def update_dynamic_rule(
    rule_id: str,
    request: UpdateRuleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    rule = db.query(DynamicRule).filter(DynamicRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    update_data = request.dict(exclude_unset=True)
    if "alert_severity" in update_data:
        update_data["alert_severity"] = update_data["alert_severity"].lower()
    if "alert_type" in update_data:
        update_data["alert_type"] = update_data["alert_type"].lower()
    if "condition_logic" in update_data:
        update_data["condition_logic"] = update_data["condition_logic"].upper()

    for field, value in update_data.items():
        setattr(rule, field, value)

    rule.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Rule updated"}


@router.delete("/rules/{rule_id}")
async def delete_dynamic_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    rule = db.query(DynamicRule).filter(DynamicRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(rule)
    db.commit()
    return {"message": "Rule deleted"}


def _build_create_table_sql(table_name: str, columns_definition: list[dict]) -> str:
    allowed_types = {
        "string": "VARCHAR(255)",
        "text": "TEXT",
        "int": "INT",
        "float": "DOUBLE",
        "bool": "BOOLEAN",
        "json": "JSON",
        "datetime": "DATETIME",
    }

    if not table_name.replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="Invalid table_name")

    columns_sql = ["id VARCHAR(36) PRIMARY KEY"]
    for column in columns_definition:
        name = str(column.get("name", "")).strip()
        col_type = str(column.get("type", "")).strip().lower()
        nullable = bool(column.get("nullable", True))

        if not name or not name.replace("_", "").isalnum():
            raise HTTPException(status_code=400, detail=f"Invalid column name: {name}")
        if col_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Unsupported column type: {col_type}")

        null_clause = "" if nullable else " NOT NULL"
        columns_sql.append(f"{name} {allowed_types[col_type]}{null_clause}")

    return f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns_sql)})"


@router.get("/schema-expansions")
async def list_schema_expansions(
    municipality_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    query = db.query(SchemaExpansion)
    if municipality_id:
        query = query.filter(SchemaExpansion.municipality_id == municipality_id)
    items = query.order_by(SchemaExpansion.created_at.desc()).all()
    return [
        {
            "id": item.id,
            "municipality_id": item.municipality_id,
            "table_name": item.table_name,
            "columns_definition": item.columns_definition,
            "status": item.status,
            "requested_by": item.requested_by,
            "approved_by": item.approved_by,
            "notes": item.notes,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
        }
        for item in items
    ]


@router.post("/schema-expansions")
async def request_schema_expansion(
    request: CreateSchemaExpansionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    item = SchemaExpansion(
        municipality_id=request.municipality_id,
        table_name=request.table_name,
        columns_definition=request.columns_definition,
        status="pending",
        requested_by=current_user.id,
        notes=request.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "status": item.status}


@router.post("/schema-expansions/{expansion_id}/approve")
async def approve_schema_expansion(
    expansion_id: str,
    execute: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    item = db.query(SchemaExpansion).filter(SchemaExpansion.id == expansion_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Schema expansion not found")

    create_sql = _build_create_table_sql(item.table_name, item.columns_definition)
    if execute:
        db.execute(text(create_sql))

    item.status = "approved"
    item.approved_by = current_user.id
    item.updated_at = datetime.utcnow()
    db.commit()

    return {"id": item.id, "status": item.status, "sql": create_sql, "executed": execute}

