"""
Safety Checker Tool for comprehensive drug safety validation.

This tool provides various safety checking functions that can be used
by the Safety Monitor Agent and other components.
"""
import json
import os
from typing import List, Dict, Optional, Tuple
from config import Config


def check_drug_safety(drug_name: str, patient_data: Dict) -> Dict:
    """
    Comprehensive drug safety check for a single medication.
    
    Args:
        drug_name: Name of the drug to check
        patient_data: Complete patient context (EHR, labs, meds, etc.)
        
    Returns:
        Dictionary with safety analysis results
    """
    safety_results = {
        'drug_name': drug_name,
        'safe': True,
        'warnings': [],
        'contraindications': [],
        'interactions': [],
        'dosing_notes': [],
        'recommendations': []
    }
    
    # Check allergies
    allergies = patient_data.get('EHR', {}).get('allergies', [])
    allergy_check = _check_allergies(drug_name, allergies)
    if allergy_check['has_allergy']:
        safety_results['safe'] = False
        safety_results['warnings'].append({
            'type': 'allergy',
            'severity': 'critical',
            'message': allergy_check['message'],
            'recommendation': 'DO NOT PRESCRIBE'
        })
    
    # Check contraindications
    conditions = patient_data.get('EHR', {}).get('conditions', [])
    labs = patient_data.get('LABS', {}).get('results', [])
    contraindications = _check_contraindications(drug_name, conditions, labs)
    safety_results['contraindications'].extend(contraindications)
    
    if contraindications:
        safety_results['safe'] = False
    
    # Check drug interactions
    current_meds = patient_data.get('MEDS', {}).get('active', [])
    interactions = _check_drug_interactions(drug_name, current_meds)
    safety_results['interactions'].extend(interactions)
    
    if interactions:
        safety_results['safe'] = False
    
    # Check dosing appropriateness
    dosing_notes = _check_dosing_appropriateness(drug_name, patient_data)
    safety_results['dosing_notes'].extend(dosing_notes)
    
    # Generate recommendations
    recommendations = _generate_safety_recommendations(safety_results)
    safety_results['recommendations'].extend(recommendations)
    
    return safety_results


def validate_prescription(prescription: Dict, patient_data: Dict) -> Dict:
    """
    Validate a complete prescription against patient data.
    
    Args:
        prescription: Prescription details (name, dose, frequency, etc.)
        patient_data: Complete patient context
        
    Returns:
        Validation results with safety analysis
    """
    drug_name = prescription.get('name', '')
    dose = prescription.get('dose', '')
    frequency = prescription.get('frequency', '')
    
    # Basic drug safety check
    safety_results = check_drug_safety(drug_name, patient_data)
    
    # Add prescription-specific validation
    prescription_validation = {
        'prescription_valid': True,
        'dose_appropriate': True,
        'frequency_appropriate': True,
        'duration_appropriate': True
    }
    
    # Check dose appropriateness
    if not _is_dose_appropriate(drug_name, dose, patient_data):
        prescription_validation['dose_appropriate'] = False
        prescription_validation['prescription_valid'] = False
    
    # Check frequency appropriateness
    if not _is_frequency_appropriate(drug_name, frequency, patient_data):
        prescription_validation['frequency_appropriate'] = False
        prescription_validation['prescription_valid'] = False
    
    return {
        'drug_safety': safety_results,
        'prescription_validation': prescription_validation,
        'overall_safe': safety_results['safe'] and prescription_validation['prescription_valid']
    }


def get_drug_contraindications(drug_name: str) -> List[Dict]:
    """
    Get contraindications for a specific drug.
    
    Args:
        drug_name: Name of the drug
        
    Returns:
        List of contraindication dictionaries
    """
    # Try to load from comprehensive drug database first
    try:
        import json
        import os
        from config import Config
        
        db_path = os.path.join(Config.DRUGS_DIR, "drug_database.json")
        if os.path.exists(db_path):
            with open(db_path, 'r') as f:
                drug_db = json.load(f)
                drugs = drug_db.get('drugs', {})
                drug_lower = drug_name.lower()
                
                # Direct match
                if drug_lower in drugs:
                    return drugs[drug_lower].get('contraindications', [])
                
                # Partial match
                for key, value in drugs.items():
                    if key in drug_lower or drug_lower in key:
                        return value.get('contraindications', [])
    except Exception:
        pass
    
    # Fallback to simplified lookup
    contraindications_db = {
        'metformin': [
            {
                'condition': 'severe renal impairment',
                'severity': 'critical',
                'description': 'Contraindicated if eGFR <30',
                'alternative': 'Insulin therapy'
            },
            {
                'condition': 'severe hepatic impairment',
                'severity': 'high',
                'description': 'Use with caution in liver disease',
                'alternative': 'Insulin therapy'
            }
        ],
        'lisinopril': [
            {
                'condition': 'pregnancy',
                'severity': 'critical',
                'description': 'Contraindicated in pregnancy',
                'alternative': 'Methyldopa or labetalol'
            },
            {
                'condition': 'bilateral renal artery stenosis',
                'severity': 'high',
                'description': 'May cause acute renal failure',
                'alternative': 'Calcium channel blocker'
            }
        ],
        'warfarin': [
            {
                'condition': 'active bleeding',
                'severity': 'critical',
                'description': 'Contraindicated with active bleeding',
                'alternative': 'Mechanical prophylaxis'
            },
            {
                'condition': 'severe thrombocytopenia',
                'severity': 'high',
                'description': 'High bleeding risk',
                'alternative': 'DOAC or aspirin'
            }
        ]
    }
    
    return contraindications_db.get(drug_name.lower(), [])


