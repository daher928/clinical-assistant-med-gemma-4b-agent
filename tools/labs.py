"""
Laboratory results tool for retrieving patient lab data.
"""
import json
import time
import random
import os
from config import Config


def get_labs(patient_id: str) -> dict:
    """
    Retrieve laboratory results for a patient.
    
    Args:
        patient_id: Unique identifier for the patient
        
    Returns:
        Dictionary containing lab results
        
    Raises:
        FileNotFoundError: If patient labs file doesn't exist
        json.JSONDecodeError: If labs file is malformed
    """
    # Simulate network delay
    time.sleep(random.uniform(0.3, 0.8))
    
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

