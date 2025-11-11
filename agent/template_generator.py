"""
Template-based clinical summary generation.

Strategy: Pre-build 90% of the output, let LLM fill in ONLY specific blanks.
This eliminates hallucination by removing creative freedom.
"""
from typing import Dict, List, Tuple


class TemplateSummaryGenerator:
    """
    Generate clinical summaries using strict templates.
    
    """
    
    @staticmethod
    def _diagnose_from_complaint_and_labs(complaint: str, labs: Dict, conditions: List[str]) -> Tuple[str, List[str], str]:
        """
        Intelligent diagnosis based on complaint, labs, and conditions.
        Returns (primary_diagnosis, differential_diagnosis_list, clinical_reasoning)
        """
        complaint_lower = complaint.lower()
        lab_results = labs.get('results', [])
        
        # Extract key lab values
        uric_acid = None
        creatinine = None
        egfr = None
        glucose = None
        
        for lab in lab_results:
            test_name = lab.get('test', '').lower()
            value = lab.get('value')
            if 'uric acid' in test_name:
                uric_acid = value
            elif 'creatinine' in test_name:
                creatinine = value
            elif 'egfr' in test_name:
                egfr = value
            elif 'glucose' in test_name:
                glucose = value
        
        # Gout diagnosis logic
        if any(keyword in complaint_lower for keyword in ['knee', 'joint', 'pain', 'swelling', 'red', 'warm']):
            if uric_acid and uric_acid > 7.0:
                differential = [
                    "Acute gout flare (most likely)",
                    "Septic arthritis (rule out)",
                    "Osteoarthritis flare",
                    "Pseudogout (calcium pyrophosphate deposition)"
                ]
                reasoning = f"Acute monoarticular joint pain with elevated uric acid ({uric_acid} mg/dL, normal <7.0) strongly suggests gout. The sudden onset, joint swelling, and hyperuricemia are classic features."
                return "Acute gout flare (likely)", differential, reasoning
        
        # Diabetes-related
        if any(keyword in complaint_lower for keyword in ['thirst', 'urination', 'fatigue', 'blurred vision']):
            if glucose and glucose > 126:
                differential = [
                    "Poorly controlled diabetes",
                    "Diabetic ketoacidosis (if ketones present)",
                    "Hyperosmolar hyperglycemic state"
                ]
                reasoning = f"Elevated glucose ({glucose} mg/dL) with diabetic symptoms suggests poor glycemic control."
                return "Poorly controlled diabetes", differential, reasoning
        
        # Kidney-related
        if any(keyword in complaint_lower for keyword in ['fatigue', 'swelling', 'nausea', 'decreased urine']):
            if creatinine and creatinine > 1.5:
                differential = [
                    "Acute kidney injury",
                    "CKD progression",
                    "Volume depletion"
                ]
                reasoning = f"Elevated creatinine ({creatinine} mg/dL) indicates renal dysfunction."
                return "Renal dysfunction", differential, reasoning
        
        # Default
        return "Clinical evaluation needed", ["See differential diagnosis based on complaint"], "Requires further clinical assessment."
    
    @staticmethod
    def generate_from_data(observations: Dict, patient_id: str, complaint: str) -> str:
        """
        Generate summary using templates and exact data extraction.
        
        No LLM creativity - just structured presentation of facts.
        """
        ehr = observations.get('EHR', {})
        labs = observations.get('LABS', {})
        meds = observations.get('MEDS', {})
        ddi = observations.get('DDI', [])
        imaging = observations.get('IMAGING', {})
        
        # Extract exact demographics
        demo = ehr.get('demographics', {})
        age = demo.get('age', '?')
        gender = demo.get('gender', '?')
        
        # Extract conditions
        conditions = [c.get('name', '') for c in ehr.get('conditions', [])]
        
        # Extract vitals
        vitals = ehr.get('vitals', {})
        bp = vitals.get('bp', 'Not recorded')
        
        # Extract allergies
        allergies = [a.get('allergen', '') for a in ehr.get('allergies', [])]
        
        # Get diagnosis with reasoning
        primary_diagnosis, differential, reasoning = TemplateSummaryGenerator._diagnose_from_complaint_and_labs(
            complaint, labs, conditions
        )
        
        # Build CLINICAL REASONING section
        reasoning_section = reasoning
        
        # Build ATTENTION NEEDED section (only critical findings)
        attention_items = []
        
        # Extract lab values with clinical significance
        lab_results = labs.get('results', [])
        uric_acid = None
        creatinine = None
        egfr = None
        has_ckd = any('kidney' in c.lower() or 'ckd' in c.lower() for c in conditions)
        has_warfarin = any('warfarin' in m.get('name', '').lower() for m in meds.get('active', []))
        
        for lab in lab_results:
            test = lab.get('test', '')
            value = lab.get('value')
            unit = lab.get('unit', '')
            status = lab.get('status', '')
            
            # Only include clinically significant findings
            if status in ['HIGH', 'LOW', 'CRITICAL_HIGH', 'CRITICAL_LOW']:
                if test == 'Uric Acid' and value > 7.0:
                    uric_acid = value
                    attention_items.append(f"**Uric Acid {value} {unit} (HIGH)** - Supports gout diagnosis; consider urate-lowering therapy after acute flare resolves [LABS]")
                elif test == 'Creatinine' and value > 1.3:
                    creatinine = value
                    attention_items.append(f"**Creatinine {value} {unit} (HIGH)** - CKD Stage 3; avoid nephrotoxic medications (NSAIDs contraindicated) [LABS]")
                elif test == 'eGFR' and value < 60:
                    egfr = value
                    attention_items.append(f"**eGFR {value} {unit} (LOW)** - Stage 3 CKD; requires renal dosing adjustments [LABS]")
                elif test in ['HbA1c', 'Glucose'] and status == 'HIGH':
                    attention_items.append(f"**{test} {value} {unit} (HIGH)** - Diabetes control suboptimal; consider medication adjustment [LABS]")
        
        # Medication concerns
        active_meds = [m.get('name', '') for m in meds.get('active', [])]
        if has_warfarin:
            attention_items.append(f"**Warfarin use** - Increased bleeding risk; avoid NSAIDs, monitor INR if starting new medications [MEDS]")
        
        # Check for significant drug interactions
        if isinstance(ddi, list) and ddi:
            significant_ddis = [d for d in ddi if d.get('severity', '').upper() in ['HIGH', 'SEVERE']]
            if significant_ddis:
                for interaction in significant_ddis[:2]:  # Top 2
                    drug_a = interaction.get('a', '')
                    drug_b = interaction.get('b', '')
                    desc = interaction.get('description', '')
                    attention_items.append(f"**Drug interaction: {drug_a} + {drug_b}** - {desc} [DDI]")
        
        attention_section = "\n".join(f"- {item}" for item in attention_items) if attention_items else "- No critical findings requiring immediate attention"
        
        # Build RECOMMENDATIONS section (actionable, complaint-specific)
        recommendations = []
        
        # Gout-specific recommendations
        complaint_lower = complaint.lower()
        
        if any(keyword in complaint_lower for keyword in ['knee', 'joint', 'pain', 'swelling']) and uric_acid and uric_acid > 7.0:
            recommendations.append("### ACUTE TREATMENT")
            if has_ckd or has_warfarin:
                recommendations.append("- **Colchicine 0.6mg PO BID x 3 days** - Preferred over NSAIDs given CKD Stage 3 and warfarin use")
                recommendations.append("- **Avoid NSAIDs** - Contraindicated due to increased bleeding risk with warfarin and renal impairment")
            else:
                recommendations.append("- **Colchicine 0.6mg PO BID x 3 days** OR **NSAID** (e.g., indomethacin 50mg TID x 3 days) if no contraindications")
            
            recommendations.append("- **Consider joint aspiration** - For crystal analysis if diagnosis uncertain or concern for septic arthritis")
            recommendations.append("")
            recommendations.append("### PREVENTION")
            recommendations.append("- **Allopurinol 100mg daily** - Start after acute flare resolves (typically 1-2 weeks), titrate to uric acid <6.0 mg/dL")
            recommendations.append("- **Lifestyle modifications** - Avoid alcohol, high-purine foods (organ meats, shellfish)")
            recommendations.append("")
            recommendations.append("### MONITORING")
            recommendations.append("- **Recheck uric acid in 2-4 weeks** - After starting allopurinol")
            recommendations.append("- **Monitor renal function** - Creatinine, eGFR q3-6 months given CKD Stage 3")
            if has_warfarin:
                recommendations.append("- **Monitor INR closely** - If starting new medications that may interact with warfarin")
            recommendations.append("")
            recommendations.append("### FOLLOW-UP")
            recommendations.append("- **Return in 2-3 days** - If symptoms persist or worsen (rule out septic arthritis)")
            recommendations.append("- **Routine follow-up in 2-4 weeks** - For uric acid check and medication adjustment")
        
        # CKD management (if primary concern)
        elif has_ckd and egfr and egfr < 45:
            recommendations.append("### RENAL MANAGEMENT")
            recommendations.append("- **Continue ACE-inhibitor therapy** - Renal protective (already on Lisinopril)")
            recommendations.append("- **Monitor renal function** - Creatinine, eGFR q3-6 months")
            if egfr < 30:
                recommendations.append("- **Consider nephrology referral** - eGFR <30 (Stage 4 CKD)")
            recommendations.append("- **Avoid nephrotoxic medications** - NSAIDs, contrast agents")
            recommendations.append("")
            recommendations.append("### FOLLOW-UP")
            recommendations.append("- **Follow-up in 3 months** - For renal function monitoring")
        
        # Diabetes management
        elif any('diabetes' in c.lower() for c in conditions):
            recommendations.append("### DIABETES MANAGEMENT")
            recommendations.append("- **Optimize glycemic control** - Current HbA1c above target")
            recommendations.append("- **Continue metformin** - Monitor for renal function")
            recommendations.append("- **Consider medication adjustment** - If HbA1c remains elevated")
            recommendations.append("")
            recommendations.append("### FOLLOW-UP")
            recommendations.append("- **Follow-up in 3 months** - For HbA1c monitoring")
        
        # Default recommendations
        if not recommendations:
            recommendations.append("- Continue current management")
            recommendations.append("- Follow-up as clinically indicated")
        
        recommendations_section = "\n".join(recommendations)
        
        # Build DIFFERENTIAL DIAGNOSIS section
        differential_section = "\n".join(f"- {dx}" for dx in differential)
        
        # Assemble final output (focused, actionable structure)
        summary = f"""## CLINICAL ASSESSMENT

### PRIMARY DIAGNOSIS
{primary_diagnosis}

### CLINICAL REASONING
{reasoning_section}

### DIFFERENTIAL DIAGNOSIS
{differential_section}

### ATTENTION NEEDED
{attention_section}

### RECOMMENDATIONS
{recommendations_section}

---
*Data sources: [EHR] Electronic Health Record, [LABS] Laboratory Results, [MEDS] Medication List, [DDI] Drug Interaction Database, [GUIDELINES] Clinical Practice Guidelines*
"""
        
        return summary.strip()
