"""Audit logging utilities"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import AuditLog
from typing import Optional, Dict, Any
from datetime import datetime


async def log_audit_event(
    db: AsyncSession,
    user_id: Optional[int],
    action: str,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Log an audit event to the database"""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        ip=ip,
        user_agent=user_agent,
        log_metadata=metadata or {},
        created_at=datetime.utcnow()
    )
    db.add(audit_log)
    await db.commit()

