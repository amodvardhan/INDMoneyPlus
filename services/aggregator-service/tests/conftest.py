"""Pytest configuration and fixtures"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import get_db
from app.models.aggregator import Base, BrokerAccount
from pathlib import Path

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="function")
async def db_session():
    """Create a test database session"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession):
    """Create a test client"""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_account(db_session: AsyncSession):
    """Create a test broker account"""
    account = BrokerAccount(
        user_id=1,
        broker_name="Zerodha",
        external_account_id="ZR123456",
        metadata={"account_type": "equity"}
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    return account


@pytest.fixture
def sample_csv_content():
    """Sample CSV content for testing"""
    return """Ticker,ISIN,Exchange,Quantity,Avg Price,Current Value
RELIANCE,INE002A01018,NSE,100,2500.50,255000.00
TCS,INE467B01029,NSE,50,3500.75,175037.50"""


@pytest.fixture
def sample_csv_file():
    """Sample CSV file path"""
    return Path(__file__).parent / "fixtures" / "sample_holdings.csv"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

