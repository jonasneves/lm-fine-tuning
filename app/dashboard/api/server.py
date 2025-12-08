"""
REST API Server for LM Fine-Tuning Dashboard

Provides HTTP endpoints for web dashboard and external integrations
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Import MCP server components for reuse
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../mcp-server'))
from tools.training import TrainingTools
from tools.validation import ValidationTools
from tools.monitoring import MonitoringTools
from tools.conversion import ConversionTools

from huggingface_hub import HfApi

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LM Fine-Tuning API",
    description="REST API for managing language model fine-tuning",
    version="1.0.0"
)

# Enable CORS for web dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize HF API
HF_TOKEN = os.getenv("HF_TOKEN")
hf_api = HfApi(token=HF_TOKEN) if HF_TOKEN else None

# Initialize tool handlers (reuse from MCP server)
training_tools = TrainingTools(hf_api)
validation_tools = ValidationTools(hf_api)
monitoring_tools = MonitoringTools(hf_api)
conversion_tools = ConversionTools(hf_api)

# Serve static files (web dashboard)
static_path = os.path.join(os.path.dirname(__file__), '../static')
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")


# Pydantic models
class JobCreateRequest(BaseModel):
    model: str
    dataset: str
    method: str  # sft, dpo, grpo
    hardware: str
    config: Optional[Dict] = {}


class DatasetValidateRequest(BaseModel):
    dataset: str
    method: str


class ConvertRequest(BaseModel):
    model: str
    quantization: str = "Q4_K_M"
    output_repo: Optional[str] = None


# Root endpoint - serve dashboard
@app.get("/")
async def root():
    """Serve main dashboard page"""
    index_path = os.path.join(static_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "LM Fine-Tuning API", "version": "1.0.0"}


# Health check
@app.get("/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "hf_token_configured": HF_TOKEN is not None,
        "version": "1.0.0"
    }


# ============================================================================
# Jobs API
# ============================================================================

@app.post("/api/jobs")
async def create_job(request: JobCreateRequest):
    """
    Create a new training job

    Returns job details and estimated cost
    """
    try:
        result = await training_tools.create_job({
            "model": request.model,
            "dataset": request.dataset,
            "method": request.method,
            "hardware": request.hardware,
            "config": request.config
        })
        return result
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs")
async def list_jobs(
    status: Optional[str] = Query("all", enum=["all", "running", "completed", "failed", "pending"]),
    limit: int = Query(10, ge=1, le=100)
):
    """
    List all training jobs with optional filtering

    Query Parameters:
    - status: Filter by job status (default: all)
    - limit: Maximum number of results (default: 10)
    """
    try:
        result = await monitoring_tools.list_jobs({
            "status": status,
            "limit": limit
        })
        return result
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """
    Get detailed information about a specific job

    Returns real-time status, progress, and costs
    """
    try:
        result = await monitoring_tools.get_status({"job_id": job_id})
        return result
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a running training job"""
    try:
        result = await monitoring_tools.cancel_job({"job_id": job_id})
        return result
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}/logs")
async def get_job_logs(job_id: str):
    """
    Get training logs for a job

    Returns recent log entries
    """
    # TODO: Implement log fetching from HF Jobs or GitHub Actions
    return {
        "job_id": job_id,
        "logs": [
            "[2025-12-08 12:00:00] Training started",
            "[2025-12-08 12:05:00] Epoch 1/3 - Loss: 2.45",
            "[2025-12-08 12:10:00] Epoch 1/3 - Loss: 1.89",
        ]
    }


# ============================================================================
# Datasets API
# ============================================================================

@app.post("/api/datasets/validate")
async def validate_dataset(request: DatasetValidateRequest):
    """
    Validate dataset format for training

    Checks if dataset is compatible with selected training method
    """
    try:
        result = await validation_tools.validate({
            "dataset": request.dataset,
            "method": request.method
        })
        return result
    except Exception as e:
        logger.error(f"Dataset validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/datasets")
async def list_datasets():
    """
    List available datasets

    Returns user's datasets from Hugging Face Hub
    """
    if not hf_api:
        raise HTTPException(status_code=503, detail="HF API not configured")

    try:
        # Get user's datasets from HF Hub
        # This is simplified - actual implementation would fetch real datasets
        datasets = [
            {
                "id": "open-r1/codeforces-cots",
                "name": "CodeForces CoTS",
                "size": 5000,
                "compatible_methods": ["sft"],
                "last_updated": "2025-12-07"
            },
            {
                "id": "openai/gsm8k",
                "name": "GSM8K Math",
                "size": 7500,
                "compatible_methods": ["sft", "grpo"],
                "last_updated": "2025-12-01"
            }
        ]
        return {"datasets": datasets, "count": len(datasets)}
    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Cost Tracking API
