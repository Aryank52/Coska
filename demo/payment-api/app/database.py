"""Database configuration for Payment API."""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, DateTime, Enum as SQLEnum, func
from datetime import datetime
import enum
from app.config import settings

# Database URL - use SQLite for demo
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./payments.db")

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=settings.db_pool_size)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Payment(Base):
    __tablename__ = "payments"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    customer_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Get database session."""
    async with AsyncSessionLocal() as session:
        yield session