"""
EHR (Electronic Health Record) tool for retrieving patient data.
"""
import json
import time
import random
import os
from config import Config


def get_ehr(patient_id: str) -> dict:
    """
    Retrieve electronic health record data for a patient.
    
    Args:
        patient_id: Unique identifier for the patient
        
    Returns:
        Dictionary containing patient EHR data
        
    Raises:
        FileNotFoundError: If patient EHR file doesn't exist
        json.JSONDecodeError: If EHR file is malformed
    """
    # Simulate network delay
    time.sleep(random.uniform(0.3, 0.8))
    
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

