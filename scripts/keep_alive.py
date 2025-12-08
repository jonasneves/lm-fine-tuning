#!/usr/bin/env python3
"""
Keep Alive Script - Auto-restart handler for GitHub Actions

Similar to serverless-llm approach:
- Monitors running time
- Gracefully shuts down before GitHub's 6-hour timeout
- Triggers new workflow run for seamless handoff
"""
import os
import sys
import time
import signal
import logging
import argparse
from datetime import datetime, timedelta
import httpx

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KeepAliveManager:
    """Manages service lifecycle and auto-restart"""

    def __init__(
        self,
        duration_hours: float = 5.5,
        auto_restart: bool = True,
        pids: str = None
    ):
        self.duration_hours = duration_hours
        self.auto_restart = auto_restart
        self.pids = [int(p) for p in pids.split(",")] if pids else []
        self.start_time = datetime.utcnow()
        self.end_time = self.start_time + timedelta(hours=duration_hours)

        self.github_token = os.getenv("GH_TOKEN")
        self.repo_owner = os.getenv("GITHUB_REPOSITORY_OWNER", "jonasneves")
        self.repo_name = os.getenv("GITHUB_REPOSITORY_NAME", "lm-fine-tuning")
        self.workflow_name = os.getenv("GITHUB_WORKFLOW", "mcp-server.yml")

        logger.info(f"Keep-Alive Manager started")
        logger.info(f"Duration: {duration_hours} hours")
        logger.info(f"Auto-restart: {auto_restart}")
        logger.info(f"End time: {self.end_time}")
        logger.info(f"Monitoring PIDs: {self.pids}")

    def run(self):
        """Main keep-alive loop"""
        try:
            while True:
                now = datetime.utcnow()
                remaining = (self.end_time - now).total_seconds()

                if remaining <= 0:
                    logger.info("Duration limit reached - initiating shutdown")
                    self.graceful_shutdown()
                    break

                # Log status every minute
                if int(remaining) % 60 == 0:
                    remaining_minutes = int(remaining / 60)
                    logger.info(f"Remaining time: {remaining_minutes} minutes")

                # Check if processes are still running
                if not self.check_processes():
                    logger.error("Monitored processes died - exiting")
                    sys.exit(1)

                time.sleep(10)  # Check every 10 seconds

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            self.graceful_shutdown()
        except Exception as e:
            logger.error(f"Error in keep-alive loop: {e}")
            self.graceful_shutdown()
            sys.exit(1)

    def check_processes(self) -> bool:
        """Check if monitored processes are still running"""
        if not self.pids:
            return True  # No processes to monitor

        for pid in self.pids:
            try:
                # Send signal 0 to check if process exists
                os.kill(pid, 0)
            except OSError:
                logger.error(f"Process {pid} is not running")
                return False

        return True

    def graceful_shutdown(self):
        """Gracefully shut down services and optionally restart"""
        logger.info("=== Starting graceful shutdown ===")

        # Trigger new workflow if auto-restart is enabled
        if self.auto_restart:
            logger.info("Auto-restart enabled - triggering new workflow")
            if self.trigger_restart():
                logger.info("New workflow triggered successfully")
                # Wait a bit to ensure new instance starts
                time.sleep(30)
            else:
                logger.error("Failed to trigger new workflow")

        # Stop monitored processes
        for pid in self.pids:
            try:
                logger.info(f"Sending SIGTERM to process {pid}")
                os.kill(pid, signal.SIGTERM)
                time.sleep(2)

                # Check if process stopped
                try:
                    os.kill(pid, 0)
                    # Still running, force kill
                    logger.warning(f"Process {pid} didn't stop, sending SIGKILL")
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    logger.info(f"Process {pid} stopped successfully")

            except OSError as e:
                logger.warning(f"Error stopping process {pid}: {e}")

        logger.info("=== Shutdown complete ===")

    def trigger_restart(self) -> bool:
        """Trigger new workflow run via GitHub API"""
        if not self.github_token:
            logger.error("GH_TOKEN not set - cannot trigger restart")
            return False

        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/actions/workflows/{self.workflow_name}/dispatches"

        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        payload = {
            "ref": "main",
            "inputs": {
                "duration_hours": str(self.duration_hours),
                "auto_restart": "true" if self.auto_restart else "false"
            }
        }

        try:
            with httpx.Client() as client:
                response = client.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()

            logger.info("Workflow dispatch successful")
            return True

        except Exception as e:
            logger.error(f"Failed to trigger workflow: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Keep-alive manager for GitHub Actions")
    parser.add_argument(
        "--duration",
        type=float,
        default=5.5,
        help="Duration in hours before shutdown (default: 5.5)"
    )
    parser.add_argument(
        "--auto-restart",
        type=lambda x: x.lower() in ["true", "1", "yes"],
        default=True,
        help="Auto-restart by triggering new workflow (default: true)"
    )
    parser.add_argument(
        "--pids",
        type=str,
        default=None,
        help="Comma-separated list of PIDs to monitor"
    )

    args = parser.parse_args()

    manager = KeepAliveManager(
        duration_hours=args.duration,
        auto_restart=args.auto_restart,
        pids=args.pids
    )

    manager.run()


if __name__ == "__main__":
    main()
