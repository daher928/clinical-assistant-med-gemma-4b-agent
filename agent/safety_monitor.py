"""
Safety Monitor Agent for post-diagnostic drug safety validation.

This agent runs after the doctor makes treatment decisions to validate
safety of prescribed medications against patient context.
"""
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from llm.med_gemma_wrapper import MedGemmaLLM


@dataclass
class SafetyWarning:
    """Represents a safety warning for a prescription."""
    severity: str  # 'critical', 'high', 'medium', 'low'
    drug_name: str
    warning_type: str  # 'ddi', 'contraindication', 'dosing', 'allergy', etc.
    message: str
    recommendation: str
    alternative: Optional[str] = None


class SafetyMonitorAgent:
    """
    Post-diagnostic safety monitor that validates doctor's treatment decisions.
    
    This agent runs after the doctor submits their treatment plan to check for:
    - Drug-drug interactions
    - Contraindications (allergies, conditions)
    - Dosage appropriateness
    - Patient-specific warnings
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
    
    def run(self, patient_id: str, doctor_decision: Dict, patient_context: Dict, emit: Callable) -> Dict:
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
            # Extract prescriptions from doctor decision
            prescriptions = doctor_decision.get('prescriptions', [])
            if not prescriptions:
                emit("SAFETY_MONITOR_NO_PRESCRIPTIONS")
                return {
                    'status': 'no_prescriptions',
                    'warnings': [],
                    'summary': 'No prescriptions to validate'
                }
            
            emit(f"SAFETY_MONITOR_VALIDATING_{len(prescriptions)}_PRESCRIPTIONS")
            
            # Run comprehensive safety checks
            safety_results = self._run_safety_checks(
                prescriptions, patient_context, emit
            )
            
            # Generate safety summary
            summary = self._generate_safety_summary(safety_results)
            
            emit("SAFETY_MONITOR_COMPLETED")
            
            return {
                'status': 'completed',
                'warnings': safety_results['warnings'],
                'summary': summary,
                'recommendations': safety_results['recommendations'],
                'alternatives': safety_results['alternatives']
            }
            
        except Exception as e:
            emit(f"SAFETY_MONITOR_ERROR: {str(e)}")
            return {
                'status': 'error',
                'warnings': [],
                'summary': f'Safety check failed: {str(e)}'
            }
    
    def _run_safety_checks(self, prescriptions: List[Dict], patient_context: Dict, emit: Callable) -> Dict:
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
            ddi_warnings = self._check_drug_interactions(
                drug_name, current_meds, patient_context
            )
            warnings.extend(ddi_warnings)
            
            # 2. Allergy Check
            allergy_warnings = self._check_allergies(
                drug_name, allergies
            )
            warnings.extend(allergy_warnings)
            
            # 3. Contraindication Check
            contraindication_warnings = self._check_contraindications(
                drug_name, conditions, labs
            )
            warnings.extend(contraindication_warnings)
            
            # 4. Dosage Check
            dosing_warnings = self._check_dosage(
                drug_name, dose, frequency, ehr, labs
            )
            warnings.extend(dosing_warnings)
        
        # Generate recommendations and alternatives
        if warnings:
            recommendations = self._generate_recommendations(warnings)
            alternatives = self._suggest_alternatives(prescriptions, warnings, patient_context)
        
        return {
            'warnings': warnings,
            'recommendations': recommendations,
            'alternatives': alternatives
        }
    
    def _check_drug_interactions(self, new_drug: str, current_meds: List[Dict], patient_context: Dict) -> List[SafetyWarning]:
        """Check for drug-drug interactions."""
        warnings = []
        
        try:
            # Get current medication names
            current_med_names = [med.get('name', '') for med in current_meds]
            
            # Check DDI using existing tool
            all_meds = current_meds + [{'name': new_drug}]
            ddi_results = self.tools['ddi'](all_meds)
            
            for interaction in ddi_results:
                if interaction.get('a') == new_drug or interaction.get('b') == new_drug:
                    severity = self._map_ddi_severity(interaction.get('severity', 'moderate'))
                    warnings.append(SafetyWarning(
                        severity=severity,
                        drug_name=new_drug,
                        warning_type='ddi',
                        message=interaction.get('description', 'Drug interaction detected'),
                        recommendation=interaction.get('recommendation', 'Monitor patient closely'),
                        alternative=None
                    ))
        
        except Exception as e:
            # If DDI check fails, create a warning about the failure
            warnings.append(SafetyWarning(
                severity='medium',
                drug_name=new_drug,
                warning_type='system_error',
                message=f'Unable to check drug interactions: {str(e)}',
                recommendation='Manually verify drug interactions',
                alternative=None
            ))
        
        return warnings
    
    def _check_allergies(self, drug_name: str, allergies: List[Dict]) -> List[SafetyWarning]:
        """Check for drug allergies."""
        warnings = []
        
        drug_lower = drug_name.lower()
        
        for allergy in allergies:
            allergy_name = allergy.get('name', '').lower()
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
                    message=f'Patient has {allergy_type} allergy to {allergy.get("name", "unknown")}',
                    recommendation='DO NOT PRESCRIBE - Use alternative medication',
                    alternative=self._suggest_allergy_alternative(drug_name, allergy_name)
                ))
        
        return warnings
    
    def _check_contraindications(self, drug_name: str, conditions: List[Dict], labs: List[Dict]) -> List[SafetyWarning]:
        """Check for contraindications based on patient conditions."""
        warnings = []
        
        # Get condition names
        condition_names = [cond.get('name', '').lower() for cond in conditions]
        
        # Check for common contraindications
        contraindications = self._get_drug_contraindications(drug_name)
        
        for contraindication in contraindications:
            for condition in condition_names:
                if contraindication['condition'].lower() in condition:
                    warnings.append(SafetyWarning(
                        severity=contraindication['severity'],
                        drug_name=drug_name,
                        warning_type='contraindication',
                        message=f'Contraindicated in {condition}',
                        recommendation=contraindication['recommendation'],
                        alternative=contraindication.get('alternative')
                    ))
        
        # Check lab-based contraindications
        lab_warnings = self._check_lab_contraindications(drug_name, labs)
        warnings.extend(lab_warnings)
        
        return warnings
    
    def _check_dosage(self, drug_name: str, dose: str, frequency: str, ehr: Dict, labs: List[Dict]) -> List[SafetyWarning]:
        """Check dosage appropriateness."""
        warnings = []
        
        # Get patient demographics
        age = ehr.get('age', 0)
        weight = ehr.get('weight', 0)
        
        # Check age-appropriate dosing
        if age > 65:
            warnings.append(SafetyWarning(
                severity='medium',
                drug_name=drug_name,
                warning_type='dosing',
                message=f'Patient is {age} years old - consider reduced dosing',
                recommendation='Start with lower dose, monitor closely',
                alternative=None
            ))
        
        # Check renal function for certain drugs
        if self._requires_renal_adjustment(drug_name):
            egfr = self._get_lab_value(labs, 'eGFR')
            if egfr and egfr < 30:
                warnings.append(SafetyWarning(
                    severity='high',
                    drug_name=drug_name,
                    warning_type='dosing',
                    message=f'Renal impairment (eGFR {egfr}) - dose adjustment required',
                    recommendation='Reduce dose by 50% or use alternative',
                    alternative=self._suggest_renal_alternative(drug_name)
                ))
        
        return warnings
    
    def _generate_safety_summary(self, safety_results: Dict) -> str:
        """Generate human-readable safety summary."""
        warnings = safety_results['warnings']
        
        if not warnings:
            return "✅ All prescriptions appear safe based on current patient data."
        
        critical_count = sum(1 for w in warnings if w.severity == 'critical')
        high_count = sum(1 for w in warnings if w.severity == 'high')
        medium_count = sum(1 for w in warnings if w.severity == 'medium')
        
        summary_parts = []
        
        if critical_count > 0:
            summary_parts.append(f"🚨 {critical_count} CRITICAL safety issue(s)")
        if high_count > 0:
            summary_parts.append(f"⚠️ {high_count} HIGH priority warning(s)")
        if medium_count > 0:
            summary_parts.append(f"ℹ️ {medium_count} medium priority note(s)")
        
        return " | ".join(summary_parts)
    
    def _generate_recommendations(self, warnings: List[SafetyWarning]) -> List[str]:
        """Generate actionable recommendations from warnings."""
        recommendations = []
        
        for warning in warnings:
            if warning.severity in ['critical', 'high']:
                recommendations.append(f"{warning.drug_name}: {warning.recommendation}")
        
        return recommendations
    
    def _suggest_alternatives(self, prescriptions: List[Dict], warnings: List[SafetyWarning], patient_context: Dict) -> List[Dict]:
        """Suggest alternative medications for problematic prescriptions."""
        alternatives = []
        
        for warning in warnings:
            if warning.alternative:
                alternatives.append({
                    'original_drug': warning.drug_name,
                    'alternative': warning.alternative,
                    'reason': warning.message,
                    'severity': warning.severity
                })
        
        return alternatives
    
    # Helper methods
    def _map_ddi_severity(self, ddi_severity: str) -> str:
        """Map DDI severity to safety warning severity."""
        mapping = {
            'major': 'critical',
            'moderate': 'high',
            'minor': 'medium',
            'none': 'low'
        }
        return mapping.get(ddi_severity, 'medium')
    
    def _check_drug_class_allergy(self, drug_name: str, allergy_name: str) -> bool:
        """Check if drug belongs to a class the patient is allergic to."""
        # This would need a drug class database - simplified for now
        drug_classes = {
            'penicillin': ['amoxicillin', 'ampicillin', 'penicillin'],
            'sulfa': ['sulfamethoxazole', 'sulfasalazine'],
            'ace_inhibitor': ['lisinopril', 'enalapril', 'captopril']
        }
        
        for drug_class, drugs in drug_classes.items():
            if drug_class in allergy_name.lower():
                return drug_name.lower() in [d.lower() for d in drugs]
        
        return False
    
    def _get_drug_contraindications(self, drug_name: str) -> List[Dict]:
        """Get contraindications for a specific drug."""
        # This would ideally come from a drug database
        contraindications = {
            'metformin': [
                {'condition': 'severe renal impairment', 'severity': 'critical', 'recommendation': 'Contraindicated if eGFR <30', 'alternative': 'Insulin therapy'}
            ],
            'lisinopril': [
                {'condition': 'pregnancy', 'severity': 'critical', 'recommendation': 'Contraindicated in pregnancy', 'alternative': 'Methyldopa or labetalol'}
            ]
        }
        
        return contraindications.get(drug_name.lower(), [])
    
    def _check_lab_contraindications(self, drug_name: str, labs: List[Dict]) -> List[SafetyWarning]:
        """Check lab-based contraindications."""
        warnings = []
        
        # Check eGFR for metformin
        if drug_name.lower() == 'metformin':
            egfr = self._get_lab_value(labs, 'eGFR')
            if egfr and egfr < 30:
                warnings.append(SafetyWarning(
                    severity='critical',
                    drug_name=drug_name,
                    warning_type='contraindication',
                    message=f'Metformin contraindicated with eGFR {egfr}',
                    recommendation='Use insulin therapy instead',
                    alternative='Insulin therapy'
                ))
        
        return warnings
    
    def _requires_renal_adjustment(self, drug_name: str) -> bool:
        """Check if drug requires renal dose adjustment."""
        renal_drugs = ['metformin', 'digoxin', 'gabapentin', 'pregabalin']
        return drug_name.lower() in renal_drugs
    
    def _get_lab_value(self, labs: List[Dict], test_name: str) -> Optional[float]:
        """Get specific lab value."""
        for lab in labs:
            if lab.get('test', '').lower() == test_name.lower():
                try:
                    return float(lab.get('value', 0))
                except (ValueError, TypeError):
                    return None
        return None
    
    def _suggest_allergy_alternative(self, drug_name: str, allergy_name: str) -> Optional[str]:
        """Suggest alternative for drug allergy."""
        alternatives = {
            'penicillin': 'Cephalexin or azithromycin',
            'sulfa': 'Alternative antibiotic based on indication',
            'ace_inhibitor': 'ARB (losartan, valsartan)'
        }
        
        for allergy, alternative in alternatives.items():
            if allergy in allergy_name.lower():
                return alternative
        
        return None
    
    def _suggest_renal_alternative(self, drug_name: str) -> Optional[str]:
        """Suggest renal-friendly alternative."""
        alternatives = {
            'metformin': 'Insulin therapy',
            'gabapentin': 'Pregabalin (lower dose)',
            'digoxin': 'Beta-blocker or calcium channel blocker'
        }
        
        return alternatives.get(drug_name.lower())
