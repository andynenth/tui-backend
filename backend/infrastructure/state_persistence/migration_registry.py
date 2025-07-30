"""
Migration registry for state machine migrations.

Provides automatic migration discovery and registration.
"""

from typing import Dict, List, Type, Optional
import logging
import importlib
import pkgutil
from pathlib import Path

from .versioning import StateMigration, MigrationRunner
from .abstractions import StateVersion


logger = logging.getLogger(__name__)


class MigrationRegistry:
    """
    Registry for state machine migrations.

    Features:
    - Automatic migration discovery
    - Version path calculation
    - Migration validation
    """

    def __init__(self):
        """Initialize migration registry."""
        self._migrations: Dict[str, StateMigration] = {}
        self._runner = MigrationRunner()

    def register_migration(self, migration: StateMigration) -> None:
        """Register a migration."""
        key = f"{migration.from_version}_{migration.to_version}"

        if key in self._migrations:
            logger.warning(f"Overwriting existing migration: {key}")

        self._migrations[key] = migration
        self._runner.register_migration(migration)

        logger.info(
            f"Registered migration: {migration.from_version} -> {migration.to_version}"
        )

    def discover_migrations(self, package_name: str = "migrations") -> int:
        """
        Discover and register migrations from a package.

        Returns number of migrations discovered.
        """
        count = 0

        try:
            # Import the migrations package
            migrations_module = importlib.import_module(
                f".{package_name}", package=__package__
            )

            # Get package path
            package_path = Path(migrations_module.__file__).parent

            # Discover all Python modules in the package
            for _, module_name, _ in pkgutil.iter_modules([str(package_path)]):
                if module_name.startswith("_"):
                    continue

                try:
                    # Import the module
                    module = importlib.import_module(
                        f".{package_name}.{module_name}", package=__package__
                    )

                    # Find migration classes
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)

                        if (
                            isinstance(attr, type)
                            and issubclass(attr, StateMigration)
                            and attr is not StateMigration
                        ):

                            # Instantiate and register
                            migration = attr()
                            self.register_migration(migration)
                            count += 1

                except Exception as e:
                    logger.error(f"Error loading migration module {module_name}: {e}")

        except Exception as e:
            logger.error(f"Error discovering migrations: {e}")

        logger.info(f"Discovered {count} migrations")
        return count

    def get_migration_path(
        self, from_version: StateVersion, to_version: StateVersion
    ) -> List[StateMigration]:
        """Get migration path between versions."""
        return self._runner._find_migration_path(from_version, to_version) or []

    def get_available_versions(self) -> List[StateVersion]:
        """Get all available versions."""
        versions = set()

        for migration in self._migrations.values():
            versions.add(migration.from_version)
            versions.add(migration.to_version)

        return sorted(versions)

    def get_latest_version(self) -> Optional[StateVersion]:
        """Get the latest available version."""
        versions = self.get_available_versions()
        return versions[-1] if versions else None

    def can_migrate(self, from_version: StateVersion, to_version: StateVersion) -> bool:
        """Check if migration path exists."""
        path = self.get_migration_path(from_version, to_version)
        return len(path) > 0

    async def migrate(
        self,
        state: Dict[str, Any],
        from_version: StateVersion,
        to_version: Optional[StateVersion] = None,
    ) -> Dict[str, Any]:
        """
        Migrate state to target version.

        If to_version is None, migrates to latest version.
        """
        if to_version is None:
            to_version = self.get_latest_version()
            if not to_version:
                logger.warning("No migrations available")
                return state

        return await self._runner.migrate(state, from_version, to_version)

    def get_migration_info(self) -> Dict[str, Any]:
        """Get information about registered migrations."""
        info = {
            "total_migrations": len(self._migrations),
            "available_versions": [str(v) for v in self.get_available_versions()],
            "latest_version": (
                str(self.get_latest_version()) if self.get_latest_version() else None
            ),
            "migrations": [],
        }

        for key, migration in self._migrations.items():
            info["migrations"].append(
                {
                    "from": str(migration.from_version),
                    "to": str(migration.to_version),
                    "class": migration.__class__.__name__,
                }
            )

        return info


# Global migration registry
_global_registry: Optional[MigrationRegistry] = None


def get_migration_registry() -> MigrationRegistry:
    """Get the global migration registry."""
    global _global_registry

    if _global_registry is None:
        _global_registry = MigrationRegistry()
        # Auto-discover migrations
        _global_registry.discover_migrations()

    return _global_registry


def register_migration(migration_class: Type[StateMigration]) -> Type[StateMigration]:
    """
    Decorator to register a migration class.

    Usage:
        @register_migration
        class MyMigration(StateMigration):
            ...
    """
    registry = get_migration_registry()
    registry.register_migration(migration_class())
    return migration_class
