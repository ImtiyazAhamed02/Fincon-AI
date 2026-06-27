import sys
import io
import os

# Fix Windows charmap encoding errors for CrewAI emojis
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logger import logger
from app.core.config import settings
from app.api.routes import analysis, history, portfolio

app = FastAPI(
    title="FINCON API",
    description="Multi-agent Financial AI Platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"], # Frontend dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting FINCON API in {settings.ENVIRONMENT} mode.")
    logger.info("Initializing Agent System...")
    # Setup agents here later

app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(history.router, prefix="/api/history", tags=["History"])
app.include_router(portfolio.router, prefix="/api/portfolios", tags=["Portfolio"])

@app.get("/")
async def root():
    return {"message": "Welcome to FINCON API", "status": "online"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
