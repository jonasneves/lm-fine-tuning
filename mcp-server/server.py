"""
MCP Server for LM Fine-Tuning
Implements Model Context Protocol for Claude Code integration
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn
from huggingface_hub import HfApi

from tools.training import TrainingTools
from tools.validation import ValidationTools
from tools.monitoring import MonitoringTools
from tools.conversion import ConversionTools

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LM Fine-Tuning MCP Server",
    description="Model Context Protocol server for managing language model fine-tuning",
    version="1.0.0"
)

# Initialize Hugging Face API
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    logger.warning("HF_TOKEN not set - some features will be disabled")

hf_api = HfApi(token=HF_TOKEN) if HF_TOKEN else None

# Initialize tool handlers
training_tools = TrainingTools(hf_api)
validation_tools = ValidationTools(hf_api)
monitoring_tools = MonitoringTools(hf_api)
conversion_tools = ConversionTools(hf_api)


# Pydantic models for request/response
class ToolCallRequest(BaseModel):
    tool: str = Field(..., description="Tool name to invoke")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")


class ToolCallResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "hf_token_configured": HF_TOKEN is not None,
        "version": "1.0.0"
    }


# MCP tool listing endpoint
@app.get("/mcp/tools")
async def list_tools():
    """List all available MCP tools"""
    tools = [
        {
            "name": "create_training_job",
            "description": "Create a new fine-tuning job on Hugging Face",
            "parameters": {
                "model": {
                    "type": "string",
                    "description": "Base model name (e.g., 'Qwen/Qwen2.5-0.5B')",
                    "required": True
                },
                "dataset": {
                    "type": "string",
                    "description": "Dataset ID from Hugging Face Hub",
                    "required": True
                },
                "method": {
                    "type": "string",
                    "enum": ["sft", "dpo", "grpo"],
                    "description": "Training method",
                    "required": True
                },
                "hardware": {
                    "type": "string",
                    "enum": ["t4-small", "t4-medium", "a10g-small", "a10g-large", "a100-large"],
                    "description": "GPU hardware to use",
                    "required": True
                },
                "config": {
                    "type": "object",
                    "description": "Training configuration (epochs, learning_rate, etc.)",
                    "required": False
                }
            }
        },
        {
            "name": "validate_dataset",
            "description": "Validate dataset format for training compatibility",
            "parameters": {
                "dataset": {
                    "type": "string",
                    "description": "Dataset ID from Hugging Face Hub",
                    "required": True
                },
                "method": {
                    "type": "string",
                    "enum": ["sft", "dpo", "grpo"],
                    "description": "Training method to validate for",
                    "required": True
                }
            }
        },
        {
            "name": "estimate_cost",
            "description": "Estimate training cost before submission",
            "parameters": {
                "model": {
                    "type": "string",
                    "description": "Base model name",
                    "required": True
                },
                "dataset": {
                    "type": "string",
                    "description": "Dataset ID",
                    "required": True
                },
                "hardware": {
                    "type": "string",
                    "description": "GPU hardware",
                    "required": True
                },
                "epochs": {
                    "type": "integer",
                    "description": "Number of epochs",
                    "default": 3
                },
                "batch_size": {
                    "type": "integer",
                    "description": "Training batch size",
                    "default": 8
                }
            }
        },
        {
            "name": "get_job_status",
            "description": "Get status and progress of a training job",
            "parameters": {
                "job_id": {
                    "type": "string",
                    "description": "Hugging Face Jobs ID",
                    "required": True
                }
            }
        },
        {
            "name": "list_jobs",
            "description": "List all training jobs",
            "parameters": {
                "status": {
                    "type": "string",
                    "enum": ["running", "completed", "failed", "pending", "all"],
                    "default": "all",
                    "description": "Filter by job status"
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of jobs to return"
                }
            }
        },
        {
            "name": "cancel_job",
            "description": "Cancel a running training job",
            "parameters": {
                "job_id": {
                    "type": "string",
                    "description": "Job ID to cancel",
                    "required": True
                }
            }
        },
        {
            "name": "convert_to_gguf",
            "description": "Convert trained model to GGUF format",
            "parameters": {
                "model": {
                    "type": "string",
                    "description": "Model ID on Hugging Face Hub",
                    "required": True
                },
                "quantization": {
                    "type": "string",
                    "enum": ["Q4_K_M", "Q5_K_M", "Q8_0"],
                    "default": "Q4_K_M",
                    "description": "Quantization level"
                },
                "output_repo": {
                    "type": "string",
                    "description": "Output repository name",
                    "required": False
                }
            }
        }
    ]

    return {
        "tools": tools,
        "count": len(tools),
        "version": "1.0.0"
    }


# MCP tool invocation endpoint
@app.post("/mcp/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest, authorization: Optional[str] = Header(None)):
    """
    Invoke an MCP tool

    This is the main endpoint that Claude Code calls to execute tools
    """
    try:
        logger.info(f"Tool call: {request.tool} with params: {request.parameters}")

        # Route to appropriate tool handler
        if request.tool == "create_training_job":
            result = await training_tools.create_job(request.parameters)

        elif request.tool == "validate_dataset":
            result = await validation_tools.validate(request.parameters)

        elif request.tool == "estimate_cost":
            result = await training_tools.estimate_cost(request.parameters)

        elif request.tool == "get_job_status":
            result = await monitoring_tools.get_status(request.parameters)

        elif request.tool == "list_jobs":
            result = await monitoring_tools.list_jobs(request.parameters)

        elif request.tool == "cancel_job":
            result = await monitoring_tools.cancel_job(request.parameters)

        elif request.tool == "convert_to_gguf":
            result = await conversion_tools.convert(request.parameters)

        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {request.tool}")

        return ToolCallResponse(
            success=True,
            result=result,
            metadata={
                "tool": request.tool,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    except Exception as e:
        logger.error(f"Tool call failed: {str(e)}", exc_info=True)
        return ToolCallResponse(
            success=False,
            error=str(e),
            metadata={
                "tool": request.tool,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Stream job progress (for real-time updates)
@app.get("/mcp/stream/{job_id}")
async def stream_job_progress(job_id: str):
    """
    Stream real-time progress updates for a training job

    Returns Server-Sent Events (SSE) for Claude Code to display
    """
    async def event_generator():
        try:
            async for update in monitoring_tools.stream_progress(job_id):
                yield f"data: {json.dumps(update)}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


# Webhook endpoint for job completion notifications
@app.post("/webhooks/job-complete")
async def job_completion_webhook(data: Dict[str, Any]):
    """
    Receive webhook when training job completes

    Hugging Face Jobs can send webhooks on completion
    """
    logger.info(f"Job completion webhook: {data}")

    job_id = data.get("job_id")
    status = data.get("status")

    # TODO: Add notification logic (Slack, Discord, etc.)
    # TODO: Trigger GGUF conversion if configured
    # TODO: Trigger deployment to serverless-llm if configured

    return {"received": True, "job_id": job_id, "status": status}


# Main entry point
if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting MCP Server on {host}:{port}")
    logger.info(f"HF Token configured: {HF_TOKEN is not None}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
