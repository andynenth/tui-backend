"""
Archive backend implementations for different storage systems.

Provides concrete implementations for filesystem, S3, and PostgreSQL.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import logging
import json
import os
from pathlib import Path
import hashlib
import aiofiles
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class FileSystemArchiveBackend:
    """
    Filesystem-based archive backend.

    Stores archived data as compressed JSON files with metadata.
    """

    def __init__(
        self,
        base_path: str = "./archives",
        use_compression: bool = True,
        partition_by_date: bool = True,
    ):
        """
        Initialize filesystem backend.

        Args:
            base_path: Base directory for archives
            use_compression: Whether to compress files
            partition_by_date: Whether to partition by date
        """
        self.base_path = Path(base_path)
        self.use_compression = use_compression
        self.partition_by_date = partition_by_date

        # Create base directory
        self.base_path.mkdir(parents=True, exist_ok=True)

        self._metrics = {
            "total_archived": 0,
            "total_retrieved": 0,
            "total_deleted": 0,
            "total_size_bytes": 0,
        }

    async def archive(self, entity_id: str, entity_type: str, data: bytes) -> str:
        """Archive entity data and return location."""
        try:
            # Generate file path
            file_path = self._generate_path(entity_id, entity_type)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Add metadata wrapper
            metadata = {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "archived_at": datetime.utcnow().isoformat(),
                "size_bytes": len(data),
                "checksum": hashlib.sha256(data).hexdigest(),
            }

            # Create archive file
            archive_data = {
                "metadata": metadata,
                "data": data.hex(),  # Store as hex string
            }

            # Write to file
            async with aiofiles.open(file_path, "wb") as f:
                content = json.dumps(archive_data).encode("utf-8")

                if self.use_compression:
                    import gzip

                    content = gzip.compress(content, compresslevel=6)

                await f.write(content)

            # Update metrics
            self._metrics["total_archived"] += 1
            self._metrics["total_size_bytes"] += len(content)

            return str(file_path.relative_to(self.base_path))

        except Exception as e:
            logger.error(f"Failed to archive {entity_id}: {e}")
            raise

    async def retrieve(self, archive_location: str) -> bytes:
        """Retrieve archived data."""
        try:
            file_path = self.base_path / archive_location

            if not file_path.exists():
                raise FileNotFoundError(f"Archive not found: {archive_location}")

            # Read file
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()

            if self.use_compression:
                import gzip

                content = gzip.decompress(content)

            # Parse archive
            archive_data = json.loads(content.decode("utf-8"))

            # Verify checksum
            data = bytes.fromhex(archive_data["data"])
            checksum = hashlib.sha256(data).hexdigest()

            if checksum != archive_data["metadata"]["checksum"]:
                raise ValueError(f"Checksum mismatch for {archive_location}")

            # Update metrics
            self._metrics["total_retrieved"] += 1

            return data

        except Exception as e:
            logger.error(f"Failed to retrieve {archive_location}: {e}")
            raise

    async def delete(self, archive_location: str) -> bool:
        """Delete archived data."""
        try:
            file_path = self.base_path / archive_location

            if file_path.exists():
                file_path.unlink()
                self._metrics["total_deleted"] += 1

                # Clean up empty directories
                try:
                    file_path.parent.rmdir()
                except OSError:
                    pass  # Directory not empty

                return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete {archive_location}: {e}")
            raise

    async def list_archives(
        self,
        entity_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[str]:
        """List archived entities."""
        archives = []

        try:
            # Search pattern based on partitioning
            if self.partition_by_date and (start_date or end_date):
                # Search specific date partitions
                search_paths = self._get_date_partitions(
                    entity_type, start_date, end_date
                )
            else:
                # Search all entity type directory
                search_paths = [self.base_path / entity_type]

            # Find all archive files
            for search_path in search_paths:
                if search_path.exists():
                    for file_path in search_path.rglob("*.json*"):
                        relative_path = file_path.relative_to(self.base_path)

                        # Check date range if specified
                        if start_date or end_date:
                            # Read metadata to check date
                            try:
                                metadata = await self._read_metadata(file_path)
                                archived_at = datetime.fromisoformat(
                                    metadata["archived_at"]
                                )

                                if start_date and archived_at < start_date:
                                    continue
                                if end_date and archived_at > end_date:
                                    continue

                            except Exception:
                                continue

                        archives.append(str(relative_path))

            return sorted(archives)

        except Exception as e:
            logger.error(f"Failed to list archives: {e}")
            return []

    def _generate_path(self, entity_id: str, entity_type: str) -> Path:
        """Generate file path for archive."""
        # Create hash-based subdirectory for distribution
        id_hash = hashlib.md5(entity_id.encode()).hexdigest()

        if self.partition_by_date:
            # Partition by date
            date_str = datetime.utcnow().strftime("%Y/%m/%d")
            path = (
                self.base_path
                / entity_type
                / date_str
                / id_hash[:2]
                / f"{entity_id}.json"
            )
        else:
            # Just use hash distribution
            path = (
                self.base_path
                / entity_type
                / id_hash[:2]
                / id_hash[2:4]
                / f"{entity_id}.json"
            )

        if self.use_compression:
            path = path.with_suffix(".json.gz")

        return path

    def _get_date_partitions(
        self,
        entity_type: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> List[Path]:
        """Get date partition paths to search."""
        partitions = []

        # Default to last 30 days if no range specified
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # Generate paths for each day in range
        current = start_date.date()
        end = end_date.date()

        while current <= end:
            date_str = current.strftime("%Y/%m/%d")
            partitions.append(self.base_path / entity_type / date_str)
            current += timedelta(days=1)

        return partitions

    async def _read_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Read metadata from archive file."""
        async with aiofiles.open(file_path, "rb") as f:
            content = await f.read()

        if file_path.suffix == ".gz":
            import gzip

            content = gzip.decompress(content)

        archive_data = json.loads(content.decode("utf-8"))
        return archive_data["metadata"]

    def get_metrics(self) -> Dict[str, Any]:
        """Get backend metrics."""
        return self._metrics.copy()


