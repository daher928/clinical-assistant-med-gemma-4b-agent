"""
Constrained LLM Generation - Use LLM but prevent hallucinations.

Strategy: 
1. Template extracts EXACT values
2. Build ULTRA-strict prompt with blanks to fill
3. LLM generates ONLY within those constraints
"""
from typing import Dict
from agent.template_generator import TemplateSummaryGenerator


class ConstrainedLLMGenerator:
    """
    Use LLM for narrative generation while constraining it with exact data.
    
    This gives you AI-powered summaries without hallucinations.
    """
    
    @staticmethod
    def generate_with_llm(observations: Dict, patient_id: str, complaint: str, llm) -> str:
        """
        Generate clinical summary using LLM with strict constraints.
        
        Process:
        1. Extract exact values with Python (from template generator)
        2. Build ultra-constrained prompt (fill-in-the-blanks style)
        3. LLM generates narrative using ONLY provided values
        4. Fallback to template if LLM fails
        """
        # Step 1: Get structured data from template generator
        template_result = TemplateSummaryGenerator.generate_from_data(
            observations, patient_id, complaint
        )
        
        # Step 2: Extract key values for LLM
        ehr = observations.get('EHR', {})
        labs = observations.get('LABS', {})
        meds = observations.get('MEDS', {})
        ddi = observations.get('DDI', [])
        
        demo = ehr.get('demographics', {})
        age = demo.get('age', '?')
        gender = demo.get('gender', '?')
        conditions = [c.get('name', '') for c in ehr.get('conditions', [])]
        vitals = ehr.get('vitals', {})
        
        # Build key lab values
        lab_values = {}
        for lab in labs.get('results', []):
            test_name = lab.get('test')
            lab_values[test_name] = {
                'value': lab.get('value'),
                'unit': lab.get('unit'),
                'status': lab.get('status')
            }
        
        # Build ultra-constrained prompt
        constrained_prompt = f"""You are a clinical assistant. Generate a concise clinical summary using ONLY the exact values provided below.

=== EXACT VALUES - DO NOT MODIFY ===
Patient: {age} year old {gender}
Conditions: {', '.join(conditions)}
Chief Complaint: {complaint}
Vital Signs: BP {vitals.get('bp')}, HR {vitals.get('hr')}, Temp {vitals.get('temp')}°F

Lab Results:
"""
        
        for test_name, lab_data in lab_values.items():
            constrained_prompt += f"- {test_name}: {lab_data['value']} {lab_data['unit']} ({lab_data['status']})\n"
        
        # Add historical trends
        historical = labs.get('historical_data', {})
        if historical:
            constrained_prompt += "\nHistorical Trends (6 months ago):\n"
            for key, value in historical.items():
                test_name = key.replace('_6mo_ago', '').replace('_', ' ').title()
                constrained_prompt += f"- {test_name}: was {value}\n"
        
        # Add medications
        active_meds = meds.get('active', [])
        if active_meds:
            constrained_prompt += "\nActive Medications:\n"
            for med in active_meds:
                constrained_prompt += f"- {med.get('name')} {med.get('dose')} {med.get('frequency')}\n"
        
        # Add DDIs
        if ddi:
            constrained_prompt += "\nDrug-Drug Interactions:\n"
            for interaction in ddi[:3]:
                constrained_prompt += f"- {interaction.get('a')} + {interaction.get('b')}: {interaction.get('severity')} - {interaction.get('description')}\n"
        
        constrained_prompt += """
=== END EXACT VALUES ===

CRITICAL INSTRUCTIONS:
1. Use ONLY the values provided above - copy them exactly
2. DO NOT make up any numbers, ages, or clinical data
3. Format your response as:
   - ONE-LINE SUMMARY (one sentence)
   - PATIENT SNAPSHOT (bullet points with exact values)
   - ATTENTION NEEDED (prioritize critical findings)
   - MEDICATION CONCERNS (list DDIs if present)
   - PLAN (evidence-based recommendations)

4. Keep it concise (under 250 words total)
5. NO code, NO extra patients, STOP after the plan
6. Use professional medical tone

Generate the summary now:
"""
        
        # Step 3: Try LLM generation with strict parameters
        try:
            # Ultra-conservative generation parameters
            system_prompt = "You are a clinical decision support assistant. Provide accurate, concise summaries using only provided data."
            
            result = llm.synthesize(
                system_prompt=system_prompt,
                user_prompt=constrained_prompt,
                observations=observations  # Pass for compatibility
            )
            
            # Validate result isn't garbage
            if result and len(result) > 100 and age and str(age) in result:
                return result
            else:
                # LLM output looks bad, use template
                print("⚠️  LLM output failed validation, using template fallback")
                return template_result
                
        except Exception as e:
            # LLM failed, use template
            print(f"⚠️  LLM generation failed: {e}, using template fallback")
            return template_result

