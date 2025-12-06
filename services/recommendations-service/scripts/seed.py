"""Seed script for recommendations service - DEPRECATED
This script is kept for testing purposes only.
Production recommendations are now generated dynamically using AI agents.
To use this script for testing, run it manually.
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.models.recommendation import Recommendation, RecommendationSource, RecommendationType
from app.core.config import settings

# Create engine and session
engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Sample sources
SOURCES = [
    {
        "name": "Morgan Stanley Research",
        "source_type": "research_firm",
        "credibility_score": 0.95,
        "is_verified": "true"
    },
    {
        "name": "Goldman Sachs",
        "source_type": "research_firm",
        "credibility_score": 0.95,
        "is_verified": "true"
    },
    {
        "name": "Economic Times",
        "source_type": "news",
        "credibility_score": 0.85,
        "is_verified": "true"
    },
    {
        "name": "Moneycontrol",
        "source_type": "news",
        "credibility_score": 0.80,
        "is_verified": "true"
    },
    {
        "name": "CNBC TV18",
        "source_type": "news",
        "credibility_score": 0.82,
        "is_verified": "true"
    },
    {
        "name": "Kotak Securities",
        "source_type": "research_firm",
        "credibility_score": 0.88,
        "is_verified": "true"
    },
    {
        "name": "ICICI Direct",
        "source_type": "research_firm",
        "credibility_score": 0.87,
        "is_verified": "true"
    },
]

# Sample recommendations
RECOMMENDATIONS = [
    # Buy recommendations
    {
        "ticker": "RELIANCE",
        "exchange": "NSE",
        "recommendation_type": RecommendationType.STRONG_BUY,
        "target_price": 2850.0,
        "current_price": 2650.0,
        "reasoning": "Strong fundamentals, expanding retail and digital businesses. Jio's growth trajectory and renewable energy investments position well for long-term value creation.",
        "risk_level": "medium",
        "confidence_score": 0.85,
        "source_name": "Morgan Stanley Research",
        "source_type": "research_firm",
        "source_url": "https://example.com/reports/reliance-2024",
    },
    {
        "ticker": "TCS",
        "exchange": "NSE",
        "recommendation_type": RecommendationType.BUY,
        "target_price": 4200.0,
        "current_price": 3850.0,
        "reasoning": "Stable revenue growth, strong client relationships, and digital transformation focus. Consistent dividend payer with healthy cash flows.",
        "risk_level": "low",
        "confidence_score": 0.80,
        "source_name": "Goldman Sachs",
        "source_type": "research_firm",
        "source_url": "https://example.com/reports/tcs-2024",
    },
    {
        "ticker": "HDFCBANK",
        "exchange": "NSE",
        "recommendation_type": RecommendationType.BUY,
        "target_price": 1850.0,
        "current_price": 1720.0,
        "reasoning": "Strong asset quality, robust capital adequacy, and leadership in retail banking. Well-positioned for credit growth cycle.",
        "risk_level": "low",
        "confidence_score": 0.82,
        "source_name": "Kotak Securities",
        "source_type": "research_firm",
    },
    {
        "ticker": "INFY",
        "exchange": "NSE",
        "recommendation_type": RecommendationType.BUY,
        "target_price": 1650.0,
        "current_price": 1520.0,
        "reasoning": "Digital services growth, large deal wins, and margin expansion. Strong positioning in cloud and AI services.",
        "risk_level": "medium",
        "confidence_score": 0.78,
        "source_name": "ICICI Direct",
        "source_type": "research_firm",
    },
    {
        "ticker": "ICICIBANK",
        "exchange": "NSE",
        "recommendation_type": RecommendationType.STRONG_BUY,
        "target_price": 1150.0,
        "current_price": 1020.0,
        "reasoning": "Excellent asset quality, strong retail franchise, and digital banking leadership. Attractive valuation relative to peers.",
        "risk_level": "medium",
        "confidence_score": 0.88,
        "source_name": "Morgan Stanley Research",
        "source_type": "research_firm",
    },
    {
        "ticker": "AAPL",
        "exchange": "NASDAQ",
        "recommendation_type": RecommendationType.BUY,
        "target_price": 195.0,
        "current_price": 180.0,
        "reasoning": "Services revenue growth, strong iPhone sales, and ecosystem lock-in. Consistent cash generation and shareholder returns.",
        "risk_level": "low",
        "confidence_score": 0.85,
        "source_name": "Goldman Sachs",
        "source_type": "research_firm",
    },
    {
        "ticker": "MSFT",
        "exchange": "NASDAQ",
        "recommendation_type": RecommendationType.STRONG_BUY,
        "target_price": 420.0,
        "current_price": 380.0,
        "reasoning": "Azure cloud growth, AI integration across products, and strong enterprise relationships. Leading position in enterprise software.",
        "risk_level": "low",
        "confidence_score": 0.90,
        "source_name": "Morgan Stanley Research",
        "source_type": "research_firm",
    },
    # Sell recommendations
    {
        "ticker": "SOME_STOCK",
        "exchange": "NSE",
        "recommendation_type": RecommendationType.SELL,
        "target_price": 450.0,
        "current_price": 520.0,
        "reasoning": "Valuation concerns, slowing growth, and competitive pressures. Consider profit booking at current levels.",
        "risk_level": "high",
        "confidence_score": 0.75,
        "source_name": "Economic Times",
        "source_type": "news",
    },
]


async def seed_recommendations():
    """Seed recommendations and sources into the database"""
    async with AsyncSessionLocal() as session:
        try:
            # Create sources
            print("Creating recommendation sources...")
            source_map = {}
            for source_data in SOURCES:
                # Check if source exists
                from sqlalchemy import select
                result = await session.execute(
                    select(RecommendationSource).where(
                        RecommendationSource.name == source_data["name"]
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    source = RecommendationSource(**source_data)
                    session.add(source)
                    await session.flush()
                    source_map[source_data["name"]] = source
                    print(f"  Created source: {source_data['name']}")
                else:
                    source_map[source_data["name"]] = existing
                    print(f"  Source already exists: {source_data['name']}")
            
            await session.commit()
            
            # Create recommendations
            print("Creating recommendations...")
            for rec_data in RECOMMENDATIONS:
                # Check if recommendation already exists
                from sqlalchemy import select
                result = await session.execute(
                    select(Recommendation).where(
                        Recommendation.ticker == rec_data["ticker"].upper(),
                        Recommendation.exchange == rec_data["exchange"].upper(),
                        Recommendation.source_id == source_map[rec_data["source_name"]].id
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    source_name = rec_data.pop("source_name")
                    source_type = rec_data.pop("source_type", None)  # Remove if present
                    source = source_map[source_name]
                    rec_data["source_id"] = source.id
                    rec_data["source_date"] = datetime.utcnow()
                    rec_data["expires_at"] = datetime.utcnow() + timedelta(days=30)
                    rec_data["is_active"] = "true"
                    
                    recommendation = Recommendation(**rec_data)
                    session.add(recommendation)
                    print(f"  Created recommendation: {rec_data['ticker']} - {rec_data['recommendation_type'].value}")
                else:
                    print(f"  Recommendation already exists: {rec_data['ticker']}")
            
            await session.commit()
            print("✅ Recommendations seeded successfully!")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error seeding recommendations: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_recommendations())

