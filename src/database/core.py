from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, BigInteger, Boolean, String
from typing import AsyncGenerator

# 1. Models
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    language_code: Mapped[str] = mapped_column(String(10), default="en")

class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    channel_username: Mapped[str] = mapped_column(String(100))
    owner_telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    price_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    price_interval: Mapped[int] = mapped_column(Integer, default=5)  # minutes
    last_price_sent: Mapped[int] = mapped_column(BigInteger, default=0)  # Unix timestamp
    news_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    news_language: Mapped[str] = mapped_column(String(10), default="en")

class SavedForecast(Base):
    __tablename__ = "saved_forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[str] = mapped_column(String(20), index=True)  # YYYY-MM-DD
    time_slot: Mapped[str] = mapped_column(String(10))         # "morning" or "evening"
    content_en: Mapped[str] = mapped_column(String)
    content_ru: Mapped[str] = mapped_column(String)
    content_uz: Mapped[str] = mapped_column(String)
    created_at: Mapped[int] = mapped_column(BigInteger)        # Unix timestamp

# 2. Connection Logic
DATABASE_URL = "sqlite+aiosqlite:///./bot.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
