from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from ..models.system import ProtocolConfiguration, ProtocolType


class ProtocolService:
    @staticmethod
    def normalize_protocol(value: str | ProtocolType) -> ProtocolType:
        if isinstance(value, ProtocolType):
            return value
        return ProtocolType(str(value).lower())

    def is_protocol_enabled(
        self,
        db: Session,
        protocol: str | ProtocolType,
        municipality_id: Optional[str] = None,
    ) -> bool:
        normalized = self.normalize_protocol(protocol)

        if municipality_id:
            scoped = (
                db.query(ProtocolConfiguration)
                .filter(
                    ProtocolConfiguration.protocol == normalized,
                    ProtocolConfiguration.municipality_id == municipality_id,
                )
                .first()
            )
            if scoped:
                return bool(scoped.is_enabled)

        global_cfg = (
            db.query(ProtocolConfiguration)
            .filter(
                ProtocolConfiguration.protocol == normalized,
                ProtocolConfiguration.municipality_id.is_(None),
            )
            .first()
        )
        if global_cfg:
            return bool(global_cfg.is_enabled)

        # Default to enabled if no policy exists yet.
        return True

    def get_protocol_settings(
        self,
        db: Session,
        protocol: str | ProtocolType,
        municipality_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        normalized = self.normalize_protocol(protocol)

        if municipality_id:
            scoped = (
                db.query(ProtocolConfiguration)
                .filter(
                    ProtocolConfiguration.protocol == normalized,
                    ProtocolConfiguration.municipality_id == municipality_id,
                )
                .first()
            )
            if scoped:
                return scoped.settings or {}

        global_cfg = (
            db.query(ProtocolConfiguration)
            .filter(
                ProtocolConfiguration.protocol == normalized,
                ProtocolConfiguration.municipality_id.is_(None),
            )
            .first()
        )
        return (global_cfg.settings or {}) if global_cfg else {}


protocol_service = ProtocolService()
