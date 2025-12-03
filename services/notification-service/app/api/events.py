"""Event ingestion endpoint"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.notification import EventIngestRequest
from app.core.webhook import deliver_webhook

router = APIRouter()


@router.post("/ingest")
async def ingest_event(
    event: EventIngestRequest,
    db: AsyncSession = Depends(get_db)
):
    """Ingest event from internal services and deliver to webhook subscribers"""
    await deliver_webhook(
        db,
        event.event_type,
        event.payload
    )
    
    return {
        "status": "delivered",
        "event_type": event.event_type,
        "subscribers_notified": True
    }

