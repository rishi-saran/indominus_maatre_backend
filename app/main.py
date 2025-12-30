from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db

# --------------------
# API Routers
# --------------------
from app.api.service_categories import router as service_categories_router
from app.api.services import router as services_router
from app.api.service_packages import router as service_packages_router
from app.api.service_addons import router as service_addons_router
from app.api.service_providers import router as service_providers_router
from app.api.cart import router as cart_router
from app.api.orders import router as orders_router
from app.api.payments import router as payments_router
from app.api.auth import router as auth_router


app = FastAPI(
    title="Maathre Backend API",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
)

# --------------------
# Register API Routers
# --------------------

app.include_router(
    service_categories_router,
    prefix="/service-categories",
    tags=["Service Categories"],
)

app.include_router(
    services_router,
    prefix="/services",
    tags=["Services"],
)

app.include_router(
    service_packages_router,
    prefix="/service-packages",
    tags=["Service Packages"],
)

app.include_router(
    service_addons_router,
    prefix="/service-addons",
    tags=["Service Addons"],
)

app.include_router(
    service_providers_router,
    prefix="/service-providers",
    tags=["Service Providers"],
)

app.include_router(
    cart_router,
    prefix="/cart",
    tags=["Cart"],
)

app.include_router(
    orders_router,
    prefix="/orders",
    tags=["Orders"],
)

app.include_router(
    payments_router,
    prefix="/payments",
    tags=["Payments"],
)
app.include_router(auth_router)  #prefix="/api/auth" set in api/auth.py
# --------------------
# Health Check
# --------------------

@app.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "db": "connected",
    }