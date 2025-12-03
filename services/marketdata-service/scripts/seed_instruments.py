"""Script to seed initial instruments"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.models.instrument import Instrument
from app.core.config import settings

# Create engine and session
engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


INSTRUMENTS = [
    # Indian Stocks
    {"ticker": "RELIANCE", "exchange": "NSE", "name": "Reliance Industries Ltd", "asset_class": "EQUITY", "timezone": "Asia/Kolkata"},
    {"ticker": "TCS", "exchange": "NSE", "name": "Tata Consultancy Services Ltd", "asset_class": "EQUITY", "timezone": "Asia/Kolkata"},
    {"ticker": "HDFCBANK", "exchange": "NSE", "name": "HDFC Bank Ltd", "asset_class": "EQUITY", "timezone": "Asia/Kolkata"},
    {"ticker": "INFY", "exchange": "NSE", "name": "Infosys Ltd", "asset_class": "EQUITY", "timezone": "Asia/Kolkata"},
    {"ticker": "ICICIBANK", "exchange": "NSE", "name": "ICICI Bank Ltd", "asset_class": "EQUITY", "timezone": "Asia/Kolkata"},
    
    # US Stocks
    {"ticker": "AAPL", "exchange": "NASDAQ", "name": "Apple Inc.", "asset_class": "EQUITY", "timezone": "America/New_York"},
    {"ticker": "GOOGL", "exchange": "NASDAQ", "name": "Alphabet Inc.", "asset_class": "EQUITY", "timezone": "America/New_York"},
    {"ticker": "MSFT", "exchange": "NASDAQ", "name": "Microsoft Corporation", "asset_class": "EQUITY", "timezone": "America/New_York"},
    {"ticker": "AMZN", "exchange": "NASDAQ", "name": "Amazon.com Inc.", "asset_class": "EQUITY", "timezone": "America/New_York"},
    {"ticker": "TSLA", "exchange": "NASDAQ", "name": "Tesla Inc.", "asset_class": "EQUITY", "timezone": "America/New_York"},
]


async def seed_instruments():
    """Seed instruments into the database"""
    async with AsyncSessionLocal() as session:
        for inst_data in INSTRUMENTS:
            # Check if instrument already exists
            from sqlalchemy import select
            result = await session.execute(
                select(Instrument).where(
                    Instrument.ticker == inst_data["ticker"],
                    Instrument.exchange == inst_data["exchange"]
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                instrument = Instrument(**inst_data)
                session.add(instrument)
                print(f"✓ Added {inst_data['ticker']} on {inst_data['exchange']}")
            else:
                print(f"⊘ Skipped {inst_data['ticker']} on {inst_data['exchange']} (already exists)")
        
        await session.commit()
        print(f"\n✓ Seeded {len(INSTRUMENTS)} instruments")


if __name__ == "__main__":
    asyncio.run(seed_instruments())