# ============================================================================

@app.post("/api/costs/estimate")
async def estimate_cost(
    model: str,
    dataset: str,
    hardware: str,
    epochs: int = 3,
    batch_size: int = 8
):
    """
    Estimate training cost before submission

    Returns estimated time and cost breakdown
    """
    try:
        result = await training_tools.estimate_cost({
            "model": model,
            "dataset": dataset,
            "hardware": hardware,
            "epochs": epochs,
            "batch_size": batch_size
        })
        return result
    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/costs")
async def get_cost_summary():
    """
    Get cost summary and budget status

    Returns total spending, budget remaining, and breakdown
    """
    # TODO: Implement actual cost tracking from database or HF API
    budget_limit = float(os.getenv("BUDGET_LIMIT_USD", 1000))

    return {
        "total_spent_usd": 47.23,
        "budget_limit_usd": budget_limit,
        "budget_remaining_usd": budget_limit - 47.23,
        "budget_used_percent": (47.23 / budget_limit) * 100,
        "current_month": {
            "spent_usd": 12.45,
            "job_count": 8,
            "avg_cost_per_job": 1.56
        },
        "last_7_days": {
            "spent_usd": 8.90,
            "job_count": 5
        }
    }


# ============================================================================
# Models API
# ============================================================================

@app.get("/api/models")
async def list_models():
    """
    List available base models for training

    Returns popular models with size and capabilities
    """
    models = [
        {
            "id": "Qwen/Qwen2.5-0.5B",
            "name": "Qwen 2.5 0.5B",
            "size": "0.5B",
            "recommended_hardware": ["t4-small", "t4-medium"],
            "strengths": ["Fast training", "Low cost", "Good for testing"]
        },
        {
            "id": "Qwen/Qwen2.5-1.5B",
            "name": "Qwen 2.5 1.5B",
            "size": "1.5B",
            "recommended_hardware": ["t4-medium", "a10g-small"],
            "strengths": ["Balanced performance", "Moderate cost"]
        },
        {
            "id": "Qwen/Qwen2.5-3B",
            "name": "Qwen 2.5 3B",
            "size": "3B",
            "recommended_hardware": ["a10g-small", "a10g-large"],
            "strengths": ["Strong performance", "Requires LoRA for efficiency"]
        },
        {
            "id": "Qwen/Qwen2.5-7B",
            "name": "Qwen 2.5 7B",
            "size": "7B",
            "recommended_hardware": ["a10g-large", "a100-large"],
            "strengths": ["Best quality", "Requires LoRA", "Higher cost"]
        }
    ]

    return {"models": models, "count": len(models)}


@app.get("/api/models/fine-tuned")
async def list_fine_tuned_models():
    """
    List user's fine-tuned models

    Returns models trained via this interface
    """
    # TODO: Fetch from HF Hub filtering by user
    return {
        "models": [
            {
                "id": "username/qwen-codeforces-sft",
                "base_model": "Qwen/Qwen2.5-0.5B",
                "dataset": "open-r1/codeforces-cots",
                "method": "sft",
                "created_at": "2025-12-07T10:30:00Z",
                "cost_usd": 0.73,
                "download_count": 42
            }
        ],
        "count": 1
    }


# ============================================================================
# Conversion API
# ============================================================================

@app.post("/api/convert/gguf")
async def convert_to_gguf(request: ConvertRequest):
    """
    Convert model to GGUF format for local deployment

    Triggers conversion job and returns status
    """
    try:
        result = await conversion_tools.convert({
            "model": request.model,
            "quantization": request.quantization,
            "output_repo": request.output_repo
        })
        return result
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# System API
# ============================================================================

@app.get("/api/system/stats")
async def get_system_stats():
    """
    Get system statistics and status

    Returns overall usage stats and service health
    """
    return {
        "total_jobs": 47,
        "active_jobs": 3,
        "completed_jobs": 42,
        "failed_jobs": 2,
        "total_cost_usd": 47.23,
        "services": {
            "mcp_server": "running",
            "api_server": "running",
            "hf_jobs": "available"
        },
        "uptime_hours": 120.5
    }


# Main entry point
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting REST API Server on {host}:{port}")
    logger.info(f"HF Token configured: {HF_TOKEN is not None}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
