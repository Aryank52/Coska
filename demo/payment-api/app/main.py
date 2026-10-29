"""Payment API - Demo application for COSKA."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import structlog
import asyncio
import random

from app.config import settings
from app.database import get_db, init_db, Payment, PaymentStatus
from app.database import AsyncSessionLocal

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("payment_api_started", pool_size=settings.db_pool_size)
    yield
    logger.info("payment_api_shutdown")


app = FastAPI(
    title="Payment API",
    description="Demo payment service for COSKA incident investigation",
    version="1.8.2",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = "USD"
    customer_id: str
    description: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    amount: float
    currency: str
    customer_id: str
    status: str
    description: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]


class HealthResponse(BaseModel):
    status: str
    service: str = "payment-api"
    version: str = "1.8.2"
    database: str
    pool_size: int


# Database dependency
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


# Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error("health_check_db_failed", error=str(e))
        db_status = "disconnected"
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        database=db_status,
        pool_size=settings.db_pool_size
    )


@app.post("/payments", response_model=PaymentResponse, status_code=201)
async def create_payment(payment: PaymentCreate, session=Depends(get_session)):
    """Create a new payment."""
    # Simulate database connection acquisition delay
    await asyncio.sleep(0.01)
    
    # Simulate pool exhaustion under load
    if random.random() < 0.3:  # 30% chance of timeout
        await asyncio.sleep(settings.db_pool_timeout + 0.1)
        logger.error("payment_db_timeout", customer_id=payment.customer_id)
        raise HTTPException(status_code=500, detail="Database connection timeout")
    
    db_payment = Payment(
        amount=payment.amount,
        currency=payment.currency,
        customer_id=payment.customer_id,
        description=payment.description,
        status=PaymentStatus.COMPLETED
    )
    session.add(db_payment)
    await session.commit()
    await session.refresh(db_payment)
    
    logger.info("payment_created", payment_id=db_payment.id, customer_id=payment.customer_id)
    
    return PaymentResponse(
        id=str(db_payment.id),
        amount=db_payment.amount,
        currency=db_payment.currency,
        customer_id=db_payment.customer_id,
        status=db_payment.status.value,
        description=db_payment.description,
        created_at=db_payment.created_at,
        processed_at=db_payment.processed_at
    )


@app.get("/payments", response_model=List[PaymentResponse])
async def list_payments(limit: int = 100, session=Depends(get_session)):
    """List recent payments."""
    from sqlalchemy import select, desc
    result = await session.execute(
        select(Payment).order_by(desc(Payment.created_at)).limit(limit)
    )
    payments = result.scalars().all()
    
    return [
        PaymentResponse(
            id=str(p.id), amount=p.amount, currency=p.currency,
            customer_id=p.customer_id, status=p.status.value,
            description=p.description, created_at=p.created_at,
            processed_at=p.processed_at
        )
        for p in payments
    ]


@app.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str, session=Depends(get_session)):
    """Get payment by ID."""
    from sqlalchemy import select
    result = await session.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return PaymentResponse(
        id=str(payment.id), amount=payment.amount, currency=payment.currency,
        customer_id=payment.customer_id, status=payment.status.value,
        description=payment.description, created_at=payment.created_at,
        processed_at=payment.processed_at
    )


@app.post("/load-test")
async def load_test(requests: int = 100, concurrency: int = 20):
    """Generate load for testing."""
    import httpx
    
    async def make_request(client, i):
        try:
            resp = await client.post(
                "http://localhost:8001/payments",
                json={
                    "amount": random.uniform(10, 1000),
                    "currency": "USD",
                    "customer_id": f"cust_{random.randint(1, 1000)}",
                    "description": f"Load test payment {i}"
                },
                timeout=5.0
            )
            return resp.status_code
        except Exception as e:
            return 500
    
    async with httpx.AsyncClient() as client:
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_request(i):
            async with semaphore:
                return await make_request(client, i)
        
        tasks = [bounded_request(i) for i in range(requests)]
        results = await asyncio.gather(*tasks)
    
    status_counts = {}
    for status in results:
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "total_requests": requests,
        "concurrency": concurrency,
        "results": status_counts,
        "error_rate": status_counts.get(500, 0) / requests if requests > 0 else 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)