"""
Laboratory results tool for retrieving patient lab data.
"""
import json
import asyncio
import random
import os
from config import Config
from tools.base import BaseTool


class LabsTool(BaseTool):
    """Tool for retrieving lab results."""
    
    def __init__(self):
        super().__init__("Labs")
        
    async def _run(self, patient_id: str) -> dict:
        """
        Retrieve laboratory results for a patient.
        """
        # Simulate network delay
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        file_path = os.path.join(Config.LABS_DIR, f"{patient_id}_labs.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Lab data not found for patient {patient_id}")
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Malformed lab data for patient {patient_id}", 
                e.doc, 
                e.pos
            )

# Singleton instance
_labs_tool = LabsTool()

async def get_labs(patient_id: str) -> dict:
    """Wrapper for backward compatibility and easy import."""
    return await _labs_tool.execute(patient_id)

