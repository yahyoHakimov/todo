from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import models
from app.database import engine
from app.routers import auth, tasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="To-Do List API",
    description="Task management API with user authentication",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da specific domain bering
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(tasks.router)

# Root endpoint
@app.get("/")
def root():
    return FileResponse('frontend/index.html')


if os.path.exists('frontend'):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}