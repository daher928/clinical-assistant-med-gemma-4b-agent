"""
Medication tool for retrieving patient medication data.
"""
import json
import asyncio
import random
import os
from config import Config
from tools.base import BaseTool


class MedsTool(BaseTool):
    """Tool for retrieving medication data."""
    
    def __init__(self):
        super().__init__("Meds")
        
    async def _run(self, patient_id: str) -> dict:
        """
        Retrieve medication information for a patient.
        """
        # Simulate network delay
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        file_path = os.path.join(Config.MEDS_DIR, f"{patient_id}_meds.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Medication data not found for patient {patient_id}")
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Malformed medication data for patient {patient_id}", 
                e.doc, 
                e.pos
            )

# Singleton instance
_meds_tool = MedsTool()

async def get_meds(patient_id: str) -> dict:
    """Wrapper for backward compatibility and easy import."""
    return await _meds_tool.execute(patient_id)

