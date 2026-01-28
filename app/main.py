from fastapi import FastAPI
from fastapi import APIRouter
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# --------------------
# API Routers
# --------------------
from app.api.auth import router as auth_router
from app.api.service_categories import router as service_categories_router
from app.api.services import router as services_router
from app.api.service_packages import router as service_packages_router
from app.api.service_addons import router as service_addons_router
from app.api.service_providers import router as service_providers_router
from app.api.cart import router as cart_router
from app.api.orders import router as orders_router
from app.api.payments import router as payments_router
from app.api.addresses import router as addresses_router
from app.api.pages import router as pages_router


# --------------------
# FastAPI App
# --------------------
app = FastAPI(
    title="Maathre Backend API",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
)


# --------------------
# CORS Middleware
# --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://indominus-maathre.vercel.app",  # Your Vercel frontend
        "http://localhost:3000",  # Local development
        "http://localhost:5173",  # Vite dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------
# Exception Handlers
# --------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Log validation errors for debugging"""
    print(f"Validation error: {exc}")
    print(f"Request path: {request.url.path}")
    print(f"Request body: {await request.body()}")
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )


# --------------------
# API Version Router
# --------------------
api_v1_router = APIRouter(prefix="/api/v1")

# --------------------
# Register Routers
# --------------------
api_v1_router.include_router(auth_router)
api_v1_router.include_router(service_categories_router)
api_v1_router.include_router(services_router)
api_v1_router.include_router(service_packages_router)
api_v1_router.include_router(service_addons_router)
api_v1_router.include_router(service_providers_router)
api_v1_router.include_router(cart_router)
api_v1_router.include_router(orders_router)
api_v1_router.include_router(payments_router)
api_v1_router.include_router(addresses_router)
api_v1_router.include_router(pages_router)


app.include_router(api_v1_router)

# --------------------
# Health Check
# --------------------
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "backend": "running",
        "database": "supabase",
    }