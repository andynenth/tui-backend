# backend/api/middleware/static_cache.py

from fastapi import Request, Response
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
import os


class NoCacheStaticFiles(StaticFiles):
    """Static file handler that adds cache control headers to prevent caching issues"""
    
    async def get_response(self, path: str, scope) -> Response:
        """Override to add cache control headers"""
        response = await super().get_response(path, scope)
        
        # Add cache control headers for JavaScript and CSS files
        if path.endswith(('.js', '.css')):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response