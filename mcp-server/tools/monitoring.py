"""
Monitoring Tools - Job status and progress tracking
"""
import logging
import asyncio
import os
import httpx
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from huggingface_hub import HfApi
from .storage import JobStorage

logger = logging.getLogger(__name__)


class MonitoringTools:
    """Tools for monitoring training job status and costs"""

    def __init__(self, hf_api: Optional[HfApi] = None, github_token: Optional[str] = None):
        self.hf_api = hf_api
        self.github_token = github_token or os.getenv("GH_TOKEN")
        self.storage = JobStorage()
        self.repo_owner = os.getenv("GITHUB_REPOSITORY_OWNER", "jonasneves")
        self.repo_name = os.getenv("GITHUB_REPOSITORY_NAME", "lm-fine-tuning")
        self.job_cache = {}  # Simple in-memory cache

    async def get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get status and progress of a training job

        Returns real-time status, progress, costs, and ETAs
        """
        job_id = params.get("job_id")
        if not job_id:
            raise ValueError("Missing required parameter: job_id")

        logger.info(f"Getting status for job {job_id}")

        # Check if this is a GitHub Actions job or HF Jobs
        if job_id.startswith("gh-"):
            return await self._get_github_status(job_id)
        else:
            return await self._get_hf_status(job_id)

    async def _get_hf_status(self, job_id: str) -> Dict[str, Any]:
        """Get status from Hugging Face Jobs"""

        # TODO: Replace with actual HF Jobs API call
        # Placeholder response structure
        return {
            "job_id": job_id,
            "status": "running",  # pending, running, completed, failed
            "progress": 0.45,  # 0.0 to 1.0
            "current_step": 450,
            "total_steps": 1000,
            "current_epoch": 1,
            "total_epochs": 3,
            "loss": 1.23,
            "learning_rate": 2e-5,
            "elapsed_time_minutes": 12,
            "eta_minutes": 15,
            "cost_so_far_usd": 0.15,
            "estimated_total_cost_usd": 0.34,
            "hardware": "t4-small",
            "model": "Qwen/Qwen2.5-0.5B",
            "dataset": "open-r1/codeforces-cots",
            "method": "sft",
            "monitor_url": f"https://huggingface.co/jobs/{job_id}",
            "trackio_url": f"https://huggingface.co/spaces/user/trackio"
        }

    async def _get_github_status(self, job_id: str) -> Dict[str, Any]:
        """Get status from GitHub Actions workflow run"""

        run_id = job_id.replace("gh-", "")

        if not self.github_token:
            raise ValueError("GitHub token not configured")

        # Get workflow run details from GitHub API
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/actions/runs/{run_id}"

        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            run_data = response.json()

        # Map GitHub Actions status to our status
        gh_status = run_data.get("status")
        gh_conclusion = run_data.get("conclusion")

        if gh_status == "completed":
            if gh_conclusion == "success":
                status = "completed"
            elif gh_conclusion in ["failure", "cancelled", "timed_out"]:
                status = "failed"
            else:
                status = "failed"
        elif gh_status in ["queued", "waiting"]:
            status = "pending"
        elif gh_status == "in_progress":
            status = "running"
        else:
            status = "unknown"

        # Calculate progress (rough estimate based on elapsed time)
        created_at = datetime.fromisoformat(run_data["created_at"].replace("Z", "+00:00"))
        elapsed_minutes = (datetime.now(created_at.tzinfo) - created_at).total_seconds() / 60

        # Get job from storage for additional metadata
        job_data = self.storage.get_job(job_id) or {}

        # Update job status in storage
        self.storage.update_job(job_id, {"status": status})

        return {
            "job_id": job_id,
            "status": status,
            "gh_status": gh_status,
            "gh_conclusion": gh_conclusion,
            "workflow_url": run_data.get("html_url"),
            "elapsed_time_minutes": int(elapsed_minutes),
            "created_at": run_data.get("created_at"),
            "updated_at": run_data.get("updated_at"),
            "model": job_data.get("model"),
            "dataset": job_data.get("dataset"),
            "method": job_data.get("method"),
            "hardware": job_data.get("hardware"),
            "message": f"Training {status} via GitHub Actions"
        }

    async def list_jobs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        List training jobs with optional filtering

        Returns list of jobs with their current status
        """
        status_filter = params.get("status", "all")
        limit = params.get("limit", 10)

        logger.info(f"Listing jobs (status={status_filter}, limit={limit})")

        # Get jobs from storage
        jobs = self.storage.list_jobs(
            status=status_filter if status_filter != "all" else None,
            limit=limit
        )

        return {
            "jobs": jobs,
            "total": len(jobs),
            "status_filter": status_filter
        }

    async def cancel_job(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cancel a running training job

        Cancels GitHub Actions workflow or HF Jobs API job
        """
        job_id = params.get("job_id")
        if not job_id:
            raise ValueError("Missing required parameter: job_id")

        logger.info(f"Cancelling job {job_id}")

        # Get job from storage
        job_data = self.storage.get_job(job_id)
        if not job_data:
            raise ValueError(f"Job {job_id} not found")

        # Check if already completed or failed
        if job_data.get("status") in ["completed", "failed", "cancelled"]:
            return {
                "job_id": job_id,
                "success": False,
                "message": f"Job is already {job_data.get('status')}"
            }

        # Cancel GitHub Actions workflow
        if job_id.startswith("gh-"):
            run_id = job_id.replace("gh-", "")

            if not self.github_token:
                raise ValueError("GitHub token not configured")

            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/actions/runs/{run_id}/cancel"

            headers = {
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers)
                response.raise_for_status()

            # Update job status
            self.storage.update_job(job_id, {"status": "cancelled"})

            return {
                "job_id": job_id,
                "success": True,
                "message": "Job cancelled successfully"
            }
        else:
            # HF Jobs cancellation - TODO when HF Jobs API is available
            raise NotImplementedError("HF Jobs cancellation not yet implemented")

    async def stream_progress(self, job_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream real-time progress updates for a job

        Yields progress updates as they become available
        """
        logger.info(f"Starting progress stream for job {job_id}")

        # Simulate streaming progress updates
        # In production, this would poll HF Jobs API or websocket
        for i in range(10):
            await asyncio.sleep(2)  # Poll every 2 seconds

            progress = (i + 1) / 10
            yield {
                "job_id": job_id,
                "progress": progress,
                "current_step": (i + 1) * 100,
                "total_steps": 1000,
                "loss": 2.5 - (progress * 1.5),  # Simulated decreasing loss
                "eta_minutes": int((10 - i) * 2 / 60),
                "timestamp": datetime.utcnow().isoformat()
            }

            # Stop if complete
            if progress >= 1.0:
                break
