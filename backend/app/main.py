from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db, create_tables
from app.config import settings
from app.api import players, sources, dashboard, sleeper, team_dashboard, projections, player_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    yield
    # Shutdown (add any cleanup here if needed)

# Create FastAPI application
app = FastAPI(
    title="Fantasy Football Dashboard API",
    description="Comprehensive fantasy football data aggregation and analysis",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(players.router, prefix="/api/v1/players", tags=["players"])
app.include_router(sources.router, prefix="/api/v1/sources", tags=["sources"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(sleeper.router, prefix="/api/v1/sleeper", tags=["sleeper"])
app.include_router(team_dashboard.router, prefix="/api/v1/team", tags=["team-dashboard"])
app.include_router(projections.router, prefix="/api/v1/projections", tags=["projections"])
app.include_router(player_data.router, prefix="/api/v1/player-data", tags=["player-data"])

@app.get("/")
async def root():
    return {
        "message": "Fantasy Football Dashboard API", 
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "players": "/api/v1/players",
            "sources": "/api/v1/sources",
            "dashboard": "/api/v1/dashboard",
            "sleeper": "/api/v1/sleeper",
            "player-data": "/api/v1/player-data"
        }
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Simple database connectivity check
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}