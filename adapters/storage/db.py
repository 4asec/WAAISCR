from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from adapters.storage.base_model import Base
from core.config import settings
from core.logger import get_logger

logger = get_logger("storage")

engine = create_async_engine(
    settings.storage.database_url,
    echo=False,
    future=True
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully.")

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency helper for acquiring async db session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
