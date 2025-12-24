"""
Imaging tool for retrieving patient imaging data and reports.
"""
import json
import asyncio
import random
import os
from config import Config
from tools.base import BaseTool


class ImagingTool(BaseTool):
    """Tool for retrieving imaging results."""
    
    def __init__(self):
        super().__init__("Imaging")
        
    async def _run(self, patient_id: str) -> dict:
        """
        Retrieve imaging results for a patient.
        """
        # Simulate network delay
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        file_path = os.path.join(Config.IMAGING_DIR, f"{patient_id}_imaging.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Imaging data not found for patient {patient_id}")
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Malformed imaging data for patient {patient_id}", 
                e.doc, 
                e.pos
            )

# Singleton instance
_imaging_tool = ImagingTool()

async def get_imaging(patient_id: str) -> dict:
    """Wrapper for backward compatibility and easy import."""
    return await _imaging_tool.execute(patient_id)

