"""
Drug-Drug Interaction (DDI) checker tool.
"""
import json
import asyncio
import random
import os
from typing import List, Dict
from config import Config
from tools.base import BaseTool


class DDITool(BaseTool):
    """Tool for checking drug-drug interactions."""
    
    def __init__(self):
        super().__init__("DDI")
        
    async def _run(self, medications: List[Dict]) -> List[Dict]:
        """
        Check for potential drug-drug interactions.
        """
        # Simulate network delay
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        file_path = os.path.join(Config.DRUGS_DIR, "ddi_matrix.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError("DDI matrix file not found")
        
        try:
            with open(file_path, 'r') as f:
                ddi_data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError("Malformed DDI matrix file", e.doc, e.pos)
        
        results = []
        med_names = [m.get("name", "") for m in medications]
        
        for pair in ddi_data.get("pairs", []):
            if pair["a"] in med_names and pair["b"] in med_names:
                results.append(pair)
        
        return results

# Singleton instance
_ddi_tool = DDITool()

async def query_ddi(medications: List[Dict]) -> List[Dict]:
    """Wrapper for backward compatibility and easy import."""
    return await _ddi_tool.execute(medications)

