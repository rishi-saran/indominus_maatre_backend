from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from app.api.service_categories import router as service_categories_router

app = FastAPI(
    title="Maathre Backend API",
    version="1.0.0",
)

# Register API routers
app.include_router(
    service_categories_router,
    prefix="/service-categories",
    tags=["Service Categories"],
)

@app.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "db": "connected",
    }