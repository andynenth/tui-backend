"""
Simple maintenance scheduler for log cleanup and archival.
Implements local-only strategy with automatic rotation.
"""

import os
import gzip
import shutil
import sqlite3
import glob
from datetime import datetime, timedelta
from typing import Optional
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


class SimpleMaintenanceScheduler:
    """Handles automated log maintenance with local archival."""

    def __init__(self, event_store):
        self.event_store = event_store
        self.scheduler = AsyncIOScheduler()
        self.archives_dir = "archives"
        self.db_path = "game_events.db"
        self._last_cleanup_time: Optional[datetime] = None

        # Ensure archives directory exists
        os.makedirs(self.archives_dir, exist_ok=True)

    def start(self):
        """Start the maintenance scheduler."""
        # Get cleanup hour from env or default to 3 AM
        cleanup_hour = int(os.getenv("LOG_CLEANUP_HOUR", "3"))

        # Daily cleanup
        self.scheduler.add_job(
            self.daily_cleanup,
            "cron",
            hour=cleanup_hour,
            minute=0,
            id="daily_cleanup",
            name="Daily log cleanup and archival",
        )

        # Also run cleanup on startup if enabled
        if os.getenv("LOG_CLEANUP_ON_STARTUP", "false").lower() == "true":
            self.scheduler.add_job(
                self.daily_cleanup,
                "date",
                run_date=datetime.now() + timedelta(seconds=30),
                id="startup_cleanup",
                name="Startup log cleanup",
            )

        self.scheduler.start()
        logger.info(
            f"Maintenance scheduler started. Daily cleanup at {cleanup_hour}:00"
        )

    def stop(self):
        """Stop the maintenance scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Maintenance scheduler stopped")

    async def daily_cleanup(self):
        """Run daily maintenance tasks."""
        start_time = datetime.now()
        logger.info("Starting daily maintenance")

        try:
            # 1. Archive days that need archiving (older than retention but not yet archived)
            retention_days = int(os.getenv("LOG_RETENTION_ACTIVE_DAYS", "3"))
            for days_ago in range(
                retention_days, retention_days + 7
            ):  # Archive up to a week of missed days
                target_date = datetime.now() - timedelta(days=days_ago)
                await self.archive_day(target_date)

            # 2. Remove events older than retention period from main DB
            deleted_count = await self.event_store.cleanup_old_events(
                hours=retention_days * 24
            )
            logger.info(
                f"Deleted {deleted_count} events older than {retention_days} days"
            )

            # 3. Vacuum database to reclaim space
            self.vacuum_database()

            # 4. Delete archives older than archive retention period
            archive_days = int(os.getenv("LOG_RETENTION_ARCHIVE_DAYS", "30"))
            deleted_archives = self.cleanup_old_archives(days=archive_days)

            # 5. Log summary
            self._last_cleanup_time = datetime.now()
            duration = (datetime.now() - start_time).total_seconds()
            self.log_maintenance_summary(deleted_count, deleted_archives, duration)

        except Exception as e:
            logger.error(f"Maintenance failed: {e}", exc_info=True)

    async def archive_day(self, date: datetime):
        """Archive a single day's events to compressed file."""
        date_str = date.strftime("%Y_%m_%d")
        archive_path = os.path.join(self.archives_dir, f"game_events_{date_str}.db.gz")

        # Skip if already archived
        if os.path.exists(archive_path):
            logger.debug(f"Archive already exists: {archive_path}")
            return

        # Check if there are events for this date
        event_count = await self.event_store.count_events_for_date(date)
        if event_count == 0:
            logger.debug(f"No events to archive for {date_str}")
            return

        logger.info(f"Archiving {event_count} events for {date_str}")

        temp_db = f"temp_{date_str}.db"
        try:
            # Create a temporary database with just that day's events
            conn_main = sqlite3.connect(self.db_path)
            conn_temp = sqlite3.connect(temp_db)

            # Create the schema in temp database
            conn_main.backup(conn_temp, pages=0)
            conn_temp.execute("DELETE FROM game_events")  # Clear all data

            # Copy only that day's events
            cursor_main = conn_main.cursor()
            cursor_temp = conn_temp.cursor()

            # Use parameterized query for safety
            query = """
            SELECT * FROM game_events 
            WHERE date(created_at) = date(?)
            """

            cursor_main.execute(query, (date.strftime("%Y-%m-%d"),))
            rows = cursor_main.fetchall()

            if rows:
                # Get column names
                columns = [description[0] for description in cursor_main.description]
                placeholders = ",".join(["?" for _ in columns])
                insert_query = f"INSERT INTO game_events ({','.join(columns)}) VALUES ({placeholders})"

                cursor_temp.executemany(insert_query, rows)
                conn_temp.commit()

            # Close connections
            conn_main.close()
            conn_temp.close()

            # Compress the temporary database
            with open(temp_db, "rb") as f_in:
                with gzip.open(archive_path, "wb", compresslevel=9) as f_out:
                    shutil.copyfileobj(f_in, f_out)

            logger.info(f"Successfully archived {len(rows)} events to {archive_path}")

        finally:
            # Always cleanup temporary file
            if os.path.exists(temp_db):
                os.remove(temp_db)

    def vacuum_database(self):
        """Vacuum the database to reclaim space."""
        try:
            original_size = os.path.getsize(self.db_path) / 1024 / 1024  # MB

            conn = sqlite3.connect(self.db_path)
            conn.execute("VACUUM")
            conn.close()

            new_size = os.path.getsize(self.db_path) / 1024 / 1024  # MB
            saved = original_size - new_size

            logger.info(
                f"Database vacuumed. Size: {original_size:.1f}MB -> {new_size:.1f}MB (saved {saved:.1f}MB)"
            )
        except Exception as e:
            logger.error(f"Failed to vacuum database: {e}")

    def cleanup_old_archives(self, days: int) -> int:
        """Delete archives older than specified days."""
        cutoff = datetime.now() - timedelta(days=days)
        deleted_count = 0

        try:
            for filename in os.listdir(self.archives_dir):
                if filename.startswith("game_events_") and filename.endswith(".db.gz"):
                    # Parse date from filename (game_events_YYYY_MM_DD.db.gz)
                    try:
                        date_str = filename[12:22]  # Extract YYYY_MM_DD
                        file_date = datetime.strptime(date_str, "%Y_%m_%d")

                        if file_date < cutoff:
                            file_path = os.path.join(self.archives_dir, filename)
                            os.remove(file_path)
                            deleted_count += 1
                            logger.info(f"Deleted old archive: {filename}")
                    except (ValueError, OSError) as e:
                        logger.warning(f"Error processing archive {filename}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error cleaning up archives: {e}")

        return deleted_count

    def log_maintenance_summary(
        self, events_deleted: int, archives_deleted: int, duration: float
    ):
        """Log a summary of maintenance activities."""
        db_size = os.path.getsize(self.db_path) / 1024 / 1024  # MB
        archive_files = glob.glob(os.path.join(self.archives_dir, "*.gz"))
        archive_size = (
            sum(os.path.getsize(f) for f in archive_files) / 1024 / 1024
        )  # MB

        summary = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(duration, 2),
            "events_deleted": events_deleted,
            "archives_deleted": archives_deleted,
            "database_size_mb": round(db_size, 2),
            "archive_count": len(archive_files),
            "archive_size_mb": round(archive_size, 2),
            "total_size_mb": round(db_size + archive_size, 2),
        }

        logger.info(f"Maintenance completed: {summary}")

    def get_status(self) -> dict:
        """Get current maintenance status."""
        db_size = (
            os.path.getsize(self.db_path) / 1024 / 1024
            if os.path.exists(self.db_path)
            else 0
        )
        archive_files = glob.glob(os.path.join(self.archives_dir, "*.gz"))
        archive_size = (
            sum(os.path.getsize(f) for f in archive_files) / 1024 / 1024
            if archive_files
            else 0
        )

        # Find oldest archive
        oldest_archive = None
        if archive_files:
            oldest_file = min(archive_files, key=os.path.getctime)
            oldest_archive = os.path.basename(oldest_file)

        # Next cleanup time
        next_cleanup = None
        if self.scheduler.running:
            job = self.scheduler.get_job("daily_cleanup")
            if job:
                next_cleanup = (
                    job.next_run_time.isoformat() if job.next_run_time else None
                )

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
            "last_cleanup": (
                self._last_cleanup_time.isoformat() if self._last_cleanup_time else None
            ),
            "next_cleanup": next_cleanup,
            "scheduler_running": self.scheduler.running,
        }
