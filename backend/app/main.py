from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .config import settings
from .routers import auth, user, analytics
from .jobs import IngestionJob
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Background scheduler
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting MoodLens API")
    
    # Start background ingestion job
    scheduler.add_job(
        IngestionJob.ingest_recently_played,
        trigger=IntervalTrigger(minutes=settings.ingestion_interval_minutes),
        id='ingest_recently_played',
        name='Ingest Spotify recently played',
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"Background ingestion job started (every {settings.ingestion_interval_minutes} minutes)")
    
    yield
    
    # Shutdown
    scheduler.shutdown()
    logger.info("MoodLens API shutdown")


app = FastAPI(
    title="MoodLens API",
    description="Spotify analytics through an emotional lens",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your iOS app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(analytics.router)


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "name": "MoodLens API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "scheduler": "running" if scheduler.running else "stopped"
    }
