"""
Training Tools - Job creation and cost estimation
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from huggingface_hub import HfApi
import httpx
from .storage import JobStorage

logger = logging.getLogger(__name__)


class TrainingTools:
    """Tools for creating and managing training jobs"""

    def __init__(self, hf_api: Optional[HfApi] = None):
        self.hf_api = hf_api
        self.github_token = os.getenv("GH_TOKEN")
        self.storage = JobStorage()

        # Hardware pricing (USD per hour)
        self.hardware_costs = {
            "t4-small": 0.75,
            "t4-medium": 1.00,
            "a10g-small": 1.50,
            "a10g-large": 2.50,
            "a100-large": 5.00
        }

    async def create_job(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new fine-tuning job

        Two approaches:
        1. Direct HF Jobs API (if available)
        2. Trigger GitHub Actions workflow
        """
        model = params.get("model")
        dataset = params.get("dataset")
        method = params.get("method")
        hardware = params.get("hardware")
        config = params.get("config", {})

        logger.info(f"Creating training job: {model} on {dataset} using {method}")

        # Validate parameters
        if not all([model, dataset, method, hardware]):
            raise ValueError("Missing required parameters: model, dataset, method, hardware")

        # Estimate cost first
        cost_estimate = await self.estimate_cost({
            "model": model,
            "dataset": dataset,
            "hardware": hardware,
            "epochs": config.get("epochs", 3),
            "batch_size": config.get("batch_size", 8)
        })

        # Check budget if configured
        budget_limit = float(os.getenv("BUDGET_LIMIT_USD", 1000))
        if cost_estimate["estimated_cost_usd"] > budget_limit:
            return {
                "status": "rejected",
                "reason": "Estimated cost exceeds budget limit",
                "estimated_cost": cost_estimate["estimated_cost_usd"],
                "budget_limit": budget_limit
            }

        # Approach 1: Try HF Jobs API (if available)
        if self.hf_api and hasattr(self.hf_api, 'create_training_job'):
            try:
                job = await self._submit_to_hf_jobs(model, dataset, method, hardware, config)
                return {
                    "status": "submitted",
                    "job_id": job.get("job_id"),
                    "method": "hf_jobs",
                    "estimated_cost": cost_estimate["estimated_cost_usd"],
                    "estimated_time_minutes": cost_estimate["estimated_time_minutes"],
                    "hardware": hardware,
                    "monitor_url": f"https://huggingface.co/jobs/{job.get('job_id')}",
                    "message": f"Training job submitted successfully. Est. cost: ${cost_estimate['estimated_cost_usd']:.2f}"
                }
            except Exception as e:
                logger.warning(f"HF Jobs API failed: {e}, falling back to GitHub Actions")

        # Approach 2: Trigger GitHub Actions workflow
        if self.github_token:
            workflow_run = await self._trigger_github_workflow(
                model, dataset, method, hardware, config
            )

            job_id = f"gh-{workflow_run['id']}"

            # Save job to storage
            job_data = {
                "job_id": job_id,
                "status": "pending",
                "model": model,
                "dataset": dataset,
                "method": method,
                "hardware": hardware,
                "config": config,
                "estimated_cost_usd": cost_estimate["estimated_cost_usd"],
                "estimated_time_minutes": cost_estimate["estimated_time_minutes"],
                "workflow_url": workflow_run["html_url"],
                "backend": "github_actions"
            }
            self.storage.create_job(job_data)

            return {
                "status": "submitted",
                "job_id": job_id,
                "method": "github_actions",
                "estimated_cost": cost_estimate["estimated_cost_usd"],
                "estimated_time_minutes": cost_estimate["estimated_time_minutes"],
                "hardware": hardware,
                "workflow_url": workflow_run["html_url"],
                "message": f"Training workflow triggered. Est. cost: ${cost_estimate['estimated_cost_usd']:.2f}"
            }

        raise RuntimeError("No training backend available (HF Jobs API or GitHub Actions)")

    async def _submit_to_hf_jobs(
        self,
        model: str,
        dataset: str,
        method: str,
        hardware: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit job directly to Hugging Face Jobs API

        Note: This is placeholder - actual HF Jobs API integration depends on
        their SDK and API availability
        """
        # Prepare training configuration
        training_config = {
            "model_name_or_path": model,
            "dataset_name": dataset,
            "training_type": method,
            "hardware": hardware,
            "hyperparameters": {
                "num_train_epochs": config.get("epochs", 3),
                "per_device_train_batch_size": config.get("batch_size", 8),
                "learning_rate": config.get("learning_rate", "2e-5"),
                "warmup_ratio": config.get("warmup_ratio", 0.1),
                "logging_steps": config.get("logging_steps", 10),
                "save_steps": config.get("save_steps", 500),
            }
        }

        # TODO: Replace with actual HF Jobs API call when available
        # For now, this is a placeholder structure
        logger.info(f"Would submit to HF Jobs: {training_config}")

        return {
            "job_id": f"hf-job-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "status": "pending",
            "config": training_config
        }

    async def _trigger_github_workflow(
        self,
        model: str,
        dataset: str,
        method: str,
        hardware: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Trigger GitHub Actions workflow for training

        Uses repository_dispatch or workflow_dispatch
        """
        repo_owner = os.getenv("GITHUB_REPOSITORY_OWNER", "jonasneves")
        repo_name = os.getenv("GITHUB_REPOSITORY_NAME", "lm-fine-tuning")

        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/train-model.yml/dispatches"

        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        payload = {
            "ref": "main",
            "inputs": {
                "model_name": model,
                "dataset": dataset,
                "training_method": method,
                "hardware": hardware,
                "config_json": str(config)
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

        # Get the workflow run ID
        runs_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs"
        async with httpx.AsyncClient() as client:
            response = await client.get(runs_url, headers=headers)
            runs = response.json()

        latest_run = runs["workflow_runs"][0] if runs["workflow_runs"] else {}

        return {
            "id": latest_run.get("id"),
            "html_url": latest_run.get("html_url"),
            "status": latest_run.get("status")
        }

    async def estimate_cost(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate training cost and time

        Factors:
        - Model size (parameter count)
        - Dataset size (number of examples)
        - Hardware selection
        - Epochs and batch size
        """
        model = params.get("model", "")
        dataset = params.get("dataset", "")
        hardware = params.get("hardware", "t4-small")
        epochs = params.get("epochs", 3)
        batch_size = params.get("batch_size", 8)

        # Get hardware cost per hour
        hourly_cost = self.hardware_costs.get(hardware, 1.0)

        # Estimate training time based on model size and dataset
        # These are rough estimates - actual times vary significantly
        model_size = self._estimate_model_size(model)
        dataset_size = await self._estimate_dataset_size(dataset)

        # Time estimation formula (simplified)
        # base_time = (dataset_size * epochs) / (batch_size * steps_per_second)
        steps_per_second = {
            "t4-small": 2.0,
            "t4-medium": 2.5,
            "a10g-small": 3.0,
            "a10g-large": 4.0,
            "a100-large": 6.0
        }.get(hardware, 2.0)

        # Adjust for model size
        if "7B" in model or "7b" in model:
            steps_per_second *= 0.3
        elif "3B" in model or "3b" in model:
            steps_per_second *= 0.5
        elif "1.5B" in model or "1.5b" in model:
            steps_per_second *= 0.7

        total_steps = (dataset_size * epochs) / batch_size
        estimated_seconds = total_steps / steps_per_second
        estimated_minutes = estimated_seconds / 60
        estimated_hours = estimated_minutes / 60

        # Calculate cost
        estimated_cost = hourly_cost * estimated_hours

        return {
            "estimated_time_minutes": round(estimated_minutes),
            "estimated_time_hours": round(estimated_hours, 2),
            "estimated_cost_usd": round(estimated_cost, 2),
            "hourly_rate_usd": hourly_cost,
            "hardware": hardware,
            "model_size": model_size,
            "dataset_size": dataset_size,
            "epochs": epochs,
            "batch_size": batch_size,
            "breakdown": {
                "total_steps": int(total_steps),
                "steps_per_second": round(steps_per_second, 2),
                "time_per_epoch_minutes": round(estimated_minutes / epochs)
            }
        }

    def _estimate_model_size(self, model: str) -> str:
        """Estimate model size from name"""
        model_lower = model.lower()

        if "0.5b" in model_lower or "500m" in model_lower:
            return "0.5B"
        elif "1.5b" in model_lower or "1.7b" in model_lower:
            return "1.5B"
        elif "3b" in model_lower:
            return "3B"
        elif "7b" in model_lower:
            return "7B"
        elif "13b" in model_lower:
            return "13B"
        else:
            return "unknown"

    async def _estimate_dataset_size(self, dataset: str) -> int:
        """
        Estimate dataset size (number of examples)

        Try to fetch from HF Hub, otherwise use default estimates
        """
        if not self.hf_api:
            # Default estimates for common datasets
            common_datasets = {
                "open-r1/codeforces-cots": 5000,
                "openai/gsm8k": 7500,
                "Anthropic/hh-rlhf": 160000
            }
            return common_datasets.get(dataset, 10000)

        try:
            # Try to get actual dataset size from HF Hub
            dataset_info = self.hf_api.dataset_info(dataset)
            # This is simplified - actual implementation would parse dataset structure
            return 10000  # Placeholder
        except Exception as e:
            logger.warning(f"Could not fetch dataset size for {dataset}: {e}")
            return 10000  # Default estimate
