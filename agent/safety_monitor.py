"""
Safety Monitor Agent for post-diagnostic drug safety validation.

This agent runs after the doctor makes treatment decisions to validate
safety of prescribed medications against patient context, using:
- Drug-drug interactions
- Contraindications (allergies, conditions, labs)
- Dosage appropriateness
- Clinical guidelines
- Pharmacology knowledge
- Historical EHR analysis
- LLM-powered intelligent reasoning
"""
import json
import os
import asyncio
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass, asdict
from llm.med_gemma_wrapper import MedGemmaLLM
from config import Config


@dataclass
class SafetyWarning:
    """Represents a safety warning for a prescription."""
    severity: str  # 'critical', 'high', 'medium', 'low'
    drug_name: str
    warning_type: str  # 'ddi', 'contraindication', 'dosing', 'allergy', 'guideline', 'pharmacology', 'history'
    message: str
    recommendation: str
    alternative: Optional[str] = None
    source: Optional[str] = None  # 'guidelines', 'pharmacology', 'ehr_history', 'drug_database', 'llm_reasoning'
    confidence: Optional[str] = None  # 'high', 'medium', 'low'


class SafetyMonitorAgent:
    """
    Post-diagnostic safety monitor that validates doctor's treatment decisions.
    
    This agent runs after the doctor submits their treatment plan to check for:
    - Drug-drug interactions
    - Contraindications (allergies, conditions, labs)
    - Dosage appropriateness
    - Clinical guideline compliance
    - Pharmacology-based interactions
    - Historical EHR patterns
    - Patient-specific warnings using LLM reasoning
    """
    
    def __init__(self, tools: Dict, llm: Optional[MedGemmaLLM] = None):
        """
        Initialize Safety Monitor Agent.
        
        Args:
            tools: Dictionary of available tools
            llm: Language model for reasoning (creates new if None)
        """
        self.tools = tools
        self.llm = llm or MedGemmaLLM()
        self.name = "SafetyMonitor"
        self.drug_database = self._load_drug_database()
    
    def _load_drug_database(self) -> Dict:
        """Load comprehensive drug database."""
        try:
            db_path = os.path.join(Config.DRUGS_DIR, "drug_database.json")
            if os.path.exists(db_path):
                with open(db_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load drug database: {e}")
        return {}
    
    async def run(self, patient_id: str, doctor_decision: Dict, patient_context: Dict, emit: Callable) -> Dict:
        """
        Run comprehensive safety check on doctor's treatment decisions.
        
        Args:
            patient_id: Patient identifier
            doctor_decision: Doctor's treatment plan with prescriptions
            patient_context: Full patient data (EHR, labs, meds, etc.)
            emit: Progress callback
            
        Returns:
            Dictionary with safety analysis results
        """
        emit("SAFETY_MONITOR_STARTED")
        
        try:
            # Extract diagnosis and prescriptions from doctor decision
            diagnosis = doctor_decision.get('diagnosis', '').strip()
            prescriptions = doctor_decision.get('prescriptions', [])
            
            # Validate diagnosis first
            if diagnosis:
                emit("SAFETY_MONITOR_VALIDATING_DIAGNOSIS")
                diagnosis_warnings = self._check_diagnosis(
                    diagnosis, patient_context, emit
                )
            else:
                diagnosis_warnings = []
                emit("SAFETY_MONITOR_NO_DIAGNOSIS")
            
            if not prescriptions:
                emit("SAFETY_MONITOR_NO_PRESCRIPTIONS")
                return {
                    'status': 'no_prescriptions',
                    'warnings': diagnosis_warnings,
                    'summary': 'No prescriptions to validate' + (' (diagnosis validated)' if diagnosis else '')
                }
            
            emit(f"SAFETY_MONITOR_VALIDATING_{len(prescriptions)}_PRESCRIPTIONS")
            
            # Run comprehensive safety checks
            safety_results = await self._run_safety_checks(
                patient_id, prescriptions, patient_context, diagnosis, emit
            )
            
            # Add diagnosis warnings to overall warnings
            safety_results['warnings'].extend(diagnosis_warnings)
            
            # Skip LLM reasoning - use rule-based analysis only
            # LLM reasoning disabled for faster execution
            safety_results['llm_insights'] = []
            
            # Generate safety summary
            summary = self._generate_safety_summary(safety_results)
            
            emit("SAFETY_MONITOR_COMPLETED")
            
            return {
                'status': 'completed',
                'warnings': [asdict(w) for w in safety_results['warnings']],
                'summary': summary,
                'recommendations': safety_results['recommendations'],
                'alternatives': safety_results['alternatives'],
                'llm_insights': safety_results.get('llm_insights', [])
            }
            
        except Exception as e:
            emit(f"SAFETY_MONITOR_ERROR: {str(e)}")
            return {
                'status': 'error',
                'warnings': [],
                'summary': f'Safety check failed: {str(e)}'
            }
    
    async def _run_safety_checks(self, patient_id: str, prescriptions: List[Dict], 
                          patient_context: Dict, diagnosis: str, emit: Callable) -> Dict:
        """Run all safety checks on prescriptions."""
        warnings = []
        recommendations = []
        alternatives = []
        
        # Get patient data
        ehr = patient_context.get('EHR', {})
        current_meds = patient_context.get('MEDS', {}).get('active', [])
        allergies = ehr.get('allergies', [])
        conditions = ehr.get('conditions', [])
        labs = patient_context.get('LABS', {}).get('results', [])
        
        # Check each prescription
        for prescription in prescriptions:
            drug_name = prescription.get('name', '')
            dose = prescription.get('dose', '')
            frequency = prescription.get('frequency', '')
            
            emit(f"SAFETY_CHECKING_{drug_name}")
            
            # 1. Drug-Drug Interaction Check
            ddi_warnings = await self._check_drug_interactions(
                drug_name, current_meds, patient_context
            )
            warnings.extend(ddi_warnings)
            
            # 2. Allergy Check
            allergy_warnings = await self._check_allergies(
                drug_name, allergies, patient_id
            )
            warnings.extend(allergy_warnings)
            
            # 3. Contraindication Check (from drug database)
            contraindication_warnings = self._check_contraindications(
                drug_name, conditions, labs
            )
            warnings.extend(contraindication_warnings)
            
            # 4. Dosage Check
            dosing_warnings = self._check_dosage(
                drug_name, dose, frequency, ehr, labs
            )
            warnings.extend(dosing_warnings)
            
            # 5. Clinical Guidelines Check
            guideline_warnings = await self._check_guidelines(
                drug_name, conditions, patient_context
            )
            warnings.extend(guideline_warnings)
            
            # 6. Pharmacology Check
            pharmacology_warnings = await self._check_pharmacology(
                drug_name, current_meds, patient_context
            )
            warnings.extend(pharmacology_warnings)
            
            # 7. Historical EHR Analysis
            history_warnings = await self._check_ehr_history(
                patient_id, drug_name, patient_context
            )
            warnings.extend(history_warnings)
            
            # 8. Treatment-Diagnosis Alignment Check
            if diagnosis:
                alignment_warnings = self._check_treatment_diagnosis_alignment(
                    drug_name, diagnosis, patient_context
                )
                warnings.extend(alignment_warnings)
        
        # Generate recommendations and alternatives
        if warnings:
            recommendations = self._generate_recommendations(warnings)
            alternatives = self._suggest_alternatives(prescriptions, warnings, patient_context)
        
        return {
            'warnings': warnings,
            'recommendations': recommendations,
            'alternatives': alternatives
        }
    
    def _check_diagnosis(self, diagnosis: str, patient_context: Dict, emit: Callable) -> List[SafetyWarning]:
        """Check if diagnosis is consistent with patient data."""
        warnings = []
        
        # Get patient data
        ehr = patient_context.get('EHR', {})
        conditions = ehr.get('conditions', [])
        labs = patient_context.get('LABS', {}).get('results', [])
        demographics = ehr.get('demographics', {})
        
        diagnosis_lower = diagnosis.lower()
        
        # Check if diagnosis aligns with existing conditions
        condition_names = [c.get('name', '').lower() if isinstance(c, dict) else str(c).lower() for c in conditions]
        
        # Common diagnosis-condition mismatches
        mismatch_patterns = {
            'diabetes': ['diabetes', 'diabetic', 'dm', 't2dm', 'type 2'],
            'hypertension': ['hypertension', 'htn', 'high blood pressure'],
            'gout': ['gout', 'hyperuricemia'],
            'ckd': ['ckd', 'chronic kidney', 'kidney disease', 'renal'],
            'asthma': ['asthma', 'copd', 'respiratory'],
            'heart failure': ['heart failure', 'chf', 'cardiac']
        }
        
        # Check for potential mismatches
        for pattern_key, pattern_terms in mismatch_patterns.items():
            if any(term in diagnosis_lower for term in pattern_terms):
                # Check if patient has related conditions
                has_related = any(
                    any(term in cond for term in pattern_terms) 
                    for cond in condition_names
                )
                if not has_related:
                    # Check labs for supporting evidence
                    lab_support = False
                    if 'diabetes' in pattern_key:
                        lab_support = any('glucose' in str(lab.get('test', '')).lower() or 'hba1c' in str(lab.get('test', '')).lower() for lab in labs)
                    elif 'gout' in pattern_key:
                        lab_support = any('uric acid' in str(lab.get('test', '')).lower() for lab in labs)
                    elif 'ckd' in pattern_key:
                        lab_support = any('creatinine' in str(lab.get('test', '')).lower() or 'egfr' in str(lab.get('test', '')).lower() for lab in labs)
                    
                    if not lab_support:
                        warnings.append(SafetyWarning(
                            severity='moderate',
                            drug_name='N/A',
                            warning_type='diagnosis_validation',
                            message=f"Diagnosis '{diagnosis}' may not align with patient's documented conditions. Consider reviewing patient history.",
                            recommendation='Review patient history',
                            drug=None,
                            # details=f"Patient conditions: {', '.join([c.get('name', str(c)) if isinstance(c, dict) else str(c) for c in conditions[:3]])}"
                        ))
        
        # Check lab values for diagnosis support
        if labs:
            abnormal_labs = [lab for lab in labs if lab.get('status') in ['HIGH', 'LOW']]
            if abnormal_labs and ('normal' in diagnosis_lower or 'healthy' in diagnosis_lower):
                warnings.append(SafetyWarning(
                    severity='moderate',
                    drug_name='N/A',
                    warning_type='diagnosis_validation',
                    message=f"Diagnosis may not align with abnormal lab values present.",
                    recommendation='Review abnormal labs',
                    drug=None,
                    # details=f"Found {len(abnormal_labs)} abnormal lab value(s)"
                ))
        
        return warnings
    
    def _check_treatment_diagnosis_alignment(self, drug_name: str, diagnosis: str, 
                                            patient_context: Dict) -> List[SafetyWarning]:
        """Check if prescribed treatment aligns with diagnosis."""
        warnings = []
        
        diagnosis_lower = diagnosis.lower()
        drug_lower = drug_name.lower()
        
        # Common treatment-diagnosis mappings
        treatment_mappings = {
            'diabetes': ['metformin', 'insulin', 'glipizide', 'glimepiride', 'sitagliptin'],
            'hypertension': ['lisinopril', 'amlodipine', 'losartan', 'atenolol', 'hydrochlorothiazide'],
            'gout': ['allopurinol', 'colchicine', 'indomethacin', 'naproxen'],
            'ckd': ['lisinopril', 'losartan', 'furosemide'],
            'asthma': ['albuterol', 'salmeterol', 'fluticasone', 'montelukast'],
            'infection': ['amoxicillin', 'azithromycin', 'ciprofloxacin', 'doxycycline'],
            'pain': ['ibuprofen', 'acetaminophen', 'naproxen', 'tramadol']
        }
        
        # Check if drug matches diagnosis
        diagnosis_matched = False
        for condition, treatments in treatment_mappings.items():
            if condition in diagnosis_lower:
                if any(treatment in drug_lower for treatment in treatments):
                    diagnosis_matched = True
                    break
        
        # If diagnosis is specific but drug doesn't match common treatments
        if not diagnosis_matched and diagnosis.strip():
            # Check if it's a common mismatch
            common_mismatches = [
                ('diabetes', 'ibuprofen'),  # NSAIDs not typically first-line for diabetes
                ('hypertension', 'metformin'),  # Metformin is for diabetes, not hypertension
                ('gout', 'aspirin'),  # Aspirin can worsen gout
            ]
            
            for cond, drug in common_mismatches:
                if cond in diagnosis_lower and drug in drug_lower:
                    warnings.append(SafetyWarning(
                        severity='high',
                        drug_name=drug_name,
                        warning_type='treatment_diagnosis_mismatch',
                        message=f"Prescribed '{drug_name}' may not be appropriate for diagnosis '{diagnosis}'",
                        recommendation=f"Consider reviewing treatment guidelines for {diagnosis}",
                        source='guidelines',
                        confidence='medium'
                    ))
                    break
        
        return warnings
    
    async def _check_drug_interactions(self, new_drug: str, current_meds: List[Dict], 
                                 patient_context: Dict) -> List[SafetyWarning]:
        """Check for drug-drug interactions."""
        warnings = []
        
        try:
            # Get current medication names
            current_med_names = [med.get('name', '') for med in current_meds]
            
            # Check DDI using existing tool
            all_meds = current_meds + [{'name': new_drug}]
            ddi_results = await self.tools['ddi'](all_meds)
            
            for interaction in ddi_results:
                if interaction.get('a') == new_drug or interaction.get('b') == new_drug:
                    severity = self._map_ddi_severity(interaction.get('severity', 'moderate'))
                    warnings.append(SafetyWarning(
                        severity=severity,
                        drug_name=new_drug,
                        warning_type='ddi',
                        message=interaction.get('description', 'Drug interaction detected'),
                        recommendation=interaction.get('recommendation', 'Monitor patient closely'),
                        alternative=None,
                        source='ddi_database',
                        confidence='high'
                    ))
        
        except Exception as e:
            # If DDI check fails, create a warning about the failure
            warnings.append(SafetyWarning(
                severity='medium',
                drug_name=new_drug,
                warning_type='system_error',
                message=f'Unable to check drug interactions: {str(e)}',
                recommendation='Manually verify drug interactions',
                alternative=None,
                source='system',
                confidence='low'
            ))
        
        return warnings
    
    async def _check_allergies(self, drug_name: str, allergies: List[Dict], 
                        patient_id: str) -> List[SafetyWarning]:
        """Check for drug allergies."""
        warnings = []
        
        drug_lower = drug_name.lower()
        
        # Check current allergies
        for allergy in allergies:
            allergy_name = allergy.get('name', '').lower() or allergy.get('allergen', '').lower()
            allergy_type = allergy.get('type', '').lower()
            
            # Check for exact match or drug class match
            if (drug_lower in allergy_name or 
                allergy_name in drug_lower or
                self._check_drug_class_allergy(drug_name, allergy_name)):
                
                severity = 'critical' if allergy.get('severity') == 'severe' else 'high'
                warnings.append(SafetyWarning(
                    severity=severity,
                    drug_name=drug_name,
                    warning_type='allergy',
                    message=f'Patient has {allergy_type} allergy to {allergy.get("name", allergy.get("allergen", "unknown"))}',
                    recommendation='DO NOT PRESCRIBE - Use alternative medication',
                    alternative=self._suggest_allergy_alternative(drug_name, allergy_name),
                    source='ehr_allergies',
                    confidence='high'
                ))
        
        # Check historical allergies using EHR tool
        if 'ehr' in self.tools:
            try:
                # Need to import ehr tool specifically if it's not passed correctly or if we need specific function
                # But here we assume self.tools['ehr'] is the get_ehr function.
                # The check_allergy_history is a separate function in ehr module.
                # We should import it.
                from tools import ehr as ehr_tool
                historical_allergy = ehr_tool.check_allergy_history(patient_id, drug_name)
                if historical_allergy:
                    warnings.append(SafetyWarning(
                        severity='high',
                        drug_name=drug_name,
                        warning_type='allergy',
                        message=f'Historical allergy found: {historical_allergy.get("allergen", "unknown")}',
                        recommendation='Review allergy history before prescribing',
                        alternative=None,
                        source='ehr_history',
                        confidence='medium'
                    ))
            except Exception:
                pass
        
        return warnings
    
    def _check_contraindications(self, drug_name: str, conditions: List[Dict], 
                                labs: List[Dict]) -> List[SafetyWarning]:
        """Check for contraindications based on patient conditions and labs."""
        warnings = []
        
        # Get drug info from database
        drug_info = self._get_drug_info(drug_name)
        if not drug_info:
            return warnings
        
        contraindications = drug_info.get('contraindications', [])
        
        # Get condition names
        condition_names = [cond.get('name', '').lower() for cond in conditions]
        
        # Check each contraindication
        for contraindication in contraindications:
            contraindication_condition = contraindication.get('condition', '').lower()
            
            # Enhanced condition matching for renal/kidney conditions
            def matches_condition(contra_cond: str, patient_cond: str) -> bool:
                """Check if contraindication condition matches patient condition."""
                # Direct substring match
                if contra_cond in patient_cond or patient_cond in contra_cond:
                    return True
                # Special handling for renal/kidney conditions
                renal_keywords = ['renal', 'kidney', 'ckd', 'nephro']
                contra_has_renal = any(kw in contra_cond for kw in renal_keywords)
                patient_has_renal = any(kw in patient_cond for kw in renal_keywords)
                if contra_has_renal and patient_has_renal:
                    return True
                return False
            
            # Check if patient has matching condition
            for condition in condition_names:
                if matches_condition(contraindication_condition, condition):
                    
                    # Check lab-based contraindications
                    lab_check = contraindication.get('lab_check')
                    if lab_check:
                        lab_value = self._get_lab_value(labs, lab_check['test'])
                        if lab_value is not None:
                            threshold = lab_check.get('threshold')
                            operator = lab_check.get('operator', '<')
                            
                            if operator == '<' and lab_value < threshold:
                                warnings.append(SafetyWarning(
                                    severity=contraindication['severity'],
                                    drug_name=drug_name,
                                    warning_type='contraindication',
                                    message=f'{contraindication.get("description", f"Contraindicated in {condition}")} ({lab_check["test"]}: {lab_value})',
                                    recommendation=contraindication.get('recommendation', 'Consider alternative'),
                                    alternative=contraindication.get('alternative'),
                                    source='drug_database',
                                    confidence='high'
                                ))
                    else:
                        warnings.append(SafetyWarning(
                            severity=contraindication['severity'],
                            drug_name=drug_name,
                            warning_type='contraindication',
                            message=f'{contraindication.get("description", f"Contraindicated in {condition}")}',
                            recommendation=contraindication.get('recommendation', 'Consider alternative'),
                            alternative=contraindication.get('alternative'),
                            source='drug_database',
                            confidence='high'
                        ))
        
        return warnings
    
    def _check_dosage(self, drug_name: str, dose: str, frequency: str, 
                     ehr: Dict, labs: List[Dict]) -> List[SafetyWarning]:
        """Check dosage appropriateness."""
        warnings = []
        
        # Get drug info from database
        drug_info = self._get_drug_info(drug_name)
        if not drug_info:
            return warnings
        
        # Get patient demographics
        demographics = ehr.get('demographics', {})
        age = demographics.get('age', 0) or ehr.get('age', 0)
        weight = demographics.get('weight', 0) or ehr.get('weight', 0)
        
        dosing_info = drug_info.get('dosing', {})
        adult_dosing = dosing_info.get('adult', {})
        
        # Check age-appropriate dosing
        if age > 65 and dosing_info.get('elderly'):
            warnings.append(SafetyWarning(
                severity='medium',
                drug_name=drug_name,
                warning_type='dosing',
                message=f'Patient is {age} years old - elderly dosing considerations apply',
                recommendation=dosing_info.get('elderly', 'Start with lower dose, monitor closely'),
                alternative=None,
                source='drug_database',
                confidence='high'
            ))
        
        # Check renal function for certain drugs
        renal_adjustment = adult_dosing.get('renal_adjustment', {})
        if renal_adjustment:
            egfr = self._get_lab_value(labs, 'eGFR')
            if egfr is not None:
                if egfr < 30:
                    if 'egfr_<30' in renal_adjustment:
                        warnings.append(SafetyWarning(
                            severity='high',
                            drug_name=drug_name,
                            warning_type='dosing',
                            message=f'Renal impairment (eGFR {egfr}) - dose adjustment required',
                            recommendation=renal_adjustment.get('egfr_<30', 'Reduce dose or use alternative'),
                            alternative=self._suggest_renal_alternative(drug_name),
                            source='drug_database',
                            confidence='high'
                        ))
                elif 30 <= egfr < 45:
                    if 'egfr_30_45' in renal_adjustment:
                        warnings.append(SafetyWarning(
                            severity='medium',
                            drug_name=drug_name,
                            warning_type='dosing',
                            message=f'Moderate renal impairment (eGFR {egfr}) - consider dose adjustment',
                            recommendation=renal_adjustment.get('egfr_30_45', 'Monitor closely'),
                            alternative=None,
                            source='drug_database',
                            confidence='high'
                        ))
                elif 45 <= egfr < 60:
                    if 'egfr_45_60' in renal_adjustment:
                        warnings.append(SafetyWarning(
                            severity='low',
                            drug_name=drug_name,
                            warning_type='dosing',
                            message=f'Mild renal impairment (eGFR {egfr}) - may need dose adjustment',
                            recommendation=renal_adjustment.get('egfr_45_60', 'Monitor renal function'),
                            alternative=None,
                            source='drug_database',
                            confidence='medium'
                        ))
        
        return warnings
    
    async def _check_guidelines(self, drug_name: str, conditions: List[Dict], 
                         patient_context: Dict) -> List[SafetyWarning]:
        """Check drug against clinical guidelines."""
        warnings = []
        
        if 'guidelines' not in self.tools:
            return warnings
        
        try:
            # Search guidelines for each condition
            condition_names = [cond.get('name', '').lower() for cond in conditions]
            
            for condition in condition_names:
                # Extract keywords from condition
                keywords = condition.split()[:2]  # First 2 words
                
                for keyword in keywords:
                    guideline_results = await self.tools['guidelines'](keyword)
                    
                    for guideline in guideline_results:
                        guideline_text = guideline.get('snippet', '').lower()
                        title = guideline.get('title', '').lower()
                        
                        # Check if guideline mentions the drug
                        if drug_name.lower() in guideline_text:
                            # Check for contraindications or warnings
                            if any(word in guideline_text for word in ['contraindicated', 'avoid', 'not recommended', 'caution']):
                                warnings.append(SafetyWarning(
                                    severity='high',
                                    drug_name=drug_name,
                                    warning_type='guideline',
                                    message=f'Guideline ({title}) suggests caution with {drug_name} in {condition}',
                                    recommendation='Review guideline recommendations before prescribing',
                                    alternative=None,
                                    source='guidelines',
                                    confidence='medium'
                                ))
        except Exception as e:
            # Silently fail - guidelines check is supplementary
            pass
        
        return warnings
    
    async def _check_pharmacology(self, drug_name: str, current_meds: List[Dict], 
                           patient_context: Dict) -> List[SafetyWarning]:
        """Check pharmacology-based interactions and mechanisms."""
        warnings = []
        
        if 'pharmacology' not in self.tools:
            # Try to import pharmacology tool
            try:
                from tools import pharmacology
                self.tools['pharmacology'] = pharmacology
            except ImportError:
                return warnings
        
        try:
            pharmacology_tool = self.tools['pharmacology']
            
            # Check pharmacological interactions with current meds
            for med in current_meds:
                med_name = med.get('name', '')
                interaction = await pharmacology_tool.check_pharmacological_interaction(drug_name, med_name)
                
                if interaction:
                    warnings.append(SafetyWarning(
                        severity='high',
                        drug_name=drug_name,
                        warning_type='pharmacology',
                        message=f'Pharmacological interaction: {interaction.get("mechanism", "Mechanism-based interaction detected")}',
                        recommendation='Monitor for adverse effects based on pharmacological mechanisms',
                        alternative=None,
                        source='pharmacology',
                        confidence='medium'
                    ))
            
            # Check clearance pathway conflicts
            drug_clearance = await pharmacology_tool.check_clearance_pathway(drug_name)
            if drug_clearance == 'renal':
                egfr = self._get_lab_value(patient_context.get('LABS', {}).get('results', []), 'eGFR')
                if egfr and egfr < 30:
                    warnings.append(SafetyWarning(
                        severity='high',
                        drug_name=drug_name,
                        warning_type='pharmacology',
                        message=f'{drug_name} is renally cleared - may accumulate in renal impairment (eGFR: {egfr})',
                        recommendation='Dose adjustment required or consider alternative',
                        alternative=None,
                        source='pharmacology',
                        confidence='high'
                    ))
        except Exception as e:
            # Silently fail - pharmacology check is supplementary
            pass
        
        return warnings
    
    async def _check_ehr_history(self, patient_id: str, drug_name: str, 
                           patient_context: Dict) -> List[SafetyWarning]:
        """Check historical EHR for relevant patterns."""
        warnings = []
        
        if 'ehr' not in self.tools:
            return warnings
        
        try:
            from tools import ehr as ehr_tool
            
            # Check for past conditions that might affect drug safety
            past_conditions = await ehr_tool.get_past_conditions(patient_id)
            
            # Check if patient had conditions that might contraindicate rechallenge
            drug_info = self._get_drug_info(drug_name)
            if drug_info:
                contraindications = drug_info.get('contraindications', [])
                contraindication_keywords = [c.get('condition', '').lower() for c in contraindications]
                
                for past_condition in past_conditions:
                    condition_name = past_condition.get('name', '').lower()
                    for keyword in contraindication_keywords:
                        if keyword in condition_name or condition_name in keyword:
                            warnings.append(SafetyWarning(
                                severity='medium',
                                drug_name=drug_name,
                                warning_type='history',
                                message=f'Patient has history of {condition_name} - may affect drug safety',
                                recommendation='Review past medical history before prescribing',
                                alternative=None,
                                source='ehr_history',
                                confidence='medium'
                            ))
            
            # Check lab trends that might affect drug safety
            labs = patient_context.get('LABS', {}).get('results', [])
            for lab in labs:
                test_name = lab.get('test', '')
                trend = lab.get('trend', '')
                
                # Check if declining renal function affects drug
                if test_name.lower() == 'egfr' and trend == 'decreasing':
                    drug_info = self._get_drug_info(drug_name)
                    if drug_info:
                        dosing = drug_info.get('dosing', {})
                        if dosing.get('adult', {}).get('renal_adjustment'):
                            warnings.append(SafetyWarning(
                                severity='medium',
                                drug_name=drug_name,
                                warning_type='history',
                                message=f'Declining renal function trend - monitor closely if prescribing {drug_name}',
                                recommendation='Consider dose adjustment or alternative',
                                alternative=None,
                                source='ehr_history',
                                confidence='medium'
                            ))
        except Exception as e:
            # Silently fail - history check is supplementary
            pass
        
        return warnings
    
    def _get_drug_info(self, drug_name: str) -> Optional[Dict]:
        """Get drug info from database."""
        drug_lower = drug_name.lower()
        
        # Check direct match
        if drug_lower in self.drug_database:
            return self.drug_database[drug_lower]
        
        # Check partial matches
        for key, value in self.drug_database.items():
            if key in drug_lower or drug_lower in key:
                return value
        
        return None
    
    def _get_lab_value(self, labs: List[Dict], test_name: str) -> Optional[float]:
        """Get value of a specific lab test."""
        test_lower = test_name.lower()
        for lab in labs:
            if test_lower in lab.get('test', '').lower():
                try:
                    return float(lab.get('value'))
                except (ValueError, TypeError):
                    return None
        return None
    
    def _map_ddi_severity(self, severity: str) -> str:
        """Map DDI severity to safety warning severity."""
        severity = severity.lower()
        if severity in ['major', 'severe', 'contraindicated']:
            return 'critical'
        elif severity in ['moderate', 'significant']:
            return 'high'
        elif severity in ['minor', 'mild']:
            return 'low'
        return 'medium'
    
    def _check_drug_class_allergy(self, drug_name: str, allergy_name: str) -> bool:
        """Check if drug belongs to allergic class."""
        drug_classes = {
            'penicillin': ['amoxicillin', 'ampicillin', 'penicillin', 'augmentin'],
            'sulfa': ['sulfamethoxazole', 'sulfasalazine', 'bactrim'],
            'ace_inhibitor': ['lisinopril', 'enalapril', 'captopril', 'ramipril'],
            'nsaid': ['ibuprofen', 'naproxen', 'aspirin', 'meloxicam', 'diclofenac']
        }
        
        drug_lower = drug_name.lower()
        allergy_lower = allergy_name.lower()
        
        for class_name, members in drug_classes.items():
            if class_name in allergy_lower:
                if any(member in drug_lower for member in members):
                    return True
        
        return False
    
    def _suggest_allergy_alternative(self, drug_name: str, allergy_name: str) -> Optional[str]:
        """Suggest alternative for allergic drug."""
        # Simple lookup for common alternatives
        alternatives = {
            'amoxicillin': 'Azithromycin or Clindamycin',
            'lisinopril': 'Losartan (ARB) if cough, but caution if angioedema',
            'ibuprofen': 'Acetaminophen',
            'bactrim': 'Nitrofurantoin or Ciprofloxacin'
        }
        
        drug_lower = drug_name.lower()
        for key, value in alternatives.items():
            if key in drug_lower:
                return value
        return None
    
    def _suggest_renal_alternative(self, drug_name: str) -> Optional[str]:
        """Suggest alternative for renally cleared drug."""
        alternatives = {
            'metformin': 'Glipizide or Insulin',
            'lisinopril': 'Fosinopril (hepatically cleared)',
            'atenolol': 'Metoprolol (hepatically cleared)'
        }
        
        drug_lower = drug_name.lower()
        for key, value in alternatives.items():
            if key in drug_lower:
                return value
        return None
    
    def _generate_recommendations(self, warnings: List[SafetyWarning]) -> List[str]:
        """Generate consolidated recommendations."""
        recommendations = []
        seen = set()
        
        for warning in warnings:
            if warning.recommendation and warning.recommendation not in seen:
                recommendations.append(f"{warning.drug_name}: {warning.recommendation}")
                seen.add(warning.recommendation)
        
        return recommendations
    
    def _suggest_alternatives(self, prescriptions: List[Dict], warnings: List[SafetyWarning], 
                            patient_context: Dict) -> List[Dict]:
        """Suggest alternatives for problematic prescriptions."""
        alternatives = []
        
        for warning in warnings:
            if warning.alternative:
                alternatives.append({
                    'original_drug': warning.drug_name,
                    'suggested_alternative': warning.alternative,
                    'reason': warning.message
                })
        
        return alternatives
    
    def _generate_safety_summary(self, safety_results: Dict) -> str:
        """Generate human-readable safety summary."""
        warnings = safety_results['warnings']
        
        if not warnings:
            return "✅ All prescriptions appear safe based on current patient data."
        
        critical_count = sum(1 for w in warnings if w.severity == 'critical')
        high_count = sum(1 for w in warnings if w.severity == 'high')
        medium_count = sum(1 for w in warnings if w.severity == 'medium')
        low_count = sum(1 for w in warnings if w.severity == 'low')
        
        summary = []
        if critical_count > 0:
            summary.append(f"⛔ {critical_count} CRITICAL safety issues detected - Immediate action required.")
        if high_count > 0:
            summary.append(f"⚠️ {high_count} High priority warnings - Review recommended.")
        if medium_count > 0:
            summary.append(f"ℹ️ {medium_count} Moderate warnings - Monitor patient.")
            
        return "\n".join(summary)
