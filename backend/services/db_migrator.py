# backend/services/db_migrator.py

import sqlite3
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """
    Handles database schema migrations for the optimized event store.
    
    Phase 3 of database optimization - Schema improvements.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize the migrator with database connection.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.migrations_dir = Path(__file__).parent.parent / "migrations"
        
        # Ensure migrations table exists
        self._create_migrations_table()
        
        logger.info(f"DatabaseMigrator initialized with db: {db_path}")
    
    def _create_migrations_table(self) -> None:
        """Create migrations tracking table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL,
                    description TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()
    
    def get_current_version(self) -> int:
        """
        Get the current schema version.
        
        Returns:
            Current version number, 0 if no migrations applied
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT MAX(version) FROM schema_migrations"
            )
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            return 0
        finally:
            conn.close()
    
    def get_pending_migrations(self) -> List[Path]:
        """
        Get list of migration files that haven't been applied yet.
        
        Returns:
            List of migration file paths to apply
        """
        current_version = self.get_current_version()
        pending = []
        
        if not self.migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {self.migrations_dir}")
            return pending
        
        # Find all SQL migration files
        for migration_file in sorted(self.migrations_dir.glob("*.sql")):
            # Extract version from filename (e.g., "002_optimized_schema.sql" -> 2)
            try:
                version = int(migration_file.stem.split("_")[0])
                if version > current_version:
                    pending.append(migration_file)
            except (ValueError, IndexError):
                logger.warning(f"Skipping invalid migration filename: {migration_file}")
        
        return pending
    
    def apply_migration(self, migration_file: Path) -> None:
        """
        Apply a single migration file.
        
        Args:
            migration_file: Path to the migration SQL file
        """
        logger.info(f"Applying migration: {migration_file.name}")
        
        # Read migration content
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Apply migration in a transaction
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript(migration_sql)
            conn.commit()
            logger.info(f"Successfully applied migration: {migration_file.name}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to apply migration {migration_file.name}: {e}")
            raise
        finally:
            conn.close()
    
    def run_migrations(self) -> int:
        """
        Run all pending migrations.
        
        Returns:
            Number of migrations applied
        """
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations")
            return 0
        
        logger.info(f"Found {len(pending)} pending migrations")
        
        applied_count = 0
        for migration_file in pending:
            try:
                self.apply_migration(migration_file)
                applied_count += 1
            except Exception as e:
                logger.error(f"Migration failed, stopping: {e}")
                break
        
        logger.info(f"Applied {applied_count} migrations")
        return applied_count
    
    def rollback_to_version(self, target_version: int) -> None:
        """
        Rollback to a specific version.
        
        Note: This requires down migrations which we haven't implemented yet.
        For now, this is a placeholder.
        
        Args:
            target_version: Version to rollback to
        """
        current = self.get_current_version()
        
        if target_version >= current:
            logger.warning(f"Target version {target_version} >= current {current}, nothing to rollback")
            return
        
        logger.warning("Rollback not implemented - would need down migrations")
        # TODO: Implement if needed
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """
        Get history of applied migrations.
        
        Returns:
            List of migration records
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT version, applied_at, description
                FROM schema_migrations
                ORDER BY version DESC
            """)
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'version': row[0],
                    'applied_at': row[1],
                    'description': row[2]
                })
            
            return history
        finally:
            conn.close()
    
    def verify_schema_integrity(self) -> Dict[str, Any]:
        """
        Verify that the current schema matches expectations.
        
        Returns:
            Dict with verification results
        """
        conn = sqlite3.connect(self.db_path)
        try:
            # Check for expected tables
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
            # Expected tables for each version
            expected_v1 = ['game_events']
            expected_v2 = [
                'game_events_v2', 
                'game_summaries', 
                'round_snapshots',
                'turn_details'
            ]
            
            current_version = self.get_current_version()
            
            result = {
                'current_version': current_version,
                'tables': tables,
                'valid': True,
                'errors': []
            }
            
            # Check based on version
            if current_version >= 2:
                for table in expected_v2:
                    if table not in tables:
                        result['valid'] = False
                        result['errors'].append(f"Missing table: {table}")
            
            return result
            
        finally:
            conn.close()


# Singleton instance
_migrator = None


def get_migrator(db_path: Optional[str] = None) -> DatabaseMigrator:
    """
    Get the singleton migrator instance.
    
    Args:
        db_path: Database path (required on first call)
        
    Returns:
        DatabaseMigrator instance
    """
    global _migrator
    
    if _migrator is None:
        if db_path is None:
            # Use same path as EventStore
            from pathlib import Path
            current_dir = Path(__file__).resolve()
            project_root = current_dir.parent.parent.parent
            db_path = str(project_root / "game_events.db")
        
        _migrator = DatabaseMigrator(db_path)
    
    return _migrator