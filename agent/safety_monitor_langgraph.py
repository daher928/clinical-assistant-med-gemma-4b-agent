"""
LangGraph-based Safety Monitor Agent (Advanced).

This implementation uses LangGraph to create a state machine for safety checks:
- Initial check → DDI analysis → Contraindication check → Dosing analysis → 
  Guidelines check → Pharmacology check → EHR history → LLM reasoning → Final assessment

NOTE: Requires langgraph installation:
    pip install langgraph langchain langchain-community
"""

from typing import TypedDict, Annotated, Sequence, List, Dict, Optional, Callable
import operator

# Try to import LangGraph components
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("Warning: LangGraph not installed. Install with: pip install langgraph langchain")


class SafetyCheckState(TypedDict):
    """
    State that gets passed between nodes in the safety check graph.
    
    This represents all information the safety monitor knows at any point.
    """
    patient_id: str
    prescriptions: List[Dict]
    patient_context: Dict
    warnings: Annotated[List[Dict], operator.add]
    recommendations: Annotated[List[str], operator.add]
    alternatives: Annotated[List[Dict], operator.add]
    current_drug_index: int
    check_phase: str
    llm_insights: List[str]
    emit: Callable


class SafetyMonitorLangGraph:
    """
    LangGraph-based safety monitor with structured workflow.
    
    The agent navigates through a graph of safety checks, making decisions
    at each node about what to check next based on findings.
    """
    
    def __init__(self, tools: Dict, llm):
        """
        Initialize LangGraph safety monitor.
        
        Args:
            tools: Dictionary of available tools
            llm: Language model for reasoning
        """
        self.tools = tools
        self.llm = llm
        self.graph = None
        
        if LANGGRAPH_AVAILABLE:
            self._build_graph()
        else:
            print("LangGraph not available - using fallback mode")
    
    def _build_graph(self):
        """
        Build the state graph for safety check workflow.
        
        Graph structure:
        1. START → initial_check
        2. initial_check → ddi_analysis
        3. ddi_analysis → contraindication_check
        4. contraindication_check → dosing_analysis
        5. dosing_analysis → guidelines_check
        6. guidelines_check → pharmacology_check
        7. pharmacology_check → ehr_history_check
        8. ehr_history_check → (conditional)
           - If warnings found → llm_reasoning
           - If no warnings → final_assessment
        9. llm_reasoning → final_assessment
        10. final_assessment → END
        """
        if not LANGGRAPH_AVAILABLE:
            return
        
        graph = StateGraph(SafetyCheckState)
        
        # Add nodes
        graph.add_node("initial_check", self._initial_check)
        graph.add_node("ddi_analysis", self._ddi_analysis)
        graph.add_node("contraindication_check", self._contraindication_check)
        graph.add_node("dosing_analysis", self._dosing_analysis)
        graph.add_node("guidelines_check", self._guidelines_check)
        graph.add_node("pharmacology_check", self._pharmacology_check)
        graph.add_node("ehr_history_check", self._ehr_history_check)
        graph.add_node("llm_reasoning", self._llm_reasoning)
        graph.add_node("final_assessment", self._final_assessment)
        
        # Add edges
        graph.set_entry_point("initial_check")
        graph.add_edge("initial_check", "ddi_analysis")
        graph.add_edge("ddi_analysis", "contraindication_check")
        graph.add_edge("contraindication_check", "dosing_analysis")
        graph.add_edge("dosing_analysis", "guidelines_check")
        graph.add_edge("guidelines_check", "pharmacology_check")
        graph.add_edge("pharmacology_check", "ehr_history_check")
        
        # Conditional edge: check if we need LLM reasoning
        graph.add_conditional_edges(
            "ehr_history_check",
            self._should_use_llm,
            {
                "yes": "llm_reasoning",
                "no": "final_assessment"
            }
        )
        
        graph.add_edge("llm_reasoning", "final_assessment")
        graph.add_edge("final_assessment", END)
        
        self.graph = graph.compile()
    
    def _initial_check(self, state: SafetyCheckState) -> SafetyCheckState:
        """Node: Initial validation of prescriptions."""
        state['emit']("SAFETY_MONITOR_INITIAL_CHECK")
        
        prescriptions = state['prescriptions']
        if not prescriptions:
            state['warnings'].append({
                'severity': 'low',
                'drug_name': 'System',
                'warning_type': 'info',
                'message': 'No prescriptions to validate',
                'recommendation': 'Add prescriptions to check'
            })
        
        state['current_drug_index'] = 0
        state['check_phase'] = 'initial'
        return state
    
    def _ddi_analysis(self, state: SafetyCheckState) -> SafetyCheckState:
        """Node: Check drug-drug interactions."""
        state['emit']("SAFETY_MONITOR_DDI_ANALYSIS")
        state['check_phase'] = 'ddi'
        
        prescriptions = state['prescriptions']
        current_meds = state['patient_context'].get('MEDS', {}).get('active', [])
        
        if 'ddi' in self.tools:
            for prescription in prescriptions:
                drug_name = prescription.get('name', '')
                all_meds = current_meds + [{'name': drug_name}]
                
                try:
                    ddi_results = self.tools['ddi'](all_meds)
                    for interaction in ddi_results:
                        if interaction.get('a') == drug_name or interaction.get('b') == drug_name:
                            severity = 'critical' if interaction.get('severity') == 'major' else 'high' if interaction.get('severity') == 'moderate' else 'medium'
                            state['warnings'].append({
                                'severity': severity,
                                'drug_name': drug_name,
                                'warning_type': 'ddi',
                                'message': interaction.get('description', 'Drug interaction detected'),
                                'recommendation': interaction.get('recommendation', 'Monitor patient closely'),
                                'source': 'ddi_database'
                            })
                except Exception:
                    pass
        
        return state
    
    def _contraindication_check(self, state: SafetyCheckState) -> SafetyCheckState:
        """Node: Check contraindications."""
        state['emit']("SAFETY_MONITOR_CONTRAINDICATION_CHECK")
        state['check_phase'] = 'contraindication'
        
        # Import safety monitor to use its methods
        try:
            from agent.safety_monitor import SafetyMonitorAgent
            temp_agent = SafetyMonitorAgent(self.tools, self.llm)
            
            prescriptions = state['prescriptions']
            conditions = state['patient_context'].get('EHR', {}).get('conditions', [])
            labs = state['patient_context'].get('LABS', {}).get('results', [])
            
            for prescription in prescriptions:
                drug_name = prescription.get('name', '')
                warnings = temp_agent._check_contraindications(drug_name, conditions, labs)
                for warning in warnings:
                    state['warnings'].append({
                        'severity': warning.severity,
                        'drug_name': warning.drug_name,
                        'warning_type': warning.warning_type,
                        'message': warning.message,
                        'recommendation': warning.recommendation,
                        'alternative': warning.alternative,
                        'source': warning.source or 'drug_database'
                    })
        except Exception:
            pass
        
        return state
    
    def _dosing_analysis(self, state: SafetyCheckState) -> SafetyCheckState:
        """Node: Check dosage appropriateness."""
        state['emit']("SAFETY_MONITOR_DOSING_ANALYSIS")
        state['check_phase'] = 'dosing'
        
        try:
            from agent.safety_monitor import SafetyMonitorAgent
            temp_agent = SafetyMonitorAgent(self.tools, self.llm)
            
            prescriptions = state['prescriptions']
            ehr = state['patient_context'].get('EHR', {})
            labs = state['patient_context'].get('LABS', {}).get('results', [])
            
            for prescription in prescriptions:
                drug_name = prescription.get('name', '')
                dose = prescription.get('dose', '')
                frequency = prescription.get('frequency', '')
                
                warnings = temp_agent._check_dosage(drug_name, dose, frequency, ehr, labs)
                for warning in warnings:
                    state['warnings'].append({
                        'severity': warning.severity,
                        'drug_name': warning.drug_name,
                        'warning_type': warning.warning_type,
                        'message': warning.message,
                        'recommendation': warning.recommendation,
                        'alternative': warning.alternative,
                        'source': warning.source or 'drug_database'
                    })
        except Exception:
            pass
        
        return state
    
    def _guidelines_check(self, state: SafetyCheckState) -> SafetyCheckState:
        """Node: Check against clinical guidelines."""
        state['emit']("SAFETY_MONITOR_GUIDELINES_CHECK")
        state['check_phase'] = 'guidelines'
        
        try:
            from agent.safety_monitor import SafetyMonitorAgent
            temp_agent = SafetyMonitorAgent(self.tools, self.llm)
            
            prescriptions = state['prescriptions']
            conditions = state['patient_context'].get('EHR', {}).get('conditions', [])
            
            for prescription in prescriptions:
                drug_name = prescription.get('name', '')
                warnings = temp_agent._check_guidelines(drug_name, conditions, state['patient_context'])
                for warning in warnings:
                    state['warnings'].append({
                        'severity': warning.severity,
                        'drug_name': warning.drug_name,
                        'warning_type': warning.warning_type,
                        'message': warning.message,
                        'recommendation': warning.recommendation,
                        'source': warning.source or 'guidelines'
                    })
        except Exception:
            pass
        
        return state
    
    def _pharmacology_check(self, state: SafetyCheckState) -> SafetyCheckState:
        """Node: Check pharmacology-based interactions."""
        state['emit']("SAFETY_MONITOR_PHARMACOLOGY_CHECK")
        state['check_phase'] = 'pharmacology'
        
        try:
            from agent.safety_monitor import SafetyMonitorAgent
            temp_agent = SafetyMonitorAgent(self.tools, self.llm)
            
            prescriptions = state['prescriptions']
            current_meds = state['patient_context'].get('MEDS', {}).get('active', [])
            
            for prescription in prescriptions:
                drug_name = prescription.get('name', '')
                warnings = temp_agent._check_pharmacology(drug_name, current_meds, state['patient_context'])
                for warning in warnings:
                    state['warnings'].append({
                        'severity': warning.severity,
                        'drug_name': warning.drug_name,
                        'warning_type': warning.warning_type,
                        'message': warning.message,
                        'recommendation': warning.recommendation,
                        'source': warning.source or 'pharmacology'
                    })
        except Exception:
            pass
        
        return state
    
    def _ehr_history_check(self, state: SafetyCheckState) -> SafetyCheckState:
        """Node: Check historical EHR patterns."""
        state['emit']("SAFETY_MONITOR_EHR_HISTORY_CHECK")
        state['check_phase'] = 'ehr_history'
        
        try:
            from agent.safety_monitor import SafetyMonitorAgent
            temp_agent = SafetyMonitorAgent(self.tools, self.llm)
            
            prescriptions = state['prescriptions']
            
            for prescription in prescriptions:
                drug_name = prescription.get('name', '')
                warnings = temp_agent._check_ehr_history(
                    state['patient_id'], drug_name, state['patient_context']
                )
                for warning in warnings:
                    state['warnings'].append({
                        'severity': warning.severity,
                        'drug_name': warning.drug_name,
                        'warning_type': warning.warning_type,
                        'message': warning.message,
                        'recommendation': warning.recommendation,
                        'source': warning.source or 'ehr_history'
                    })
        except Exception:
            pass
        
        return state
    
    def _should_use_llm(self, state: SafetyCheckState) -> str:
        """Conditional edge: Decide if LLM reasoning is needed."""
        warnings = state['warnings']
        
        # Use LLM if we have critical or high severity warnings
        critical_or_high = any(
            w.get('severity') in ['critical', 'high'] for w in warnings
        )
        
        return "yes" if critical_or_high else "no"
    
    def _llm_reasoning(self, state: SafetyCheckState) -> SafetyCheckState:
        """Node: Use LLM for intelligent reasoning on complex cases."""
        state['emit']("SAFETY_MONITOR_LLM_REASONING")
        state['check_phase'] = 'llm_reasoning'
        
        try:
            from agent.safety_monitor import SafetyMonitorAgent
            temp_agent = SafetyMonitorAgent(self.tools, self.llm)
            
            doctor_decision = {'prescriptions': state['prescriptions']}
            safety_results = {'warnings': state['warnings']}
            
            insights = temp_agent._llm_safety_reasoning(
                state['prescriptions'], safety_results, state['patient_context'], state['emit']
            )
            state['llm_insights'] = insights
        except Exception:
            state['llm_insights'] = []
        
        return state
    
    def _final_assessment(self, state: SafetyCheckState) -> SafetyCheckState:
        """Node: Generate final recommendations and alternatives."""
        state['emit']("SAFETY_MONITOR_FINAL_ASSESSMENT")
        state['check_phase'] = 'final'
        
        try:
            from agent.safety_monitor import SafetyMonitorAgent
            temp_agent = SafetyMonitorAgent(self.tools, self.llm)
            
            # Generate recommendations
            warnings_objects = []
            for w in state['warnings']:
                from agent.safety_monitor import SafetyWarning
                warnings_objects.append(SafetyWarning(
                    severity=w.get('severity', 'medium'),
                    drug_name=w.get('drug_name', ''),
                    warning_type=w.get('warning_type', 'general'),
                    message=w.get('message', ''),
                    recommendation=w.get('recommendation', ''),
                    alternative=w.get('alternative'),
                    source=w.get('source'),
                    confidence=w.get('confidence')
                ))
            
            state['recommendations'] = temp_agent._generate_recommendations(warnings_objects)
            state['alternatives'] = temp_agent._suggest_alternatives(
                state['prescriptions'], warnings_objects, state['patient_context']
            )
        except Exception:
            pass
        
        return state
    
    def run(self, patient_id: str, doctor_decision: Dict, patient_context: Dict, emit: Callable) -> Dict:
        """
        Execute the safety check graph.
        
        Args:
            patient_id: Patient identifier
            doctor_decision: Doctor's treatment plan with prescriptions
            patient_context: Full patient data
            emit: Progress callback
            
        Returns:
            Safety analysis results
        """
        if not LANGGRAPH_AVAILABLE or self.graph is None:
            # Fallback to regular safety monitor
            from agent.safety_monitor import SafetyMonitorAgent
            agent = SafetyMonitorAgent(self.tools, self.llm)
            return agent.run(patient_id, doctor_decision, patient_context, emit)
        
        # Initialize state
        initial_state = SafetyCheckState(
            patient_id=patient_id,
            prescriptions=doctor_decision.get('prescriptions', []),
            patient_context=patient_context,
            warnings=[],
            recommendations=[],
            alternatives=[],
            current_drug_index=0,
            check_phase='',
            llm_insights=[],
            emit=emit
        )
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        # Generate summary
        from agent.safety_monitor import SafetyMonitorAgent
        temp_agent = SafetyMonitorAgent(self.tools, self.llm)
        summary = temp_agent._generate_safety_summary({'warnings': final_state['warnings']})
        
        return {
            'status': 'completed',
            'warnings': final_state['warnings'],
            'summary': summary,
            'recommendations': final_state['recommendations'],
            'alternatives': final_state['alternatives'],
            'llm_insights': final_state['llm_insights']
        }

