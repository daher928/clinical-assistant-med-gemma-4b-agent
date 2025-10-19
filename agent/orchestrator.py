"""
Agent orchestrator for coordinating clinical assistant workflows.

This module coordinates tool calls and LLM synthesis with proper
error handling and dynamic decision making.
"""
import json
import re
from typing import Callable, Dict, Optional
from tools import ehr, labs, meds, imaging, ddi, guidelines, safety_checker
from llm.med_gemma_wrapper import MedGemmaLLM
from config import Config


def extract_keywords(text: str) -> list:
    """
    Extract medical keywords from complaint text.
    
    Args:
        text: Complaint or query text
        
    Returns:
        List of potential keywords for guideline search
    """
    # Common medical terms that might indicate guideline needs
    keywords = []
    
    # Extract potential condition keywords
    medical_terms = [
        'diabetes', 'hypertension', 'ckd', 'kidney', 'heart', 'cardiac',
        'copd', 'asthma', 'cancer', 'stroke', 'seizure', 'infection',
        'pneumonia', 'sepsis', 'anemia', 'thrombosis', 'bleeding',
        'pain', 'fever', 'fatigue', 'dizziness', 'chest', 'respiratory'
    ]
    
    text_lower = text.lower()
    for term in medical_terms:
        if term in text_lower:
            keywords.append(term)
    
    # Default to general internal medicine if no specific terms
    if not keywords:
        keywords.append('general')
    
    return keywords


def run_agent_hybrid(patient_id: str, complaint: str, emit: Callable[[str], None]) -> str:
    """
    HYBRID MODE: Intelligent routing to best autonomy level.
    
    Now includes multi-agent system for data insights.
    
    Args:
        patient_id: Patient identifier
        complaint: Clinical complaint
        emit: Progress callback
        
    Returns:
        Clinical summary
    """
    # Use multi-agent system for comprehensive analysis
    emit("USING_MULTI_AGENT_MODE (Level 5 - Comprehensive Analysis)")
    return run_agent_multi_agent(patient_id, complaint, emit)


def run_agent_standard(patient_id: str, complaint: str, emit: Callable[[str], None]) -> str:
    """
    STANDARD MODE: Level 1 autonomy with smart tool selection.
    
    Fast and efficient for most cases.
    """
    return _run_agent_level1(patient_id, complaint, emit)


