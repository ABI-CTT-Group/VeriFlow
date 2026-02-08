import uvicorn
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import publications, catalogue, workflows, executions, veriflow

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("veriflow_backend")

app = FastAPI(title="VeriFlow Orchestrator")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(publications.router, prefix="/api/v1")
app.include_router(catalogue.router, prefix="/api/v1")
app.include_router(workflows.router, prefix="/api/v1")
app.include_router(executions.router, prefix="/api/v1")
app.include_router(veriflow.router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "VeriFlow Orchestrator is operational."}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)