"""
EHR (Electronic Health Record) tool for retrieving patient data.
"""
import json
import asyncio
import random
import os
from typing import List, Dict, Optional
from config import Config
from tools.base import BaseTool


class EHRTool(BaseTool):
    """Tool for retrieving EHR data."""
    
    def __init__(self):
        super().__init__("EHR")
        
    async def _run(self, patient_id: str) -> dict:
        """
        Retrieve electronic health record data for a patient.
        """
        # Simulate network delay
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        file_path = os.path.join(Config.EHR_DIR, f"{patient_id}_ehr.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"EHR data not found for patient {patient_id}")
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Malformed EHR data for patient {patient_id}", 
                e.doc, 
                e.pos
            )

# Singleton instance
_ehr_tool = EHRTool()

async def get_ehr(patient_id: str) -> dict:
    """Wrapper for backward compatibility and easy import."""
    return await _ehr_tool.execute(patient_id)


async def get_historical_conditions(patient_id: str) -> List[Dict]:
    """Get historical conditions (including past/resolved conditions)."""
    ehr_data = await get_ehr(patient_id)
    
    conditions = ehr_data.get('conditions', [])
    historical = ehr_data.get('historical_conditions', [])
    
    return conditions + historical


async def get_past_conditions(patient_id: str) -> List[Dict]:
    """Get only past/resolved conditions."""
    all_conditions = await get_historical_conditions(patient_id)
    
    return [
        cond for cond in all_conditions 
        if cond.get('status', 'active').lower() in ['past', 'resolved', 'history']
    ]


async def has_condition_history(patient_id: str, condition_keywords: List[str]) -> bool:
    """Check if patient has history of specific condition(s)."""
    all_conditions = await get_historical_conditions(patient_id)
    condition_names = [cond.get('name', '').lower() for cond in all_conditions]
    
    for keyword in condition_keywords:
        keyword_lower = keyword.lower()
        for condition_name in condition_names:
            if keyword_lower in condition_name or condition_name in keyword_lower:
                return True
    return False


async def get_condition_timeline(patient_id: str) -> List[Dict]:
    """Get chronological timeline of patient conditions."""
    all_conditions = await get_historical_conditions(patient_id)
    
    conditions_with_dates = [c for c in all_conditions if c.get('onset')]
    conditions_with_dates.sort(key=lambda x: x.get('onset', ''), reverse=True)
    
    return conditions_with_dates


async def get_patient_demographics(patient_id: str) -> Dict:
    """Get patient demographics from EHR."""
    ehr_data = await get_ehr(patient_id)
    return ehr_data.get('demographics', {})


async def get_allergies(patient_id: str) -> List[Dict]:
    """Get patient allergies from EHR."""
    ehr_data = await get_ehr(patient_id)
    return ehr_data.get('allergies', [])

