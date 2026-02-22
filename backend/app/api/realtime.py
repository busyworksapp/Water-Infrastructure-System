from typing import Optional

from fastapi import APIRouter, Depends, Query

from ..core.security import get_current_user
from ..models.user import User
from ..websocket.manager import ws_manager

router = APIRouter(prefix="/realtime", tags=["Real-time"])


@router.get("/events/replay")
async def replay_events(
    municipality_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_super_admin:
        target = municipality_id or "global"
    else:
        target = current_user.municipality_id
    return {
        "municipality_id": target,
        "events": ws_manager.get_events(target, limit=limit),
    }