def _run_agent_level1(patient_id: str, complaint: str, emit: Callable[[str], None]) -> str:
    """
    Execute the clinical assistant agent workflow with smart tool selection.
    
    This function orchestrates tool calls with intelligent selection based on
    the complaint, performs error handling, and synthesizes results using the LLM.
    
    Args:
        patient_id: Patient identifier
        complaint: Clinical complaint or question
        emit: Callback function to emit progress updates
        
    Returns:
        Clinical summary text from the LLM
    """
    observations = {}
    errors = []
    
    # Step 1: ALWAYS fetch EHR (critical baseline)
    try:
        emit("FETCH_EHR_STARTED")
        observations['EHR'] = ehr.get_ehr(patient_id)
        emit("FETCH_EHR_COMPLETED")
    except Exception as e:
        emit(f"FETCH_EHR_FAILED: {str(e)}")
        errors.append(f"EHR: {str(e)}")
        observations['EHR'] = {"error": str(e)}
    
    # Step 2: SMART TOOL SELECTION (Level 1 Autonomy)
    try:
        from agent.tool_selector import ToolSelector
        selected_tools = ToolSelector.select_tools(complaint, observations.get('EHR'))
        prioritized_tools = ToolSelector.prioritize_tools(selected_tools)
        emit(f"SMART_SELECTION: {', '.join(prioritized_tools)}")
    except Exception as e:
        # Fallback to all tools if selection fails
        emit(f"TOOL_SELECTION_FAILED: {str(e)}, using all tools")
        prioritized_tools = ['ehr', 'labs', 'meds', 'imaging', 'ddi', 'guidelines']
    
    # Step 3: Execute ONLY selected tools
    if 'labs' in prioritized_tools:
        try:
            emit("FETCH_LABS_STARTED")
            observations['LABS'] = labs.get_labs(patient_id)
            emit("FETCH_LABS_COMPLETED")
        except Exception as e:
            emit(f"FETCH_LABS_FAILED: {str(e)}")
            errors.append(f"Labs: {str(e)}")
            observations['LABS'] = {"error": str(e)}
    else:
        emit("FETCH_LABS_SKIPPED (not relevant)")
    
    if 'meds' in prioritized_tools:
        try:
            emit("FETCH_MEDS_STARTED")
            observations['MEDS'] = meds.get_meds(patient_id)
            emit("FETCH_MEDS_COMPLETED")
        except Exception as e:
            emit(f"FETCH_MEDS_FAILED: {str(e)}")
            errors.append(f"Medications: {str(e)}")
            observations['MEDS'] = {"error": str(e), "active": []}
    else:
        emit("FETCH_MEDS_SKIPPED (not relevant)")
        observations['MEDS'] = {"active": []}  # Empty for DDI check
    
    if 'imaging' in prioritized_tools:
        try:
            emit("FETCH_IMAGING_STARTED")
            observations['IMAGING'] = imaging.get_imaging(patient_id)
            emit("FETCH_IMAGING_COMPLETED")
        except Exception as e:
            emit(f"FETCH_IMAGING_FAILED: {str(e)}")
            errors.append(f"Imaging: {str(e)}")
            observations['IMAGING'] = {"error": str(e)}
    else:
        emit("FETCH_IMAGING_SKIPPED (not relevant)")
    
    # Check DDI only if we have meds and it's selected
    if 'ddi' in prioritized_tools and 'meds' in prioritized_tools:
        try:
            emit("CHECK_DDI_STARTED")
            active_meds = observations.get('MEDS', {}).get('active', [])
            if active_meds and not isinstance(observations.get('MEDS', {}).get('error'), str):
                observations['DDI'] = ddi.query_ddi(active_meds)
            else:
                observations['DDI'] = []
            emit("CHECK_DDI_COMPLETED")
        except Exception as e:
            emit(f"CHECK_DDI_FAILED: {str(e)}")
            errors.append(f"DDI: {str(e)}")
            observations['DDI'] = {"error": str(e)}
    else:
        if 'ddi' not in prioritized_tools:
            emit("CHECK_DDI_SKIPPED (not relevant)")
        observations['DDI'] = []
    
    # Search Guidelines only if selected
    if 'guidelines' in prioritized_tools:
        try:
            emit("SEARCH_GUIDELINES_STARTED")
            
            # Extract keywords from complaint
            keywords = extract_keywords(complaint)
            
            # Also check for conditions in EHR
            if 'conditions' in observations.get('EHR', {}):
                for condition in observations['EHR'].get('conditions', []):
                    condition_name = condition.get('name', '').lower()
                    if 'ckd' in condition_name or 'kidney' in condition_name:
                        keywords.append('ckd')
                    if 'diabetes' in condition_name:
                        keywords.append('diabetes')
                    if 'hypertension' in condition_name or 'htn' in condition_name:
                        keywords.append('hypertension')
            
            # Search for each keyword and combine results
            all_guidelines = []
            seen_titles = set()
            
            for keyword in keywords[:3]:  # Limit to top 3 keywords
                results = guidelines.search_guidelines(keyword)
                for result in results:
                    if result['title'] not in seen_titles:
                        all_guidelines.append(result)
                        seen_titles.add(result['title'])
            
            observations['GUIDE'] = all_guidelines
            emit(f"SEARCH_GUIDELINES_COMPLETED (keywords: {', '.join(keywords)})")
        except Exception as e:
            emit(f"SEARCH_GUIDELINES_FAILED: {str(e)}")
            errors.append(f"Guidelines: {str(e)}")
            observations['GUIDE'] = {"error": str(e)}
    else:
        emit("SEARCH_GUIDELINES_SKIPPED (not relevant)")
        observations['GUIDE'] = []
    
    # Step 7: Load system prompt
    try:
        with open("prompts/system.txt", 'r') as f:
            system_prompt = f.read()
    except Exception as e:
        system_prompt = "You are a clinical decision support assistant."
        emit(f"WARNING: Could not load system prompt: {str(e)}")
    
    # Step 8: Build user prompt
    user_prompt = f"patient_id: {patient_id}\ncomplaint: \"{complaint}\""
    
    if errors:
        user_prompt += f"\n\nNote: Some data sources had errors:\n" + "\n".join(f"- {e}" for e in errors)
    
    # Step 9: Synthesize with LLM
    try:
        emit("SYNTHESIS_STARTED")
        
        # For Mock mode: use simple mock
        if Config.USE_MOCK_LLM:
            emit("USING_MOCK_MODE")
            llm = MedGemmaLLM()
            result = llm.synthesize(system_prompt, user_prompt, observations)
        else:
            # PRODUCTION MODE: Pure MedGemma
            emit("USING_MEDGEMMA_MODEL")
            llm = MedGemmaLLM()
            result = llm.synthesize(system_prompt, user_prompt, observations)
        
        emit("SYNTHESIS_COMPLETED")
        
        # Store observations for potential follow-up questions
        return result, observations
    except Exception as e:
        emit(f"SYNTHESIS_FAILED: {str(e)}")
        return f"❌ Error during synthesis: {str(e)}\n\nObservations collected:\n{observations}", observations


