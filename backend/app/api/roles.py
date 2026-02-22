from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..core.database import get_db
from ..core.security import get_current_super_admin
from ..models.user import User, Role, Permission

router = APIRouter(prefix="/roles", tags=["Roles & Permissions"])


class CreateRoleRequest(BaseModel):
    name: str
    code: str
    description: Optional[str] = None


class UpdateRoleRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CreatePermissionRequest(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None


@router.get("/")
async def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    roles = db.query(Role).all()
    return [{
        "id": r.id,
        "name": r.name,
        "code": r.code,
        "description": r.description,
        "is_system": r.is_system,
        "permissions": [{"id": p.id, "code": p.code, "name": p.name} for p in r.permissions],
        "created_at": r.created_at.isoformat()
    } for r in roles]


@router.post("/")
async def create_role(
    request: CreateRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    existing = db.query(Role).filter(
        (Role.name == request.name) | (Role.code == request.code)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role name or code already exists")

    role = Role(
        name=request.name,
        code=request.code,
        description=request.description,
        is_system=False
    )
    db.add(role)
    db.commit()
    db.refresh(role)

    return {"id": role.id, "name": role.name, "code": role.code}


@router.put("/{role_id}")
async def update_role(
    role_id: str,
    request: UpdateRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system role")

    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role, field, value)

    db.commit()
    return {"message": "Role updated"}


@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system role")

    db.delete(role)
    db.commit()
    return {"message": "Role deleted"}


@router.post("/{role_id}/permissions/{permission_id}")
async def assign_permission_to_role(
    role_id: str,
    permission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    if permission not in role.permissions:
        role.permissions.append(permission)
        db.commit()

    return {"message": "Permission assigned"}


@router.delete("/{role_id}/permissions/{permission_id}")
async def remove_permission_from_role(
    role_id: str,
    permission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if permission and permission in role.permissions:
        role.permissions.remove(permission)
        db.commit()

    return {"message": "Permission removed"}


@router.get("/permissions")
async def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    permissions = db.query(Permission).all()
    return [{
        "id": p.id,
        "name": p.name,
        "code": p.code,
        "description": p.description,
        "resource": p.resource,
        "action": p.action,
        "created_at": p.created_at.isoformat()
    } for p in permissions]


@router.post("/permissions")
async def create_permission(
    request: CreatePermissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    existing = db.query(Permission).filter(Permission.code == request.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Permission code already exists")

    permission = Permission(
        name=request.name,
        code=request.code,
        description=request.description,
        resource=request.resource,
        action=request.action
    )
    db.add(permission)
    db.commit()
    db.refresh(permission)

    return {"id": permission.id, "code": permission.code}


@router.delete("/permissions/{permission_id}")
async def delete_permission(
    permission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    db.delete(permission)
    db.commit()
    return {"message": "Permission deleted"}

