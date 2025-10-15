"""
Hybrid LLM + Structured Extraction.

Strategy: Use Python for exact values, LLM for reasoning and synthesis.

This prevents hallucinations while maintaining intelligent analysis.
"""
from typing import Dict, List


class StructuredExtractor:
    """
    Extract exact values from structured data using Python (no hallucinations).
    """
    
    @staticmethod
    def extract_patient_summary(observations: Dict) -> Dict:
        """
        Extract accurate patient summary from observations.
        
        Returns structured data with EXACT values from JSON.
        """
        ehr = observations.get('EHR', {})
        labs = observations.get('LABS', {})
        meds = observations.get('MEDS', {})
        ddi = observations.get('DDI', [])
        
        summary = {
            'demographics': {},
            'conditions': [],
            'vitals': {},
            'abnormal_labs': [],
            'lab_trends': [],
            'medications': [],
            'interactions': [],
            'critical_findings': []
        }
        
        # Extract demographics (EXACT from JSON)
        demo = ehr.get('demographics', {})
        summary['demographics'] = {
            'age': demo.get('age'),  # Will be 68, not 6!
            'gender': demo.get('gender'),
            'patient_id': ehr.get('patient_id')
        }
        
        # Extract conditions
        summary['conditions'] = [
            c.get('name') for c in ehr.get('conditions', [])
        ]
        
        # Extract vitals (EXACT)
        vitals = ehr.get('vitals', {})
        summary['vitals'] = {
            'bp': vitals.get('bp'),  # Will be "145/88", not "160/90"!
            'hr': vitals.get('hr'),
            'date': vitals.get('last_visit')
        }
        
        # Extract abnormal labs with EXACT values
        for lab in labs.get('results', []):
            if lab.get('status') in ['HIGH', 'LOW', 'CRITICAL_HIGH', 'CRITICAL_LOW']:
                summary['abnormal_labs'].append({
                    'test': lab['test'],
                    'value': lab['value'],  # EXACT value
                    'unit': lab['unit'],
                    'status': lab['status'],
                    'reference': lab['reference_range']
                })
        
        # Extract trends (EXACT values)
        historical = labs.get('historical_data', {})
        for lab in labs.get('results', []):
            test_name = lab['test']
            current = lab['value']
            
            # Find historical value
            hist_key = test_name.lower().replace(' ', '_') + '_6mo_ago'
            if hist_key in historical:
                past = historical[hist_key]
                if current != past:
                    direction = "↑" if current > past else "↓"
                    summary['lab_trends'].append({
                        'test': test_name,
                        'past': past,  # EXACT
                        'current': current,  # EXACT
                        'direction': direction,
                        'change_percent': round(abs((current - past) / past * 100), 1)
                    })
        
        # Extract medications
        summary['medications'] = [
            {
                'name': m.get('name'),
                'dose': m.get('dose'),
                'frequency': m.get('frequency'),
                'indication': m.get('indication')
            }
            for m in meds.get('active', [])
        ]
        
        # Extract DDIs
        if isinstance(ddi, list):
            summary['interactions'] = [
                {
                    'drugs': f"{d.get('a')} + {d.get('b')}",
                    'severity': d.get('severity'),
                    'description': d.get('description')
                }
                for d in ddi
            ]
        
        # Identify critical findings
        for lab in summary['abnormal_labs']:
            if lab['test'] == 'eGFR' and lab['value'] < 35:
                summary['critical_findings'].append(
                    f"Severe CKD: eGFR {lab['value']} (approaching dialysis threshold)"
                )
            if lab['test'] == 'Hemoglobin' and lab['value'] < 10:
                summary['critical_findings'].append(
                    f"Severe anemia: Hgb {lab['value']} (transfusion threshold)"
                )
            if lab['test'] == 'Potassium' and lab['value'] > 5.5:
                summary['critical_findings'].append(
                    f"Dangerous hyperkalemia: K+ {lab['value']} (arrhythmia risk)"
                )
        
        return summary
    
    @staticmethod
    def format_for_llm(structured_data: Dict) -> str:
        """
        Format extracted data for LLM in a way that prevents hallucination.
        
        Provides clear, unambiguous values that LLM can reference.
        """
        demo = structured_data['demographics']
        vitals = structured_data['vitals']
        
        formatted = f"""
=== VERIFIED PATIENT DATA (Use these EXACT values) ===

PATIENT: {demo['age']}yo {demo['gender']} (ID: {demo['patient_id']})

CONDITIONS: {', '.join(structured_data['conditions'])}

VITALS (from {vitals.get('date', 'recent visit')}):
- Blood Pressure: {vitals.get('bp', 'N/A')}
- Heart Rate: {vitals.get('hr', 'N/A')}

ABNORMAL LABS:
"""
        for lab in structured_data['abnormal_labs']:
            formatted += f"- {lab['test']}: {lab['value']} {lab['unit']} ({lab['status']}, ref: {lab['reference']})\n"
        
        formatted += "\nLAB TRENDS (6 months):\n"
        for trend in structured_data['lab_trends']:
            formatted += f"- {trend['test']}: {trend['past']} → {trend['current']} {trend['direction']} ({trend['change_percent']}% change)\n"
        
        formatted += "\nMEDICATIONS:\n"
        for med in structured_data['medications']:
            formatted += f"- {med['name']} {med['dose']} {med['frequency']}\n"
        
        if structured_data['interactions']:
            formatted += "\nDRUG INTERACTIONS:\n"
            for interaction in structured_data['interactions']:
                formatted += f"- {interaction['drugs']}: {interaction['severity']} - {interaction['description']}\n"
        
        if structured_data['critical_findings']:
            formatted += "\n🚨 CRITICAL FINDINGS:\n"
            for finding in structured_data['critical_findings']:
                formatted += f"- {finding}\n"
        
        formatted += "\n=== USE THESE EXACT VALUES IN YOUR SUMMARY ===\n"
        
        return formatted


