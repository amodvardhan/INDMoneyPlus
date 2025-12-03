"""Reconciliation job for detecting discrepancies"""
import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.core.kafka_producer import get_kafka_producer
from app.core.config import settings
from app.models.aggregator import (
    BrokerAccount,
    NormalizedHolding,
    ReconciliationException
)

logger = logging.getLogger(__name__)


class ReconciliationJob:
    """Job to reconcile holdings and detect discrepancies"""
    
    def __init__(self):
        self.running = False
    
    async def run(self):
        """Run reconciliation job"""
        if self.running:
            logger.warning("Reconciliation job already running")
            return
        
        self.running = True
        logger.info("Starting reconciliation job")
        
        try:
            async with AsyncSessionLocal() as db:
                # Get all accounts
                result = await db.execute(select(BrokerAccount))
                accounts = result.scalars().all()
                
                for account in accounts:
                    await self._reconcile_account(db, account)
                
                await db.commit()
        except Exception as e:
            logger.error(f"Error in reconciliation job: {e}")
        finally:
            self.running = False
            logger.info("Reconciliation job completed")
    
    async def _reconcile_account(self, db: AsyncSession, account: BrokerAccount):
        """Reconcile holdings for a single account"""
        # Get all holdings for account
        result = await db.execute(
            select(NormalizedHolding).where(
                NormalizedHolding.account_id == account.id
            )
        )
        holdings = result.scalars().all()
        
        # Check for discrepancies
        issues = []
        
        for holding in holdings:
            # Check for missing instrument_id
            if not holding.instrument_id and (holding.isin or holding.ticker):
                issues.append({
                    "type": "missing_instrument_mapping",
                    "holding_id": holding.id,
                    "message": f"Instrument not mapped: {holding.ticker or holding.isin}",
                    "payload": {
                        "ticker": holding.ticker,
                        "isin": holding.isin,
                        "exchange": holding.exchange
                    }
                })
            
            # Check for negative quantities
            if holding.qty < 0:
                issues.append({
                    "type": "negative_quantity",
                    "holding_id": holding.id,
                    "message": f"Negative quantity detected: {holding.qty}",
                    "payload": {
                        "qty": holding.qty,
                        "ticker": holding.ticker
                    }
                })
            
            # Check for missing valuation
            if not holding.valuation and holding.qty > 0:
                issues.append({
                    "type": "missing_valuation",
                    "holding_id": holding.id,
                    "message": f"Missing valuation for holding: {holding.ticker or holding.isin}",
                    "payload": {
                        "ticker": holding.ticker,
                        "isin": holding.isin,
                        "qty": holding.qty
                    }
                })
        
        # Create reconciliation exceptions for issues
        kafka = get_kafka_producer()
        
        for issue in issues:
            # Check if exception already exists
            result = await db.execute(
                select(ReconciliationException).where(
                    ReconciliationException.account_id == account.id,
                    ReconciliationException.message == issue["message"],
                    ReconciliationException.resolved == False
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                exception = ReconciliationException(
                    account_id=account.id,
                    message=issue["message"],
                    payload_json=issue["payload"]
                )
                db.add(exception)
                await db.flush()
                
                # Emit Kafka event
                await kafka.send(
                    settings.kafka_topic_reconciliation,
                    key=str(account.id),
                    value={
                        "account_id": account.id,
                        "exception_id": exception.id,
                        "type": issue["type"],
                        "message": issue["message"],
                        "payload": issue["payload"]
                    }
                )
        
        if issues:
            logger.info(f"Found {len(issues)} reconciliation issues for account {account.id}")


async def run_reconciliation_job():
    """Run reconciliation job periodically"""
    job = ReconciliationJob()
    while True:
        try:
            await job.run()
            # Run every hour
            await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"Error in reconciliation job loop: {e}")
            await asyncio.sleep(60)

