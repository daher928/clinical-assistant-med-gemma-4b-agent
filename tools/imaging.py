"""
Imaging tool for retrieving patient imaging data and reports.
"""
import json
import time
import random
import os
from config import Config


def get_imaging(patient_id: str) -> dict:
    """
    Retrieve imaging results for a patient.
    
    Args:
        patient_id: Unique identifier for the patient
        
    Returns:
        Dictionary containing imaging data and reports
        
    Raises:
        FileNotFoundError: If patient imaging file doesn't exist
        json.JSONDecodeError: If imaging file is malformed
    """
    # Simulate network delay
    time.sleep(random.uniform(0.3, 0.8))
    
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

