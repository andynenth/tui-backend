#!/usr/bin/env python3
"""
State data backup script for production environments.

This script creates backups of game state data from Redis or DynamoDB,
with support for scheduled backups, retention policies, and restore capabilities.
"""

import os
import sys
import json
import gzip
import asyncio
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import boto3
import redis
from dataclasses import dataclass

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.config.production_state_config import ProductionStateConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BackupConfig:
    """Configuration for backup operations."""
    
    storage_backend: str
    backup_location: str
    retention_days: int
    compress: bool
    encrypt: bool
    include_completed_games: bool
    max_backup_size_gb: float
    
    @classmethod
    def from_env(cls) -> "BackupConfig":
        """Create config from environment variables."""
        return cls(
            storage_backend=os.getenv("STATE_STORAGE_BACKEND", "redis"),
            backup_location=os.getenv("STATE_BACKUP_LOCATION", "/backups/state"),
            retention_days=int(os.getenv("STATE_BACKUP_RETENTION_DAYS", "30")),
            compress=os.getenv("STATE_BACKUP_COMPRESS", "true").lower() == "true",
            encrypt=os.getenv("STATE_BACKUP_ENCRYPT", "false").lower() == "true",
            include_completed_games=os.getenv("BACKUP_COMPLETED_GAMES", "false").lower() == "true",
            max_backup_size_gb=float(os.getenv("MAX_BACKUP_SIZE_GB", "50")),
        )


