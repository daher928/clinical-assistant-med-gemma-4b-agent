"""
Template-based clinical summary generation.

Strategy: Pre-build 90% of the output, let LLM fill in ONLY specific blanks.
This eliminates hallucination by removing creative freedom.
"""
from typing import Dict


class TemplateSummaryGenerator:
    """
    Generate clinical summaries using strict templates.
    
    The LLM does NOT write freely - it only completes specific tasks
    like identifying the primary concern or suggesting next steps.
    """
    
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
        condition_str = ', '.join(conditions[:3]) if conditions else 'no documented conditions'
        
        # Extract vitals
        vitals = ehr.get('vitals', {})
        bp = vitals.get('bp', 'not recorded')
        hr = vitals.get('hr', '?')
        temp = vitals.get('temp', '?')
        
        # Extract allergies
        allergies = [a.get('allergen', '') for a in ehr.get('allergies', [])]
        allergy_str = ', '.join(allergies) if allergies else 'none documented'
        
        # Build ONE-LINE summary
        primary_condition = conditions[0] if conditions else 'multiple conditions'
        one_liner = f"{age}yo {gender} with {primary_condition} presenting with {complaint}"
        
        # Build SNAPSHOT section
        snapshot = f"""- Age/Gender: {age}yo {gender}
- Chief Complaint: {complaint}
- Active Conditions: {condition_str}
- Allergies: {allergy_str}
- BP: {bp}, HR: {hr}, Temp: {temp}°F"""
        
        # Build ATTENTION NEEDED section with clinical context
        attention_items = []
        
        # First, check for CRITICAL labs
        critical_labs = []
        high_priority_labs = []
        
        for lab in labs.get('results', []):
            test = lab.get('test')
            value = lab.get('value')
            unit = lab.get('unit')
            status = lab.get('status')
            
            if status in ['CRITICAL_HIGH', 'CRITICAL_LOW']:
                critical_labs.append((test, value, unit, status))
            elif status in ['HIGH', 'LOW']:
                high_priority_labs.append((test, value, unit, status))
        
        # Add critical labs first with clinical context
        for test, value, unit, status in critical_labs:
            if test == 'eGFR':
                attention_items.append(f"- Severe kidney dysfunction: eGFR {value} {unit} (Stage 4 CKD) [LABS]")
            elif test == 'Hemoglobin':
                attention_items.append(f"- Severe anemia: Hemoglobin {value} {unit} (transfusion threshold) [LABS]")
            elif test == 'Potassium':
                attention_items.append(f"- Critical hyperkalemia: K+ {value} {unit} (arrhythmia risk) [LABS]")
            else:
                attention_items.append(f"- {test}: {value} {unit} ({status}) [LABS]")
        
        # Add high-priority labs
        for test, value, unit, status in high_priority_labs[:3]:  # Limit to top 3
            attention_items.append(f"- {test}: {value} {unit} ({status}) [LABS]")
        
        # Check for worsening trends (VERY important clinically)
        historical = labs.get('historical_data', {})
        trend_count = 0
        for lab in labs.get('results', []):
            if trend_count >= 2:  # Limit to 2 most important trends
                break
                
            test_name = lab['test']
            current = lab['value']
            hist_key = test_name.lower().replace(' ', '_') + '_6mo_ago'
            
            if hist_key in historical:
                past = historical[hist_key]
                if current != past:
                    # Determine if trend is worsening
                    is_worsening = False
                    if test_name == 'eGFR' and current < past:
                        is_worsening = True
                        change_pct = abs(round((current - past) / past * 100, 1))
                        attention_items.append(
                            f"- Declining kidney function: eGFR {past} → {current} ({change_pct}% decrease over 6mo) [LABS]"
                        )
                        trend_count += 1
                    elif test_name == 'Hemoglobin' and current < past:
                        is_worsening = True
                        attention_items.append(
                            f"- Worsening anemia: Hemoglobin {past} → {current} {lab['unit']} [LABS]"
                        )
                        trend_count += 1
                    elif test_name in ['Creatinine', 'BUN'] and current > past:
                        is_worsening = True
                        attention_items.append(
                            f"- Rising {test_name}: {past} → {current} {lab['unit']} [LABS]"
                        )
                        trend_count += 1
        
        attention_section = "\n".join(attention_items) if attention_items else "- All laboratory values within acceptable ranges"
        
        # Build MEDICATION CONCERNS section
        med_concerns = []
        
        # List medications
        active_meds = [m.get('name', '') for m in meds.get('active', [])]
        if active_meds:
            med_concerns.append(f"- Active medications: {', '.join(active_meds)} [MEDS]")
        
        # List interactions
        if isinstance(ddi, list) and ddi:
            for interaction in ddi[:3]:  # Top 3 interactions
                drug_a = interaction.get('a', '')
                drug_b = interaction.get('b', '')
                severity = interaction.get('severity', '')
                desc = interaction.get('description', '')
                med_concerns.append(f"- {drug_a} + {drug_b}: {severity} - {desc} [DDI]")
        else:
            med_concerns.append("- No significant drug-drug interactions detected [DDI]")
        
        med_section = "\n".join(med_concerns)
        
        # Build PLAN section with evidence-based recommendations
        plan_items = []
        plan_counter = 1
        
        # INTELLIGENT CLINICAL REASONING (no LLM needed)
        
        # Check for CKD progression
        has_ckd = any('kidney' in c.lower() or 'ckd' in c.lower() for c in conditions)
        egfr_value = None
        hgb_value = None
        k_value = None
        creat_value = None
        
        for lab in labs.get('results', []):
            if lab.get('test') == 'eGFR':
                egfr_value = lab.get('value')
            elif lab.get('test') == 'Hemoglobin':
                hgb_value = lab.get('value')
            elif lab.get('test') == 'Potassium':
                k_value = lab.get('value')
            elif lab.get('test') == 'Creatinine':
                creat_value = lab.get('value')
        
        # CKD-specific recommendations (evidence-based)
        if has_ckd and egfr_value:
            if egfr_value < 30:
                plan_items.append(f"{plan_counter}. URGENT: Nephrology referral for Stage 4 CKD (eGFR {egfr_value}) [GUIDELINES]")
                plan_counter += 1
            elif egfr_value < 45:
                plan_items.append(f"{plan_counter}. Nephrology referral for CKD management (eGFR {egfr_value}) [GUIDELINES]")
                plan_counter += 1
        
        # Anemia management (CKD-specific)
        if has_ckd and hgb_value:
            if hgb_value < 10:
                plan_items.append(f"{plan_counter}. Initiate ESA therapy for severe anemia (Hgb {hgb_value}) [GUIDELINES]")
                plan_counter += 1
            elif hgb_value < 11:
                plan_items.append(f"{plan_counter}. Consider ESA for anemia management (Hgb {hgb_value}) [GUIDELINES]")
                plan_counter += 1
        
        # Hyperkalemia management
        if k_value and k_value > 5.5:
            plan_items.append(f"{plan_counter}. Monitor potassium closely, consider dietary counseling (K+ {k_value}) [GUIDELINES]")
            plan_counter += 1
        
        # Blood pressure management (CKD-specific targets)
        if bp != 'not recorded':
            try:
                systolic = int(bp.split('/')[0])
                if systolic > 140:
                    target = "<130/80" if has_ckd else "<140/90"
                    plan_items.append(f"{plan_counter}. Optimize BP control (current {bp}, target {target}) [GUIDELINES]")
                    plan_counter += 1
            except:
                pass
        
        # Medication review for DDIs
        if isinstance(ddi, list) and len(ddi) > 0:
            high_severity = [d for d in ddi if d.get('severity', '').upper() in ['HIGH', 'SEVERE']]
            if high_severity:
                plan_items.append(f"{plan_counter}. Review medications for {len(high_severity)} high-severity interactions [DDI]")
                plan_counter += 1
        
        # Check for ACE/ARB in CKD (guideline-directed therapy)
        if has_ckd:
            active_meds = [m.get('name', '').lower() for m in meds.get('active', [])]
            has_ace_arb = any(
                med for med in active_meds 
                if 'lisinopril' in med or 'losartan' in med or 'enalapril' in med
            )
            if has_ace_arb and creat_value:
                plan_items.append(f"{plan_counter}. Continue ACE-inhibitor therapy, monitor renal function [GUIDELINES]")
                plan_counter += 1
        
        # Default follow-up timing based on acuity
        if not plan_items:
            plan_items.append("1. Continue current management")
            plan_items.append("2. Routine follow-up in 3 months")
        else:
            # Determine follow-up based on findings
            if egfr_value and egfr_value < 30:
                followup = "1-2 weeks"
            elif any('URGENT' in item for item in plan_items):
                followup = "1-2 weeks"
            elif len(plan_items) >= 3:
                followup = "2-4 weeks"
            else:
                followup = "4-8 weeks"
            
            plan_items.append(f"{plan_counter}. Follow-up in {followup} to reassess")
        
        plan_section = "\n".join(plan_items)
        
        # Assemble final output
        summary = f"""## ONE-LINE SUMMARY
{one_liner}

## PATIENT SNAPSHOT
{snapshot}

## ATTENTION NEEDED
{attention_section}

## MEDICATION CONCERNS
{med_section}

## PLAN
{plan_section}

---
*Data sources: [EHR] Electronic Health Record, [LABS] Laboratory Results, [MEDS] Medication List, [DDI] Drug Interaction Database, [GUIDELINES] Clinical Practice Guidelines*
"""
        
        return summary.strip()

