"""
Maintenance endpoints for log management and system health.
"""

import os
import glob
from typing import Dict, Any
from fastapi import APIRouter, HTTPException

# Remove unused import - event store is handled by scheduler
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/maintenance",
    tags=["maintenance"],
    responses={404: {"description": "Not found"}},
)

# Store reference to maintenance scheduler (will be set by main app)
maintenance_scheduler = None


def set_maintenance_scheduler(scheduler):
    """Set the maintenance scheduler instance."""
    global maintenance_scheduler
    maintenance_scheduler = scheduler


@router.get("/status")
async def maintenance_status() -> Dict[str, Any]:
    """Get current maintenance status including database and archive information."""
    try:
        if maintenance_scheduler:
            # Get status from scheduler
            return maintenance_scheduler.get_status()
        else:
            # Fallback if scheduler not available
            db_path = "game_events.db"
            archives_dir = "archives"

            db_size = (
                os.path.getsize(db_path) / 1024 / 1024 if os.path.exists(db_path) else 0
            )
            archive_files = glob.glob(os.path.join(archives_dir, "*.gz"))
            archive_size = (
                sum(os.path.getsize(f) for f in archive_files) / 1024 / 1024
                if archive_files
                else 0
            )

            oldest_archive = None
            if archive_files:
                oldest_file = min(archive_files, key=os.path.getctime)
                oldest_archive = os.path.basename(oldest_file)

            return {
                "database": {
                    "size_mb": round(db_size, 2),
                    "days_retained": int(os.getenv("LOG_RETENTION_ACTIVE_DAYS", "3")),
                },
                "archives": {
                    "count": len(archive_files),
                    "size_mb": round(archive_size, 2),
                    "oldest": oldest_archive,
                    "days_retained": int(os.getenv("LOG_RETENTION_ARCHIVE_DAYS", "30")),
                },
                "total_size_mb": round(db_size + archive_size, 2),
                "last_cleanup": None,
                "next_cleanup": "Daily at 3:00 AM (scheduler not active)",
                "scheduler_running": False,
            }
    except Exception as e:
        logger.error(f"Error getting maintenance status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-cleanup")
async def trigger_cleanup() -> Dict[str, str]:
    """Manually trigger a cleanup cycle (for testing or emergency use)."""
    try:
        if not maintenance_scheduler:
            raise HTTPException(
                status_code=503, detail="Maintenance scheduler not available"
            )

        # Check if enabled
        if os.getenv("LOG_CLEANUP_ENABLED", "true").lower() != "true":
            raise HTTPException(status_code=403, detail="Log cleanup is disabled")

        # Trigger cleanup asynchronously
        await maintenance_scheduler.daily_cleanup()

        return {"status": "success", "message": "Cleanup triggered successfully"}
    except Exception as e:
        logger.error(f"Error triggering cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_maintenance_config() -> Dict[str, Any]:
    """Get current maintenance configuration."""
    return {
        "retention": {
            "active_days": int(os.getenv("LOG_RETENTION_ACTIVE_DAYS", "3")),
            "archive_days": int(os.getenv("LOG_RETENTION_ARCHIVE_DAYS", "30")),
        },
        "cleanup": {
            "enabled": os.getenv("LOG_CLEANUP_ENABLED", "true").lower() == "true",
            "hour": int(os.getenv("LOG_CLEANUP_HOUR", "3")),
            "on_startup": os.getenv("LOG_CLEANUP_ON_STARTUP", "false").lower()
            == "true",
        },
        "storage": {
            "database_path": "game_events.db",
            "archives_directory": "archives",
        },
    }