class StateBackupManager:
    """Manages backup and restore operations for state data."""
    
    def __init__(self, config: BackupConfig):
        """Initialize backup manager."""
        self.config = config
        self.prod_config = ProductionStateConfig()
        self._setup_storage_clients()
        
    def _setup_storage_clients(self):
        """Setup storage backend clients."""
        if self.config.storage_backend == "redis":
            self.redis_client = redis.from_url(
                self.prod_config.redis_url,
                decode_responses=True
            )
        elif self.config.storage_backend == "dynamodb":
            self.dynamodb = boto3.resource("dynamodb")
            self.s3 = boto3.client("s3")
        
    async def create_backup(self, backup_name: Optional[str] = None) -> str:
        """
        Create a backup of all state data.
        
        Args:
            backup_name: Optional custom backup name
            
        Returns:
            Path to backup file
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = backup_name or f"state_backup_{timestamp}"
        
        logger.info(f"Starting backup: {backup_name}")
        
        try:
            if self.config.storage_backend == "redis":
                return await self._backup_redis(backup_name)
            elif self.config.storage_backend == "dynamodb":
                return await self._backup_dynamodb(backup_name)
            else:
                raise ValueError(f"Unsupported backend: {self.config.storage_backend}")
                
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise
            
    async def _backup_redis(self, backup_name: str) -> str:
        """Backup Redis state data."""
        backup_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "backend": "redis",
            "games": {},
            "metadata": {}
        }
        
        # Get all game keys
        game_keys = self.redis_client.keys("game:*")
        logger.info(f"Found {len(game_keys)} games to backup")
        
        # Backup each game
        backed_up = 0
        skipped = 0
        
        for key in game_keys:
            try:
                game_data = self.redis_client.hgetall(key)
                
                # Skip completed games if configured
                if not self.config.include_completed_games:
                    if game_data.get("phase") == "GAME_OVER":
                        skipped += 1
                        continue
                
                # Parse JSON fields
                for field in ["state", "snapshots", "transitions"]:
                    if field in game_data:
                        try:
                            game_data[field] = json.loads(game_data[field])
                        except json.JSONDecodeError:
                            pass
                
                backup_data["games"][key] = game_data
                backed_up += 1
                
            except Exception as e:
                logger.warning(f"Failed to backup {key}: {e}")
        
        logger.info(f"Backed up {backed_up} games, skipped {skipped}")
        
        # Save backup
        return await self._save_backup(backup_name, backup_data)
        
    async def _backup_dynamodb(self, backup_name: str) -> str:
        """Backup DynamoDB state data."""
        table = self.dynamodb.Table(self.prod_config.dynamodb_table)
        
        backup_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "backend": "dynamodb",
            "games": {},
            "metadata": {}
        }
        
        # Scan table for all items
        backed_up = 0
        skipped = 0
        
        try:
            response = table.scan()
            
            while True:
                for item in response.get("Items", []):
                    # Skip completed games if configured
                    if not self.config.include_completed_games:
                        if item.get("phase") == "GAME_OVER":
                            skipped += 1
                            continue
                    
                    game_id = item.get("game_id")
                    if game_id:
                        backup_data["games"][game_id] = item
                        backed_up += 1
                
                # Check for more pages
                if "LastEvaluatedKey" not in response:
                    break
                    
                response = table.scan(
                    ExclusiveStartKey=response["LastEvaluatedKey"]
                )
                
        except Exception as e:
            logger.error(f"DynamoDB scan failed: {e}")
            raise
            
        logger.info(f"Backed up {backed_up} games, skipped {skipped}")
        
        # Save backup
        return await self._save_backup(backup_name, backup_data)
        
    async def _save_backup(self, backup_name: str, data: Dict[str, Any]) -> str:
        """Save backup data to file."""
        # Create backup directory
        backup_dir = Path(self.config.backup_location)
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine file path
        file_ext = ".json.gz" if self.config.compress else ".json"
        backup_path = backup_dir / f"{backup_name}{file_ext}"
        
        # Convert to JSON
        json_data = json.dumps(data, indent=2, default=str)
        
        # Check size limit
        size_gb = len(json_data) / (1024 ** 3)
        if size_gb > self.config.max_backup_size_gb:
            raise ValueError(f"Backup too large: {size_gb:.2f}GB > {self.config.max_backup_size_gb}GB")
        
        # Save file
        if self.config.compress:
            with gzip.open(backup_path, "wt", encoding="utf-8") as f:
                f.write(json_data)
        else:
            with open(backup_path, "w") as f:
                f.write(json_data)
                
        # Encrypt if configured
        if self.config.encrypt:
            await self._encrypt_backup(backup_path)
            
        logger.info(f"Backup saved: {backup_path} ({size_gb:.2f}GB)")
        
        # Clean old backups
        await self._cleanup_old_backups()
        
        return str(backup_path)
        
    async def _encrypt_backup(self, backup_path: Path):
        """Encrypt backup file (placeholder for actual encryption)."""
        # In production, use proper encryption like AWS KMS or GPG
        logger.info(f"Encrypting backup: {backup_path}")
        # Implementation depends on your security requirements
        
    async def _cleanup_old_backups(self):
        """Remove backups older than retention period."""
        backup_dir = Path(self.config.backup_location)
        cutoff_date = datetime.utcnow() - timedelta(days=self.config.retention_days)
        
        removed = 0
        for backup_file in backup_dir.glob("state_backup_*"):
            try:
                # Extract timestamp from filename
                timestamp_str = backup_file.stem.split("_", 2)[2]
                file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                if file_date < cutoff_date:
                    backup_file.unlink()
                    removed += 1
                    
            except Exception as e:
                logger.warning(f"Failed to process {backup_file}: {e}")
                
        if removed > 0:
            logger.info(f"Cleaned up {removed} old backups")
            
    async def restore_backup(self, backup_path: str, dry_run: bool = True) -> Dict[str, Any]:
        """
        Restore state data from backup.
        
        Args:
            backup_path: Path to backup file
            dry_run: If True, validate but don't apply
            
        Returns:
            Restore statistics
        """
        logger.info(f"{'Validating' if dry_run else 'Restoring'} backup: {backup_path}")
        
        # Load backup data
        backup_data = await self._load_backup(backup_path)
        
        # Validate backup
        validation = await self._validate_backup(backup_data)
        if not validation["valid"]:
            raise ValueError(f"Invalid backup: {validation['errors']}")
            
        # Restore based on backend
        if backup_data["backend"] == "redis":
            return await self._restore_redis(backup_data, dry_run)
        elif backup_data["backend"] == "dynamodb":
            return await self._restore_dynamodb(backup_data, dry_run)
        else:
            raise ValueError(f"Unsupported backend: {backup_data['backend']}")
            
    async def _load_backup(self, backup_path: str) -> Dict[str, Any]:
        """Load backup data from file."""
        path = Path(backup_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")
            
        # Decrypt if needed
        if self.config.encrypt:
            await self._decrypt_backup(path)
            
        # Load data
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8") as f:
                return json.load(f)
        else:
            with open(path, "r") as f:
                return json.load(f)
                
    async def _decrypt_backup(self, backup_path: Path):
        """Decrypt backup file (placeholder)."""
        logger.info(f"Decrypting backup: {backup_path}")
        # Implementation depends on encryption method
        
    async def _validate_backup(self, backup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate backup data structure."""
        errors = []
        
        # Check required fields
        required = ["timestamp", "backend", "games"]
        for field in required:
            if field not in backup_data:
                errors.append(f"Missing required field: {field}")
                
        # Validate games
        if "games" in backup_data:
            for game_id, game_data in backup_data["games"].items():
                if not isinstance(game_data, dict):
                    errors.append(f"Invalid game data for {game_id}")
                    
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "game_count": len(backup_data.get("games", {}))
        }
        
    async def _restore_redis(self, backup_data: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
        """Restore Redis data from backup."""
        stats = {
            "total_games": len(backup_data["games"]),
            "restored": 0,
            "skipped": 0,
            "errors": 0
        }
        
        for key, game_data in backup_data["games"].items():
            try:
                if not dry_run:
                    # Convert complex fields to JSON
                    for field in ["state", "snapshots", "transitions"]:
                        if field in game_data and isinstance(game_data[field], dict):
                            game_data[field] = json.dumps(game_data[field])
                            
                    # Restore to Redis
                    self.redis_client.hmset(key, game_data)
                    
                stats["restored"] += 1
                
            except Exception as e:
                logger.error(f"Failed to restore {key}: {e}")
                stats["errors"] += 1
                
        return stats
        
    async def _restore_dynamodb(self, backup_data: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
        """Restore DynamoDB data from backup."""
        table = self.dynamodb.Table(self.prod_config.dynamodb_table)
        
        stats = {
            "total_games": len(backup_data["games"]),
            "restored": 0,
            "skipped": 0,
            "errors": 0
        }
        
        for game_id, item in backup_data["games"].items():
            try:
                if not dry_run:
                    table.put_item(Item=item)
                    
                stats["restored"] += 1
                
            except Exception as e:
                logger.error(f"Failed to restore {game_id}: {e}")
                stats["errors"] += 1
                
        return stats
        
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups."""
        backup_dir = Path(self.config.backup_location)
        backups = []
        
        if not backup_dir.exists():
            return backups
            
        for backup_file in sorted(backup_dir.glob("state_backup_*")):
            try:
                # Extract info from filename
                parts = backup_file.stem.split("_", 2)
                if len(parts) >= 3:
                    timestamp_str = parts[2]
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    backups.append({
                        "name": backup_file.name,
                        "path": str(backup_file),
                        "timestamp": timestamp.isoformat(),
                        "size_mb": backup_file.stat().st_size / (1024 * 1024),
                        "compressed": backup_file.suffix == ".gz",
                        "age_days": (datetime.utcnow() - timestamp).days
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to process {backup_file}: {e}")
                
        return backups


async def main():
    """Main backup script."""
    parser = argparse.ArgumentParser(description="State data backup utility")
    parser.add_argument(
        "action",
        choices=["backup", "restore", "list", "validate"],
        help="Action to perform"
    )
    parser.add_argument(
        "--name",
        help="Backup name (for backup action)"
    )
    parser.add_argument(
        "--path",
        help="Backup path (for restore/validate)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate but don't apply changes"
    )
    parser.add_argument(
        "--include-completed",
        action="store_true",
        help="Include completed games in backup"
    )
    
    args = parser.parse_args()
    
    # Create backup manager
    config = BackupConfig.from_env()
    if args.include_completed:
        config.include_completed_games = True
        
    manager = StateBackupManager(config)
    
    try:
        if args.action == "backup":
            backup_path = await manager.create_backup(args.name)
            print(f"✅ Backup created: {backup_path}")
            
        elif args.action == "restore":
            if not args.path:
                print("❌ Error: --path required for restore")
                return 1
                
            stats = await manager.restore_backup(args.path, args.dry_run)
            
            if args.dry_run:
                print(f"✅ Backup validated: {stats['total_games']} games")
            else:
                print(f"✅ Restored {stats['restored']} games")
                if stats["errors"] > 0:
                    print(f"⚠️  {stats['errors']} errors occurred")
                    
        elif args.action == "list":
            backups = await manager.list_backups()
            
            if not backups:
                print("No backups found")
            else:
                print(f"\nFound {len(backups)} backups:\n")
                print(f"{'Name':<40} {'Size':<10} {'Age':<10} {'Compressed'}")
                print("-" * 70)
                
                for backup in backups:
                    print(
                        f"{backup['name']:<40} "
                        f"{backup['size_mb']:.1f}MB{'':<5} "
                        f"{backup['age_days']}d{'':<7} "
                        f"{'Yes' if backup['compressed'] else 'No'}"
                    )
                    
        elif args.action == "validate":
            if not args.path:
                print("❌ Error: --path required for validate")
                return 1
                
            backup_data = await manager._load_backup(args.path)
            validation = await manager._validate_backup(backup_data)
            
            if validation["valid"]:
                print(f"✅ Backup is valid: {validation['game_count']} games")
            else:
                print(f"❌ Backup is invalid:")
                for error in validation["errors"]:
                    print(f"  - {error}")
                    
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Backup operation failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))