class HybridLLMSystem:
    """
    Combines structured extraction (accurate) with LLM synthesis (intelligent).
    """
    
    @staticmethod
    def generate_summary(observations: Dict, patient_id: str, complaint: str, llm) -> str:
        """
        Generate clinical summary using hybrid approach.
        
        Process:
        1. Python extracts EXACT values
        2. Format values clearly for LLM
        3. LLM synthesizes narrative using provided values
        4. Result: Accurate + Intelligent
        """
        # Step 1: Extract exact values with Python
        extractor = StructuredExtractor()
        structured_data = extractor.extract_patient_summary(observations)
        
        # Step 2: Format for LLM (clean, simple)
        formatted_data = extractor.format_for_llm(structured_data)
        
        # Step 3: Build ULTRA-STRICT prompt with exact format
        simple_prompt = f"""Generate a clinical summary using ONLY the data below. Use bullet points, NO long paragraphs.

{formatted_data}

Chief Complaint: {complaint}

REQUIRED FORMAT (copy this structure exactly):

## ONE-LINE SUMMARY
[One short sentence, max 20 words]

## PATIENT SNAPSHOT
- Age/Gender: [from data]
- Conditions: [from data]
- BP: [exact value], HR: [exact value]

## ATTENTION NEEDED
- [Most critical finding from labs]
- [Second critical finding]
- [Trend if present]

## MEDICATION CONCERNS
- [List medications]
- [DDI if present]

## PLAN
1. [First action]
2. [Second action]
3. [Follow-up timing]

CRITICAL RULES:
- Use bullet points, NOT paragraphs
- Keep each bullet under 15 words
- Use exact numbers from data above
- Stop after PLAN section
- NO long sentences, NO rambling

Generate now:
"""
        
        # Step 4: LLM synthesizes with simplified observations
        # Just pass the formatted data, not raw JSON
        simplified_obs = {'FORMATTED_DATA': formatted_data}
        
        result = llm.synthesize(
            simple_prompt,
            "",  # Empty user prompt
            simplified_obs
        )
        
        return result

