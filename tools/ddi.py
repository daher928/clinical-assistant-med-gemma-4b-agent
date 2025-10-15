"""
Drug-Drug Interaction (DDI) checker tool.
"""
import json
import time
import random
import os
from typing import List, Dict
from config import Config


def query_ddi(medications: List[Dict]) -> List[Dict]:
    """
    Check for potential drug-drug interactions.
    
    Args:
        medications: List of medication dictionaries with 'name' field
        
    Returns:
        List of interaction dictionaries with severity and description
        
    Raises:
        FileNotFoundError: If DDI matrix file doesn't exist
        json.JSONDecodeError: If DDI file is malformed
    """
    # Simulate network delay
    time.sleep(random.uniform(0.3, 0.8))
    
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

