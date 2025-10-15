#!/usr/bin/env python3
"""Quick test of template generator."""

import sys
sys.path.insert(0, '/Users/ddaher/projects/clinical-assistant-agent')

from agent.template_generator import TemplateSummaryGenerator
from tools import ehr, labs, meds, imaging, ddi

# Test with P001
patient_id = "P001"
complaint = "Feeling tired and dizzy"

observations = {}
observations['EHR'] = ehr.get_ehr(patient_id)
observations['LABS'] = labs.get_labs(patient_id)
observations['MEDS'] = meds.get_meds(patient_id)
observations['IMAGING'] = imaging.get_imaging(patient_id)

# Get DDI by passing medications
med_list = observations['MEDS'].get('active', [])
observations['DDI'] = ddi.query_ddi(med_list)

print("=" * 80)
print("TESTING TEMPLATE GENERATOR")
print("=" * 80)

result = TemplateSummaryGenerator.generate_from_data(observations, patient_id, complaint)

print(result)
print("\n" + "=" * 80)
print("✅ TEST COMPLETE - Check output for accuracy")
print("=" * 80)