def get_drug_interactions(drug_name: str, other_meds: List[str]) -> List[Dict]:
    """
    Get drug interactions for a specific drug with other medications.
    
    Args:
        drug_name: Name of the drug to check
        other_meds: List of other medication names
        
    Returns:
        List of interaction dictionaries
    """
    interactions = []
    
    # Common interaction patterns
    interaction_patterns = {
        'warfarin': {
            'aspirin': {
                'severity': 'high',
                'description': 'Increased bleeding risk',
                'recommendation': 'Monitor INR closely, consider PPI'
            },
            'metformin': {
                'severity': 'moderate',
                'description': 'May affect INR',
                'recommendation': 'Monitor INR more frequently'
            }
        },
        'digoxin': {
            'furosemide': {
                'severity': 'high',
                'description': 'Hypokalemia increases digoxin toxicity',
                'recommendation': 'Monitor potassium and digoxin levels'
            }
        },
        'metformin': {
            'furosemide': {
                'severity': 'moderate',
                'description': 'May increase metformin levels',
                'recommendation': 'Monitor renal function closely'
            }
        }
    }
    
    drug_interactions = interaction_patterns.get(drug_name.lower(), {})
    
    for other_med in other_meds:
        if other_med.lower() in drug_interactions:
            interaction = drug_interactions[other_med.lower()].copy()
            interaction['interacting_drug'] = other_med
            interactions.append(interaction)
    
    return interactions


def suggest_alternatives(drug_name: str, contraindication_reason: str) -> List[str]:
    """
    Suggest alternative medications based on contraindication.
    
    Args:
        drug_name: Original drug name
        contraindication_reason: Reason for contraindication
        
    Returns:
        List of alternative drug names
    """
    alternatives_db = {
        'metformin': {
            'renal_impairment': ['Insulin therapy', 'Sulfonylurea', 'DPP-4 inhibitor'],
            'liver_disease': ['Insulin therapy', 'Sulfonylurea']
        },
        'lisinopril': {
            'pregnancy': ['Methyldopa', 'Labetalol', 'Nifedipine'],
            'cough': ['ARB (losartan)', 'Calcium channel blocker']
        },
        'warfarin': {
            'bleeding_risk': ['DOAC (apixaban)', 'Aspirin', 'Mechanical prophylaxis']
        }
    }
    
    drug_alternatives = alternatives_db.get(drug_name.lower(), {})
    
    # Match contraindication reason to alternatives
    for reason, alts in drug_alternatives.items():
        if reason.lower() in contraindication_reason.lower():
            return alts
    
    # Default alternatives
    default_alternatives = {
        'metformin': ['Insulin therapy', 'Sulfonylurea'],
        'lisinopril': ['ARB (losartan)', 'Calcium channel blocker'],
        'warfarin': ['DOAC (apixaban)', 'Aspirin']
    }
    
    return default_alternatives.get(drug_name.lower(), ['Consult pharmacy'])


# Helper functions
def _check_allergies(drug_name: str, allergies: List[Dict]) -> Dict:
    """Check if patient has allergies to the drug."""
    drug_lower = drug_name.lower()
    
    for allergy in allergies:
        allergy_name = allergy.get('name', '').lower()
        if drug_lower in allergy_name or allergy_name in drug_lower:
            return {
                'has_allergy': True,
                'message': f'Patient allergic to {allergy.get("name", "unknown")}',
                'severity': allergy.get('severity', 'unknown')
            }
    
    return {'has_allergy': False}


def _check_contraindications(drug_name: str, conditions: List[Dict], labs: List[Dict]) -> List[Dict]:
    """Check for contraindications based on patient conditions."""
    contraindications = []
    drug_contraindications = get_drug_contraindications(drug_name)
    
    # Get condition names
    condition_names = [cond.get('name', '').lower() for cond in conditions]
    
    for contraindication in drug_contraindications:
        condition_match = contraindication['condition'].lower()
        
        # Check if any patient condition matches contraindication
        for condition in condition_names:
            if condition_match in condition or condition in condition_match:
                contraindications.append({
                    'condition': condition,
                    'severity': contraindication['severity'],
                    'description': contraindication['description'],
                    'alternative': contraindication.get('alternative')
                })
    
    return contraindications


