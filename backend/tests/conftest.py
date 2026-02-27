"""Pytest configuration and fixtures."""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from app.database import Base, get_db
from app.main import app
from app.models import User, Subscription, Message, NotificationSetting
from app.api.auth import get_password_hash


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine):
    """Create a test database session."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session):
    """Create a test client."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def test_user(db_session) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("testpassword"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers for test user."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpassword"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
async def test_subscription(db_session: AsyncSession, test_user: User) -> Subscription:
    """Create a test subscription."""
    from app.models.subscription import SourceType

    subscription = Subscription(
        user_id=test_user.id,
        name="Test RSS Feed",
        source_type=SourceType.RSS,
        source_config={"url": "https://example.com/feed.xml"},
        enabled=True,
    )
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)
    return subscription


@pytest.fixture(scope="function")
async def test_message(db_session: AsyncSession, test_subscription: Subscription) -> Message:
    """Create a test message."""
    from app.models.message import MessageStatus

    message = Message(
        subscription_id=test_subscription.id,
        title="Test Message",
        content="This is a test message content.",
        author="Test Author",
        status=MessageStatus.NEW,
    )
    db_session.add(message)
    await db_session.commit()
    await db_session.refresh(message)
    return message


@pytest.fixture(scope="function")
async def test_notification_settings(db_session: AsyncSession, test_user: User) -> NotificationSetting:
    """Create test notification settings."""
    settings = NotificationSetting(
        user_id=test_user.id,
        telegram_enabled=True,
        telegram_chat_id="123456789",
        email_enabled=True,
        email_address="test@example.com",
    )
    db_session.add(settings)
    await db_session.commit()
    await db_session.refresh(settings)
    return settings
