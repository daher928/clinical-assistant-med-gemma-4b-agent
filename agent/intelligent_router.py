"""
Intelligent Router: Automatically selects the best autonomy level.

This router analyzes the case and chooses:
- Level 1: Simple, straightforward cases
- Level 1+2: Complex, uncertain cases  
- Level 1+2+4: Critical, high-stakes cases
"""
from typing import Dict, Callable
import re


class IntelligentRouter:
    """
    Routes cases to appropriate autonomy level based on complexity and risk.
    """
    
    # Keywords indicating complexity
    COMPLEX_KEYWORDS = [
        'unclear', 'uncertain', 'confused', 'multiple', 'several',
        'worsening', 'progressive', 'new onset', 'change in'
    ]
    
    # Keywords indicating critical/high-risk
    CRITICAL_KEYWORDS = [
        'chest pain', 'difficulty breathing', 'severe', 'acute',
        'sudden', 'unconscious', 'bleeding', 'seizure', 'stroke',
        'mi', 'heart attack', 'anaphylaxis', 'shock'
    ]
    
    # Patient factors indicating complexity
    HIGH_RISK_CONDITIONS = [
        'ckd', 'kidney', 'dialysis', 'transplant', 'immunosuppressed',
        'chemotherapy', 'heart failure', 'liver failure'
    ]
    
    @staticmethod
    def assess_complexity(complaint: str, ehr_data: Dict = None) -> dict:
        """
        Assess case complexity to determine routing.
        
        Args:
            complaint: Patient's chief complaint
            ehr_data: Optional EHR data for additional context
            
        Returns:
            Dictionary with complexity assessment
        """
        complaint_lower = complaint.lower()
        complexity_score = 0
        risk_score = 0
        reasons = []
        
        # Check complaint complexity
        for keyword in IntelligentRouter.COMPLEX_KEYWORDS:
            if keyword in complaint_lower:
                complexity_score += 1
                reasons.append(f"Complex keyword: '{keyword}'")
        
        # Check for critical indicators
        for keyword in IntelligentRouter.CRITICAL_KEYWORDS:
            if keyword in complaint_lower:
                risk_score += 2
                reasons.append(f"Critical keyword: '{keyword}'")
        
        # Check EHR for high-risk conditions
        if ehr_data:
            conditions = ehr_data.get('conditions', [])
            condition_count = len(conditions)
            
            # Multiple conditions = more complex
            if condition_count >= 4:
                complexity_score += 2
                reasons.append(f"{condition_count} active conditions")
            elif condition_count >= 3:
                complexity_score += 1
            
            # Check for high-risk conditions
            for condition in conditions:
                condition_name = condition.get('name', '').lower()
                for risk_condition in IntelligentRouter.HIGH_RISK_CONDITIONS:
                    if risk_condition in condition_name:
                        risk_score += 1
                        reasons.append(f"High-risk condition: {condition.get('name')}")
                        break
            
            # Check medication count
            # (Would need meds data, but we can estimate from conditions)
            if condition_count >= 3:
                complexity_score += 1
                reasons.append("Likely polypharmacy")
        
        # Determine recommended level
        total_score = complexity_score + risk_score
        
        # TEMPORARY: Force CRITICAL for quality testing
        # TODO: Revert after validating output quality
        if risk_score >= 2 or total_score >= 3:  # Lower threshold
            recommended_level = "CRITICAL"
            recommended_autonomy = "Level 1+2+4 (Smart + ReAct + Self-Correct)"
        elif complexity_score >= 2 or total_score >= 3:
            recommended_level = "COMPLEX"
            recommended_autonomy = "Level 1+2 (Smart + ReAct)"
        else:
            recommended_level = "STANDARD"
            recommended_autonomy = "Level 1 (Smart Selection)"
        
        return {
            'complexity_score': complexity_score,
            'risk_score': risk_score,
            'total_score': total_score,
            'level': recommended_level,
            'autonomy': recommended_autonomy,
            'reasons': reasons
        }
    
    @staticmethod
    def route_to_agent(patient_id: str, complaint: str, ehr_data: Dict, 
                       tools: Dict, llm, emit: Callable) -> Dict:
        """
        Route to appropriate agent based on complexity assessment.
        
        Args:
            patient_id: Patient identifier
            complaint: Chief complaint
            ehr_data: EHR data
            tools: Available tools
            llm: Language model
            emit: Progress callback
            
        Returns:
            Result dictionary with summary and metadata
        """
        # Assess complexity
        assessment = IntelligentRouter.assess_complexity(complaint, ehr_data)
        
        emit(f"COMPLEXITY_ASSESSMENT: {assessment['level']}")
        emit(f"ROUTING_TO: {assessment['autonomy']}")
        
        if assessment['reasons']:
            for reason in assessment['reasons'][:3]:  # Top 3 reasons
                emit(f"  • {reason}")
        
        level = assessment['level']
        
        try:
            if level == "CRITICAL":
                # Level 1+2+4: Smart + ReAct + Self-Correction
                emit("USING_CRITICAL_MODE: Maximum quality & safety")
                
                # First, use ReAct for adaptive gathering
                from agent.react_agent import ReActAgent
                react = ReActAgent(tools, llm)
                observations = react.run(patient_id, complaint, emit)
                
                # Then, use self-correction for quality
                from agent.self_correcting_agent import SelfCorrectingAgent
                corrector = SelfCorrectingAgent(tools, llm)
                result = corrector.run(patient_id, complaint, observations, emit)
                
                return {
                    'summary': result,
                    'level_used': 'CRITICAL (1+2+4)',
                    'assessment': assessment,
                    'react_trace': react.get_trace(),
                    'correction_trace': corrector.get_correction_trace()
                }
                
            elif level == "COMPLEX":
                # Level 1+2: Smart + ReAct
                emit("USING_COMPLEX_MODE: Adaptive reasoning")
                
                from agent.react_agent import ReActAgent
                react = ReActAgent(tools, llm)
                observations = react.run(patient_id, complaint, emit)
                
                # Synthesize
                system_prompt = open('prompts/system.txt').read()
                user_prompt = f"patient_id: {patient_id}\ncomplaint: {complaint}"
                result = llm.synthesize(system_prompt, user_prompt, observations)
                
                return {
                    'summary': result,
                    'level_used': 'COMPLEX (1+2)',
                    'assessment': assessment,
                    'react_trace': react.get_trace()
                }
                
            else:
                # Level 1: Smart Selection (already in orchestrator)
                emit("USING_STANDARD_MODE: Fast & efficient")
                
                # The orchestrator already has Level 1 implemented
                # This is the fallback - we'll use the standard run_agent
                return {
                    'use_standard': True,
                    'level_used': 'STANDARD (1)',
                    'assessment': assessment
                }
                
        except Exception as e:
            emit(f"ROUTING_ERROR: {str(e)}, falling back to standard mode")
            return {
                'use_standard': True,
                'level_used': 'FALLBACK (1)',
                'assessment': assessment,
                'error': str(e)
            }


class HybridMode:
    """
    Convenience class for running in hybrid mode.
    
    Usage:
        result = HybridMode.run(patient_id, complaint, tools, llm, emit)
    """
    
    @staticmethod
    def run(patient_id: str, complaint: str, tools: Dict, llm, emit: Callable) -> str:
        """
        Run in intelligent hybrid mode.
        
        This automatically selects the best autonomy level and returns
        the clinical summary.
        """
        # Step 1: Always get EHR first
        emit("FETCH_EHR_STARTED")
        try:
            ehr_data = tools['ehr'](patient_id)
            emit("FETCH_EHR_COMPLETED")
        except Exception as e:
            emit(f"FETCH_EHR_FAILED: {str(e)}")
            ehr_data = {}
        
        # Step 2: Route based on complexity
        route_result = IntelligentRouter.route_to_agent(
            patient_id, complaint, ehr_data, tools, llm, emit
        )
        
        # Step 3: If standard mode selected, return signal to use normal flow
        if route_result.get('use_standard'):
            return None  # Signal to use standard run_agent
        
        # Otherwise return the advanced result
        return route_result['summary']