def _check_drug_interactions(drug_name: str, current_meds: List[Dict]) -> List[Dict]:
    """Check for drug interactions with current medications."""
    interactions = []
    current_med_names = [med.get('name', '') for med in current_meds]
    
    drug_interactions = get_drug_interactions(drug_name, current_med_names)
    interactions.extend(drug_interactions)
    
    return interactions


def _check_dosing_appropriateness(drug_name: str, patient_data: Dict) -> List[Dict]:
    """Check if dosing is appropriate for the patient."""
    dosing_notes = []
    
    # Get patient demographics
    ehr = patient_data.get('EHR', {})
    age = ehr.get('age', 0)
    weight = ehr.get('weight', 0)
    labs = patient_data.get('LABS', {}).get('results', [])
    
    # Age-based dosing considerations
    if age > 65:
        dosing_notes.append({
            'type': 'age',
            'message': f'Patient is {age} years old - consider reduced dosing',
            'severity': 'medium'
        })
    
    # Weight-based considerations
    if weight > 0:
        bmi = weight / ((ehr.get('height', 1.7) / 100) ** 2) if ehr.get('height') else 0
        if bmi > 30:
            dosing_notes.append({
                'type': 'weight',
                'message': 'Obese patient - may need higher doses',
                'severity': 'low'
            })
    
    # Renal function considerations
    if _requires_renal_adjustment(drug_name):
        egfr = _get_lab_value(labs, 'eGFR')
        if egfr and egfr < 30:
            dosing_notes.append({
                'type': 'renal',
                'message': f'Renal impairment (eGFR {egfr}) - dose adjustment required',
                'severity': 'high'
            })
    
    return dosing_notes


def _is_dose_appropriate(drug_name: str, dose: str, patient_data: Dict) -> bool:
    """Check if the prescribed dose is appropriate."""
    # This would need a comprehensive dosing database
    # For now, basic validation
    try:
        dose_value = float(dose.replace('mg', '').replace('g', ''))
        
        # Basic dose ranges (simplified)
        dose_ranges = {
            'metformin': (500, 2000),  # mg
            'lisinopril': (2.5, 40),   # mg
            'atorvastatin': (10, 80),  # mg
            'furosemide': (20, 200)    # mg
        }
        
        if drug_name.lower() in dose_ranges:
            min_dose, max_dose = dose_ranges[drug_name.lower()]
            return min_dose <= dose_value <= max_dose
        
        return True  # Unknown drug, assume appropriate
        
    except (ValueError, TypeError):
        return False  # Invalid dose format


def _is_frequency_appropriate(drug_name: str, frequency: str, patient_data: Dict) -> bool:
    """Check if the prescribed frequency is appropriate."""
    # Basic frequency validation
    valid_frequencies = [
        'once daily', 'twice daily', 'three times daily', 'four times daily',
        'once a day', 'twice a day', 'three times a day', 'four times a day',
        'daily', 'bid', 'tid', 'qid', 'prn'
    ]
    
    frequency_lower = frequency.lower()
    return any(valid_freq in frequency_lower for valid_freq in valid_frequencies)


def _generate_safety_recommendations(safety_results: Dict) -> List[str]:
    """Generate actionable recommendations from safety results."""
    recommendations = []
    
    # Critical warnings
    critical_warnings = [w for w in safety_results['warnings'] if w.get('severity') == 'critical']
    for warning in critical_warnings:
        recommendations.append(f"🚨 CRITICAL: {warning['message']} - {warning['recommendation']}")
    
    # High priority warnings
    high_warnings = [w for w in safety_results['warnings'] if w.get('severity') == 'high']
    for warning in high_warnings:
        recommendations.append(f"⚠️ HIGH: {warning['message']} - {warning['recommendation']}")
    
    # Contraindications
    for contraindication in safety_results['contraindications']:
        if contraindication['severity'] == 'critical':
            recommendations.append(f"🚫 CONTRAINDICATED: {contraindication['description']}")
        elif contraindication['severity'] == 'high':
            recommendations.append(f"⚠️ CAUTION: {contraindication['description']}")
    
    return recommendations


def _requires_renal_adjustment(drug_name: str) -> bool:
    """Check if drug requires renal dose adjustment."""
    renal_drugs = [
        'metformin', 'digoxin', 'gabapentin', 'pregabalin', 'allopurinol',
        'colchicine', 'sulfamethoxazole', 'trimethoprim'
    ]
    return drug_name.lower() in renal_drugs


def _get_lab_value(labs: List[Dict], test_name: str) -> Optional[float]:
    """Get specific lab value from lab results."""
    for lab in labs:
        if lab.get('test', '').lower() == test_name.lower():
            try:
                return float(lab.get('value', 0))
            except (ValueError, TypeError):
                return None
    return None
