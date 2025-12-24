"""
Base class for all clinical tools.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Abstract base class for clinical tools."""
    
    def __init__(self, name: str):
        self.name = name
    
    async def execute(self, *args, **kwargs) -> Any:
        """
        Execute the tool with standardized error handling and logging.
        """
        try:
            logger.info(f"Tool {self.name} started with args: {args} kwargs: {kwargs}")
            result = await self._run(*args, **kwargs)
            logger.info(f"Tool {self.name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {self.name} failed: {str(e)}")
            raise e
            
    @abstractmethod
    async def _run(self, *args, **kwargs) -> Any:
        """
        Implementation of the tool logic.
        """
        pass
