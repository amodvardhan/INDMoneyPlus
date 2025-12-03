"""Corporate actions endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.instrument import Instrument, CorporateAction
from app.schemas.market_data import CorporateActionRead, CorporateActionCreate

router = APIRouter()


@router.post("", response_model=CorporateActionRead, status_code=status.HTTP_201_CREATED)
async def create_corporate_action(
    action_data: CorporateActionCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a corporate action (requires authentication)"""
    # Verify instrument exists
    result = await db.execute(
        select(Instrument).where(Instrument.id == action_data.instrument_id)
    )
    instrument = result.scalar_one_or_none()
    
    if not instrument:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument with id {action_data.instrument_id} not found"
        )
    
    corporate_action = CorporateAction(
        instrument_id=action_data.instrument_id,
        type=action_data.type.upper(),
        effective_date=action_data.effective_date,
        payload_json=action_data.payload_json or {}
    )
    
    db.add(corporate_action)
    await db.commit()
    await db.refresh(corporate_action)
    
    return corporate_action


@router.get("", response_model=list[CorporateActionRead])
async def list_corporate_actions(
    instrument_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    """List corporate actions, optionally filtered by instrument"""
    query = select(CorporateAction)
    
    if instrument_id:
        query = query.where(CorporateAction.instrument_id == instrument_id)
    
    query = query.order_by(CorporateAction.effective_date.desc())
    
    result = await db.execute(query)
    actions = result.scalars().all()
    
    return actions

