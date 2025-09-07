# backend/config/version.py
"""Version management for the application."""

import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_app_version():
    """Get application version dynamically with multiple fallbacks."""

    # Method 1: Environment variable (highest priority)
    if os.getenv("APP_VERSION"):
        version = os.getenv("APP_VERSION")
        logger.info(f"Version from environment: {version}")
        return version

    # Method 2: frontend-package.json in production (most reliable in Docker)
    prod_package_path = Path("/app/frontend-package.json")
    if prod_package_path.exists():
        try:
            with open(prod_package_path, "r") as f:
                data = json.load(f)
                version = data.get("version", "1.0.0")
                logger.info(f"Version from frontend-package.json: {version}")
                return version
        except Exception as e:
            logger.warning(f"Failed to read frontend-package.json: {e}")

    # Method 3: VERSION file (legacy fallback)
    version_file = Path("/app/VERSION")
    if version_file.exists():
        try:
            version = version_file.read_text().strip()
            logger.info(f"Version from VERSION file: {version}")
            return version
        except Exception as e:
            logger.warning(f"Failed to read VERSION file: {e}")

    # Method 4: Development - read from frontend/package.json
    try:
        current_dir = Path(__file__).resolve()
        project_root = current_dir.parent.parent.parent
        dev_package_path = project_root / "frontend" / "package.json"

        if dev_package_path.exists():
            with open(dev_package_path, "r") as f:
                data = json.load(f)
                version = data.get("version", "1.0.0")
                logger.info(f"Version from development package.json: {version}")
                return version
    except Exception as e:
        logger.warning(f"Failed to read development package.json: {e}")

    # Final fallback
    logger.warning("All version detection methods failed, using default")
    return "1.0.0"


# Cache the version at import time
APP_VERSION = get_app_version()
logger.info(f"Application version initialized: {APP_VERSION}")