class S3ArchiveBackend:
    """
    S3-based archive backend.

    Stores archived data in S3 with metadata tags.
    """

    def __init__(
        self,
        bucket_name: str,
        prefix: str = "archives",
        region: str = "us-east-1",
        storage_class: str = "STANDARD_IA",
    ):
        """
        Initialize S3 backend.

        Args:
            bucket_name: S3 bucket name
            prefix: Key prefix for archives
            region: AWS region
            storage_class: S3 storage class
        """
        self.bucket_name = bucket_name
        self.prefix = prefix
        self.region = region
        self.storage_class = storage_class

        # Note: In production, would use boto3
        # This is a mock implementation
        self._storage: Dict[str, tuple[bytes, Dict[str, str]]] = {}

        logger.info(
            f"S3 archive backend initialized (mock mode): "
            f"bucket={bucket_name}, prefix={prefix}"
        )

    async def archive(self, entity_id: str, entity_type: str, data: bytes) -> str:
        """Archive entity data to S3."""
        try:
            # Generate S3 key
            key = self._generate_key(entity_id, entity_type)

            # Create metadata tags
            tags = {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "archived_at": datetime.utcnow().isoformat(),
                "size_bytes": str(len(data)),
                "checksum": hashlib.sha256(data).hexdigest(),
            }

            # Mock S3 upload
            self._storage[key] = (data, tags)

            logger.debug(f"Archived {entity_id} to S3: {key}")

            return key

        except Exception as e:
            logger.error(f"Failed to archive to S3: {e}")
            raise

    async def retrieve(self, archive_location: str) -> bytes:
        """Retrieve archived data from S3."""
        try:
            if archive_location not in self._storage:
                raise KeyError(f"Archive not found in S3: {archive_location}")

            data, tags = self._storage[archive_location]

            # Verify checksum
            checksum = hashlib.sha256(data).hexdigest()
            if checksum != tags.get("checksum"):
                raise ValueError(f"Checksum mismatch for {archive_location}")

            return data

        except Exception as e:
            logger.error(f"Failed to retrieve from S3: {e}")
            raise

    async def delete(self, archive_location: str) -> bool:
        """Delete archived data from S3."""
        try:
            if archive_location in self._storage:
                del self._storage[archive_location]
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete from S3: {e}")
            raise

    async def list_archives(
        self,
        entity_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[str]:
        """List archived entities in S3."""
        archives = []

        prefix = f"{self.prefix}/{entity_type}/"

        for key, (_, tags) in self._storage.items():
            if not key.startswith(prefix):
                continue

            # Check entity type
            if tags.get("entity_type") != entity_type:
                continue

            # Check date range
            if start_date or end_date:
                archived_at = datetime.fromisoformat(tags["archived_at"])
                if start_date and archived_at < start_date:
                    continue
                if end_date and archived_at > end_date:
                    continue

            archives.append(key)

        return sorted(archives)

    def _generate_key(self, entity_id: str, entity_type: str) -> str:
        """Generate S3 key for archive."""
        date_str = datetime.utcnow().strftime("%Y/%m/%d")
        return f"{self.prefix}/{entity_type}/{date_str}/{entity_id}.json"


class PostgreSQLArchiveBackend:
    """
    PostgreSQL-based archive backend.

    Stores archived data in PostgreSQL with JSONB support.
    """

    def __init__(
        self,
        connection_string: str,
        table_name: str = "game_archives",
        use_compression: bool = True,
    ):
        """
        Initialize PostgreSQL backend.

        Args:
            connection_string: PostgreSQL connection string
            table_name: Table name for archives
            use_compression: Whether to compress data
        """
        self.connection_string = connection_string
        self.table_name = table_name
        self.use_compression = use_compression

        # Note: In production, would use asyncpg
        # This is a mock implementation
        self._storage: Dict[str, Dict[str, Any]] = {}

        logger.info(
            f"PostgreSQL archive backend initialized (mock mode): "
            f"table={table_name}"
        )

    async def archive(self, entity_id: str, entity_type: str, data: bytes) -> str:
        """Archive entity data to PostgreSQL."""
        try:
            # Compress if enabled
            if self.use_compression:
                import gzip

                data = gzip.compress(data, compresslevel=6)

            # Create record
            record = {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "data": data.hex(),  # Store as hex string
                "compressed": self.use_compression,
                "size_bytes": len(data),
                "checksum": hashlib.sha256(data).hexdigest(),
                "archived_at": datetime.utcnow().isoformat(),
                "metadata": {},
            }

            # Mock insert
            location = f"{entity_type}:{entity_id}"
            self._storage[location] = record

            return location

        except Exception as e:
            logger.error(f"Failed to archive to PostgreSQL: {e}")
            raise

    async def retrieve(self, archive_location: str) -> bytes:
        """Retrieve archived data from PostgreSQL."""
        try:
            if archive_location not in self._storage:
                raise KeyError(f"Archive not found: {archive_location}")

            record = self._storage[archive_location]

            # Get data
            data = bytes.fromhex(record["data"])

            # Decompress if needed
            if record["compressed"]:
                import gzip

                data = gzip.decompress(data)

            return data

        except Exception as e:
            logger.error(f"Failed to retrieve from PostgreSQL: {e}")
            raise

    async def delete(self, archive_location: str) -> bool:
        """Delete archived data from PostgreSQL."""
        try:
            if archive_location in self._storage:
                del self._storage[archive_location]
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete from PostgreSQL: {e}")
            raise

    async def list_archives(
        self,
        entity_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[str]:
        """List archived entities in PostgreSQL."""
        archives = []

        for location, record in self._storage.items():
            if record["entity_type"] != entity_type:
                continue

            # Check date range
            if start_date or end_date:
                archived_at = datetime.fromisoformat(record["archived_at"])
                if start_date and archived_at < start_date:
                    continue
                if end_date and archived_at > end_date:
                    continue

            archives.append(location)

        return sorted(archives)


class CompositeArchiveBackend:
    """
    Composite backend that can use multiple backends.

    Supports tiered storage and migration between backends.
    """

    def __init__(self, backends: List[tuple[str, Any, Optional[timedelta]]]):
        """
        Initialize composite backend.

        Args:
            backends: List of (name, backend, age_threshold) tuples
        """
        self.backends = backends
        self._primary = backends[0][1] if backends else None

    async def archive(self, entity_id: str, entity_type: str, data: bytes) -> str:
        """Archive to primary backend."""
        if not self._primary:
            raise RuntimeError("No backends configured")

        location = await self._primary.archive(entity_id, entity_type, data)
        return f"{self.backends[0][0]}:{location}"

    async def retrieve(self, archive_location: str) -> bytes:
        """Retrieve from appropriate backend."""
        # Parse backend name and location
        parts = archive_location.split(":", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid archive location: {archive_location}")

        backend_name, location = parts

        # Find backend
        for name, backend, _ in self.backends:
            if name == backend_name:
                return await backend.retrieve(location)

        raise KeyError(f"Backend not found: {backend_name}")

    async def delete(self, archive_location: str) -> bool:
        """Delete from appropriate backend."""
        parts = archive_location.split(":", 1)
        if len(parts) != 2:
            return False

        backend_name, location = parts

        for name, backend, _ in self.backends:
            if name == backend_name:
                return await backend.delete(location)

        return False

    async def list_archives(
        self,
        entity_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[str]:
        """List from all backends."""
        all_archives = []

        for name, backend, _ in self.backends:
            archives = await backend.list_archives(entity_type, start_date, end_date)
            all_archives.extend(f"{name}:{loc}" for loc in archives)

        return sorted(all_archives)
