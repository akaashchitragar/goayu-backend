from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import connect_to_mongodb, close_mongodb_connection
from app.api.v1 import questionnaire, consultation, pdf, users, auth, ai_usage, daily_tip, stores


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for FastAPI application
    """
    # Startup
    print("🚀 Starting Ayushya Backend API...")
    connect_to_mongodb()
    yield
    # Shutdown
    print("👋 Shutting down Ayushya Backend API...")
    close_mongodb_connection()


# Initialize FastAPI app
app = FastAPI(
    title="Ayushya API",
    description="AI-Powered Ayurvedic Consultation Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Ayushya API",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected"
    }


# Include routers
app.include_router(
    questionnaire.router,
    prefix="/api/v1/questionnaire",
    tags=["Questionnaire"]
)

app.include_router(
    consultation.router,
    prefix="/api/v1/consultation",
    tags=["Consultation"]
)

app.include_router(
    pdf.router,
    prefix="/api/v1/pdf",
    tags=["PDF"]
)

app.include_router(
    users.router,
    prefix="/api/v1",
    tags=["Users"]
)

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    ai_usage.router,
    prefix="/api/v1/ai-usage",
    tags=["AI Usage"]
)

app.include_router(
    daily_tip.router,
    prefix="/api/v1",
    tags=["Daily Tip"]
)

app.include_router(
    stores.router,
    prefix="/api/v1",
    tags=["Stores"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
