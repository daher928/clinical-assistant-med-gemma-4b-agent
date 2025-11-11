"""
EHR (Electronic Health Record) tool for retrieving patient data.
"""
import json
import time
import random
import os
from typing import List, Dict, Optional
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


def get_historical_conditions(patient_id: str) -> List[Dict]:
    """
    Get historical conditions (including past/resolved conditions) for a patient.
    
    Args:
        patient_id: Unique identifier for the patient
        
    Returns:
        List of condition dictionaries with status (active/past/resolved)
    """
    ehr_data = get_ehr(patient_id)
    
    # Get all conditions (both active and historical)
    conditions = ehr_data.get('conditions', [])
    
    # Also check for historical_conditions if present
    historical = ehr_data.get('historical_conditions', [])
    
    # Combine and return all conditions
    all_conditions = conditions + historical
    
    return all_conditions


def get_past_conditions(patient_id: str) -> List[Dict]:
    """
    Get only past/resolved conditions (not currently active).
    
    Args:
        patient_id: Unique identifier for the patient
        
    Returns:
        List of past condition dictionaries
    """
    all_conditions = get_historical_conditions(patient_id)
    
    # Filter for past/resolved conditions
    past_conditions = [
        cond for cond in all_conditions 
        if cond.get('status', 'active').lower() in ['past', 'resolved', 'history']
    ]
    
    return past_conditions


def has_condition_history(patient_id: str, condition_keywords: List[str]) -> bool:
    """
    Check if patient has history of specific condition(s).
    
    Args:
        patient_id: Unique identifier for the patient
        condition_keywords: List of keywords to search for in condition names
        
    Returns:
        True if patient has history of any matching condition
    """
    all_conditions = get_historical_conditions(patient_id)
    
    condition_names = [cond.get('name', '').lower() for cond in all_conditions]
    
    for keyword in condition_keywords:
        keyword_lower = keyword.lower()
        for condition_name in condition_names:
            if keyword_lower in condition_name or condition_name in keyword_lower:
                return True
    
    return False


def get_condition_timeline(patient_id: str) -> List[Dict]:
    """
    Get chronological timeline of patient conditions.
    
    Args:
        patient_id: Unique identifier for the patient
        
    Returns:
        List of conditions sorted by onset date
    """
    all_conditions = get_historical_conditions(patient_id)
    
    # Sort by onset date if available
    conditions_with_dates = []
    for cond in all_conditions:
        onset = cond.get('onset', '')
        if onset:
            conditions_with_dates.append(cond)
    
    # Sort by onset date (most recent first)
    conditions_with_dates.sort(key=lambda x: x.get('onset', ''), reverse=True)
    
    return conditions_with_dates


def analyze_lab_trends(patient_id: str, lab_test: str, time_period_months: int = 6) -> Optional[Dict]:
    """
    Analyze trends for a specific lab test over time.
    
    Args:
        patient_id: Unique identifier for the patient
        lab_test: Name of lab test to analyze
        time_period_months: Number of months to look back
        
    Returns:
        Dictionary with trend analysis or None if insufficient data
    """
    # Import labs tool
    from tools import labs
    
    try:
        lab_data = labs.get_labs(patient_id)
        
        # Check if historical data is available
        historical_data = lab_data.get('historical_data', {})
        
        # Get current value
        current_results = lab_data.get('results', [])
        current_value = None
        for result in current_results:
            if result.get('test', '').lower() == lab_test.lower():
                current_value = result.get('value')
                break
        
        if current_value is None:
            return None
        
        # Look for historical value
        hist_key = lab_test.lower().replace(' ', '_') + f'_{time_period_months}mo_ago'
        historical_value = historical_data.get(hist_key)
        
        if historical_value is None:
            return None
        
        # Calculate trend
        try:
            current_float = float(current_value)
            hist_float = float(historical_value)
            
            change = current_float - hist_float
            percent_change = (change / hist_float * 100) if hist_float != 0 else 0
            
            trend_direction = "increasing" if change > 0 else "decreasing" if change < 0 else "stable"
            
            return {
                "test": lab_test,
                "current_value": current_value,
                "historical_value": historical_value,
                "change": change,
                "percent_change": percent_change,
                "trend_direction": trend_direction,
                "time_period_months": time_period_months
            }
        except (ValueError, TypeError):
            return None
            
    except Exception:
        return None


def get_patient_demographics(patient_id: str) -> Dict:
    """
    Get patient demographics from EHR.
    
    Args:
        patient_id: Unique identifier for the patient
        
    Returns:
        Dictionary with demographics
    """
    ehr_data = get_ehr(patient_id)
    return ehr_data.get('demographics', {})


def get_allergies(patient_id: str) -> List[Dict]:
    """
    Get patient allergies from EHR.
    
    Args:
        patient_id: Unique identifier for the patient
        
    Returns:
        List of allergy dictionaries
    """
    ehr_data = get_ehr(patient_id)
    return ehr_data.get('allergies', [])


def check_allergy_history(patient_id: str, drug_name: str) -> Optional[Dict]:
    """
    Check if patient has allergy history to a drug or drug class.
    
    Args:
        patient_id: Unique identifier for the patient
        drug_name: Name of drug to check
        
    Returns:
        Allergy dictionary if match found, None otherwise
    """
    allergies = get_allergies(patient_id)
    drug_lower = drug_name.lower()
    
    for allergy in allergies:
        allergen_name = allergy.get('allergen', '').lower() or allergy.get('name', '').lower()
        
        # Check exact match
        if drug_lower in allergen_name or allergen_name in drug_lower:
            return allergy
        
        # Check drug class matching (simplified)
        drug_classes = {
            'penicillin': ['amoxicillin', 'ampicillin', 'penicillin'],
            'sulfa': ['sulfamethoxazole', 'sulfasalazine'],
            'ace_inhibitor': ['lisinopril', 'enalapril', 'captopril']
        }
        
        for drug_class, members in drug_classes.items():
            if drug_class in allergen_name and drug_lower in [m.lower() for m in members]:
                return allergy
    
    return None

