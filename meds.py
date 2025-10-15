"""
Medication tool for retrieving patient medication data.
"""
import json
import time
import random
import os
from config import Config


def get_meds(patient_id: str) -> dict:
    """
    Retrieve medication information for a patient.
    
    Args:
        patient_id: Unique identifier for the patient
        
    Returns:
        Dictionary containing medication data
        
    Raises:
        FileNotFoundError: If patient meds file doesn't exist
        json.JSONDecodeError: If meds file is malformed
    """
    # Simulate network delay
    time.sleep(random.uniform(0.3, 0.8))
    
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

