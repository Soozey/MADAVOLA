from fastapi import FastAPI

app = FastAPI(title="MADAVOLA API", version="0.1.0")

@app.get("/")
def root():
    return {
        "service": "MADAVOLA API",
        "version": "0.1.0",
        "message": "API operationnelle",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
        "ready": "/ready",
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    return {"status": "ready"}
