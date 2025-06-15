# backend/api/controllers/BaseController.py

from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, Optional
import asyncio

class BaseController(ABC):
    """
    Base controller สำหรับ event-driven architecture
    ให้ common functionality และ patterns
    """
    
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_active = False
        
    async def start(self) -> bool:
        """เริ่มต้น controller"""
        try:
            self.logger.info(f"Starting {self.__class__.__name__} for room {self.room_id}")
            
            # Template method pattern
            await self._validate_prerequisites()
            await self._initialize_state()
            await self._setup_event_handlers()
            
            self.is_active = True
            await self._on_started()
            
            self.logger.info(f"{self.__class__.__name__} started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start {self.__class__.__name__}: {e}")
            await self.stop()
            return False
    
    async def stop(self) -> None:
        """หยุด controller และ cleanup"""
        if not self.is_active:
            return
            
        self.logger.info(f"Stopping {self.__class__.__name__} for room {self.room_id}")
        
        try:
            await self._cleanup()
            self.is_active = False
            self.logger.info(f"{self.__class__.__name__} stopped")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    @abstractmethod
    async def _validate_prerequisites(self) -> None:
        """ตรวจสอบ prerequisites (implement ใน subclass)"""
        pass
    
    @abstractmethod
    async def _initialize_state(self) -> None:
        """เตรียม state (implement ใน subclass)"""
        pass
    
    @abstractmethod
    async def _setup_event_handlers(self) -> None:
        """ตั้งค่า event handlers (implement ใน subclass)"""
        pass
    
    async def _on_started(self) -> None:
        """Hook หลังจาก start เสร็จ (override ถ้าต้องการ)"""
        pass
    
    async def _cleanup(self) -> None:
        """Cleanup resources (override ถ้าต้องการ)"""
        pass
    
    def _log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log events สำหรับ debugging"""
        self.logger.debug(f"Event: {event_type} | Room: {self.room_id} | Data: {data}")