def run_agent_multi_agent(patient_id: str, complaint: str, emit: Callable[[str], None]) -> tuple:
    """
    MULTI-AGENT MODE: Level 5 autonomy with specialized agents.
    
    Uses CoordinatorAgent to orchestrate:
    - DataGathererAgent: Efficient data collection
    - AnalyzerAgent: Pattern/trend recognition and data insights
    - RiskAssessmentAgent: Safety and contraindications
    - GuidelineAgent: Evidence-based matching
    
    Args:
        patient_id: Patient identifier
        complaint: Clinical complaint
        emit: Progress callback
        
    Returns:
        Tuple of (clinical_summary, observations_with_insights)
    """
    try:
        from agent.multi_agent_system import CoordinatorAgent
        from llm.med_gemma_wrapper import MedGemmaLLM
        
        # Initialize tools
        tools = {
            'ehr': ehr.get_ehr,
            'labs': labs.get_labs,
            'meds': meds.get_meds,
            'imaging': imaging.get_imaging,
            'ddi': ddi.query_ddi,
            'guidelines': guidelines.search_guidelines
        }
        
        # Initialize LLM
        llm = MedGemmaLLM()
        
        # Initialize coordinator
        coordinator = CoordinatorAgent('Coordinator', tools, llm)
        
        # Run multi-agent analysis
        result = coordinator.run(patient_id, complaint, emit)
        
        # Extract summary and agent insights
        summary = result['summary']
        agent_insights = result['agent_insights']
        
        # Build enriched observations for frontend
        observations = {
            'EHR': agent_insights['gatherer']['data_collected'].get('EHR', {}),
            'LABS': agent_insights['gatherer']['data_collected'].get('LABS', {}),
            'MEDS': agent_insights['gatherer']['data_collected'].get('MEDS', {}),
            'IMAGING': agent_insights['gatherer']['data_collected'].get('IMAGING', {}),
            'DDI': agent_insights['gatherer']['data_collected'].get('DDI', []),
            'GUIDE': agent_insights['gatherer']['data_collected'].get('GUIDE', []),
            # Add agent insights for data insights tab
            'ANALYSIS': agent_insights['analyzer'],
            'RISKS': agent_insights['risk'],
            'GUIDELINES': agent_insights['guideline']
        }
        
        return summary, observations
        
    except Exception as e:
        emit(f"MULTI_AGENT_FAILED: {str(e)}")
        # Fallback to standard mode
        emit("FALLING_BACK_TO_STANDARD_MODE")
        return run_agent_standard(patient_id, complaint, emit)


class ClinicalAssistantOrchestrator:
    """
    Alternative orchestrator class for more complex workflows.
    
    Note: The run_agent function above is the primary interface.
    This class can be extended for LangGraph integration.
    """
    
    def __init__(self, llm: Optional[MedGemmaLLM] = None):
        """
        Initialize the orchestrator.
        
        Args:
            llm: Language model instance (creates new if None)
        """
        self.llm = llm or MedGemmaLLM()
        self.tools = {
            'ehr': ehr.get_ehr,
            'labs': labs.get_labs,
            'meds': meds.get_meds,
            'imaging': imaging.get_imaging,
            'ddi': ddi.query_ddi,
            'guidelines': guidelines.search_guidelines
        }
    
    def run(self, patient_id: str, complaint: str, progress_callback: Optional[Callable] = None) -> str:
        """
        Execute clinical query using the agent.
        
        Args:
            patient_id: Patient identifier
            complaint: Clinical complaint
            progress_callback: Optional callback for progress updates
            
        Returns:
            Clinical summary
        """
        def emit(msg):
            if progress_callback:
                progress_callback(msg)
        
        return run_agent_hybrid(patient_id, complaint, emit)


def run_safety_monitor(patient_id: str, doctor_decision: Dict, patient_context: Dict, emit: Callable[[str], None]) -> Dict:
    """
    Run safety monitor on doctor's treatment decisions.
    
    Args:
        patient_id: Patient identifier
        doctor_decision: Doctor's treatment plan with prescriptions
        patient_context: Full patient data from diagnostic workflow
        emit: Progress callback
        
    Returns:
        Safety analysis results
    """
    try:
        from agent.safety_monitor import SafetyMonitorAgent
        
        # Initialize tools for safety monitor
        tools = {
            'ehr': ehr.get_ehr,
            'labs': labs.get_labs,
            'meds': meds.get_meds,
            'imaging': imaging.get_imaging,
            'ddi': ddi.query_ddi,
            'guidelines': guidelines.search_guidelines,
            'safety_checker': safety_checker.check_drug_safety
        }
        
        # Initialize LLM
        llm = MedGemmaLLM()
        
        # Initialize safety monitor
        safety_monitor = SafetyMonitorAgent(tools, llm)
        
        # Run safety analysis
        safety_result = safety_monitor.run(patient_id, doctor_decision, patient_context, emit)
        
        return safety_result
        
    except Exception as e:
        emit(f"SAFETY_MONITOR_ERROR: {str(e)}")
        return {
            'status': 'error',
            'warnings': [],
            'summary': f'Safety monitor failed: {str(e)}'
        }


# Alias for backward compatibility
def run_agent(patient_id: str, complaint: str, emit: Callable[[str], None]) -> str:
    """
    Main entry point - uses hybrid intelligent mode.
    
    Backward compatible alias for run_agent_hybrid.
    """
    return run_agent_hybrid(patient_id, complaint, emit)

