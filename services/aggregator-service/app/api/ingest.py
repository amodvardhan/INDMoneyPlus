"""Ingestion endpoints"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import logging
from app.core.database import get_db
from app.core.csv_parser import CSVParser
from app.core.normalizer import InstrumentNormalizer
from app.core.idempotency import check_idempotency, mark_as_processed
from app.core.kafka_producer import get_kafka_producer
from app.core.config import settings
from app.models.aggregator import BrokerAccount, RawStatement, NormalizedHolding
from app.schemas.aggregator import (
    CSVUploadResponse,
    EmailIngestRequest,
    BrokerAPIIngestRequest,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/csv", response_model=CSVUploadResponse)
async def ingest_csv(
    file: UploadFile = File(...),
    account_id: int = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Ingest holdings from CSV file"""
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV"
        )
    
    if not account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="account_id is required"
        )
    
    # Verify account exists
    result = await db.execute(
        select(BrokerAccount).where(BrokerAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )
    
    # Read CSV content
    content = await file.read()
    csv_content = content.decode('utf-8')
    
    # Check idempotency
    statement_hash = CSVParser.generate_statement_hash(csv_content, account_id)
    if await check_idempotency(statement_hash):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This statement has already been processed"
        )
    
    # Parse CSV
    parser = CSVParser()
    try:
        records = parser.parse(csv_content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    if not records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid records found in CSV"
        )
    
    # Store raw statement
    raw_statement = RawStatement(
        account_id=account_id,
        content_type="csv",
        payload_json={"filename": file.filename, "records": records},
        statement_hash=statement_hash
    )
    db.add(raw_statement)
    await db.flush()
    
    # Normalize and store holdings
    normalizer = InstrumentNormalizer()
    holdings_created = 0
    
    for record in records:
        # Normalize instrument
        instrument_data = await normalizer.normalize_instrument(
            db,
            ticker=record.get("ticker"),
            isin=record.get("isin"),
            exchange=record.get("exchange")
        )
        
        # Create normalized holding
        holding = NormalizedHolding(
            account_id=account_id,
            instrument_id=instrument_data.get("instrument_id") if instrument_data else None,
            isin=instrument_data.get("isin") if instrument_data else record.get("isin"),
            ticker=instrument_data.get("ticker") if instrument_data else record.get("ticker"),
            exchange=instrument_data.get("exchange") if instrument_data else record.get("exchange"),
            qty=record["qty"],
            avg_price=record.get("avg_price"),
            valuation=record.get("valuation"),
            source="csv"
        )
        db.add(holding)
        holdings_created += 1
    
    await db.commit()
    
    # Mark as processed
    await mark_as_processed(statement_hash)
    
    # Emit Kafka event
    kafka = get_kafka_producer()
    await kafka.send(
        settings.kafka_topic_holdings,
        key=str(account_id),
        value={
            "account_id": account_id,
            "statement_id": raw_statement.id,
            "holdings_count": holdings_created,
            "source": "csv"
        }
    )
    
    return CSVUploadResponse(
        statement_id=raw_statement.id,
        account_id=account_id,
        records_processed=len(records),
        holdings_created=holdings_created,
        message="CSV ingested successfully"
    )


@router.post("/email")
async def ingest_email(
    request: EmailIngestRequest,
    db: AsyncSession = Depends(get_db)
):
    """Ingest holdings from email/webhook"""
    # Verify account exists
    result = await db.execute(
        select(BrokerAccount).where(BrokerAccount.id == request.account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {request.account_id} not found"
        )
    
    # Generate statement hash if not provided
    statement_hash = request.statement_hash
    if not statement_hash:
        import hashlib
        content_str = str(request.payload_json)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()
        statement_hash = f"{request.account_id}:{content_hash}"
    
    # Check idempotency
    if await check_idempotency(statement_hash):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This statement has already been processed"
        )
    
    # Store raw statement
    raw_statement = RawStatement(
        account_id=request.account_id,
        content_type="email",
        payload_json=request.payload_json,
        statement_hash=statement_hash
    )
    db.add(raw_statement)
    await db.commit()
    await db.refresh(raw_statement)
    
    # Mark as processed
    await mark_as_processed(statement_hash)
    
    # Emit Kafka event
    kafka = get_kafka_producer()
    await kafka.send(
        settings.kafka_topic_holdings,
        key=str(request.account_id),
        value={
            "account_id": request.account_id,
            "statement_id": raw_statement.id,
            "source": "email"
        }
    )
    
    return {"message": "Email ingested successfully", "statement_id": raw_statement.id}


@router.post("/api/broker")
async def ingest_broker_api(
    request: BrokerAPIIngestRequest,
    db: AsyncSession = Depends(get_db)
):
    """Ingest holdings from broker API"""
    # Verify account exists
    result = await db.execute(
        select(BrokerAccount).where(BrokerAccount.id == request.account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {request.account_id} not found"
        )
    
    # Generate statement hash if not provided
    statement_hash = request.statement_hash
    if not statement_hash:
        import hashlib
        content_str = str(request.holdings)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()
        statement_hash = f"{request.account_id}:{content_hash}"
    
    # Check idempotency
    if await check_idempotency(statement_hash):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This statement has already been processed"
        )
    
    # Store raw statement
    raw_statement = RawStatement(
        account_id=request.account_id,
        content_type="api",
        payload_json={"broker_name": request.broker_name, "holdings": request.holdings},
        statement_hash=statement_hash
    )
    db.add(raw_statement)
    await db.flush()
    
    # Normalize and store holdings
    normalizer = InstrumentNormalizer()
    holdings_created = 0
    
    for holding_data in request.holdings:
        # Normalize instrument
        instrument_data = await normalizer.normalize_instrument(
            db,
            ticker=holding_data.get("ticker"),
            isin=holding_data.get("isin"),
            exchange=holding_data.get("exchange")
        )
        
        # Create normalized holding
        holding = NormalizedHolding(
            account_id=request.account_id,
            instrument_id=instrument_data.get("instrument_id") if instrument_data else None,
            isin=instrument_data.get("isin") if instrument_data else holding_data.get("isin"),
            ticker=instrument_data.get("ticker") if instrument_data else holding_data.get("ticker"),
            exchange=instrument_data.get("exchange") if instrument_data else holding_data.get("exchange"),
            qty=holding_data.get("qty", 0),
            avg_price=holding_data.get("avg_price"),
            valuation=holding_data.get("valuation"),
            source="api"
        )
        db.add(holding)
        holdings_created += 1
    
    await db.commit()
    
    # Mark as processed
    await mark_as_processed(statement_hash)
    
    # Emit Kafka event
    kafka = get_kafka_producer()
    await kafka.send(
        settings.kafka_topic_holdings,
        key=str(request.account_id),
        value={
            "account_id": request.account_id,
            "statement_id": raw_statement.id,
            "holdings_count": holdings_created,
            "source": "api"
        }
    )
    
    return {
        "message": "Broker API data ingested successfully",
        "statement_id": raw_statement.id,
        "holdings_created": holdings_created
    }

