"""
Job Storage - Simple JSON-based job tracking
"""
import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class JobStorage:
    """Simple JSON file-based job storage"""

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            storage_path = os.getenv("JOB_STORAGE_PATH", "/tmp/lm_training_jobs.json")

        self.storage_path = Path(storage_path)
        self._ensure_storage_exists()

    def _ensure_storage_exists(self):
        """Create storage file if it doesn't exist"""
        if not self.storage_path.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_jobs([])

    def _read_jobs(self) -> List[Dict[str, Any]]:
        """Read all jobs from storage"""
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to read jobs: {e}, returning empty list")
            return []

    def _write_jobs(self, jobs: List[Dict[str, Any]]):
        """Write all jobs to storage"""
        with open(self.storage_path, 'w') as f:
            json.dump(jobs, f, indent=2)

    def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new job entry"""
        jobs = self._read_jobs()

        # Add metadata
        job_data["created_at"] = datetime.utcnow().isoformat()
        job_data["updated_at"] = datetime.utcnow().isoformat()

        jobs.append(job_data)
        self._write_jobs(jobs)

        logger.info(f"Created job {job_data['job_id']}")
        return job_data

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific job by ID"""
        jobs = self._read_jobs()
        for job in jobs:
            if job.get("job_id") == job_id:
                return job
        return None

    def update_job(self, job_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a job's data"""
        jobs = self._read_jobs()

        for i, job in enumerate(jobs):
            if job.get("job_id") == job_id:
                job.update(updates)
                job["updated_at"] = datetime.utcnow().isoformat()
                jobs[i] = job
                self._write_jobs(jobs)
                logger.info(f"Updated job {job_id}")
                return job

        logger.warning(f"Job {job_id} not found for update")
        return None

    def list_jobs(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List jobs with optional filtering"""
        jobs = self._read_jobs()

        # Filter by status
        if status and status != "all":
            jobs = [j for j in jobs if j.get("status") == status]

        # Sort by created_at descending (newest first)
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # Apply offset and limit
        if offset:
            jobs = jobs[offset:]
        if limit:
            jobs = jobs[:limit]

        return jobs

    def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        jobs = self._read_jobs()
        original_count = len(jobs)

        jobs = [j for j in jobs if j.get("job_id") != job_id]

        if len(jobs) < original_count:
            self._write_jobs(jobs)
            logger.info(f"Deleted job {job_id}")
            return True

        logger.warning(f"Job {job_id} not found for deletion")
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        jobs = self._read_jobs()

        status_counts = {}
        for job in jobs:
            status = job.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_jobs": len(jobs),
            "status_counts": status_counts,
            "storage_path": str(self.storage_path)
        }
