
from fastapi import FastAPI

app = FastAPI(
    title="BloodLink API",
    description="BloodLink - Smart Blood Donor Connection Platform",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Welcome to BloodLink API",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "message": "BloodLink FastAPI backend is running",
        "status": "healthy"
    }
