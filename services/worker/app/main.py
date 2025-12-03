"""
Worker Service - Background workers for Celery/Temporal tasks
"""
from fastapi import FastAPI
import os

app = FastAPI(
    title="Worker Service",
    description="Background workers for rebalances, tax harvesting, and compute jobs",
    version="0.1.0"
)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "worker"}

# TODO: Implement Celery or Temporal workers
# Example structure:
# - tasks/rebalance.py
# - tasks/tax_harvesting.py
# - tasks/compute.py

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)

