"""
ReAct (Reasoning + Acting) Agent Implementation.

This agent uses a thought → action → observation loop to dynamically
decide which tools to call based on intermediate findings.
"""
from typing import Dict, List, Callable, Tuple, Optional
import json


class ReActAgent:
    """
    Implements ReAct pattern for autonomous clinical decision-making.
    
    The agent alternates between:
    1. THOUGHT: Reasoning about what to do next
    2. ACTION: Calling a tool
    3. OBSERVATION: Analyzing the result
    
    This continues until sufficient information is gathered.
    """
    
    MAX_ITERATIONS = 6  # Prevent infinite loops
    
    def __init__(self, tools: Dict[str, Callable], llm):
        """
        Initialize ReAct agent.
        
        Args:
            tools: Dictionary of available tools {name: function}
            llm: Language model for reasoning
        """
        self.tools = tools
        self.llm = llm
        self.thought_history = []
        self.action_history = []
        self.observation_history = []
    
    def run(self, patient_id: str, complaint: str, emit: Callable) -> Dict:
        """
        Execute ReAct loop to gather information and reason about patient.
        
        Args:
            patient_id: Patient identifier
            complaint: Chief complaint
            emit: Progress callback
            
        Returns:
            Dictionary of observations from all tool calls
        """
        observations = {}
        iteration = 0
        
        # Initial context
        context = f"Patient {patient_id}: {complaint}"
        
        while iteration < self.MAX_ITERATIONS:
            iteration += 1
            emit(f"ITERATION_{iteration}_STARTED")
            
            # THINK: What should I do next?
            thought = self._generate_thought(context, observations, complaint)
            self.thought_history.append(thought)
            emit(f"THOUGHT: {thought[:100]}...")
            
            # Check if agent thinks it's done
            if "FINISH" in thought or "SUFFICIENT" in thought:
                emit("AGENT_DECIDED_TO_STOP")
                break
            
            # ACT: Choose and execute tool
            action = self._choose_action(thought, observations)
            if not action:
                emit("NO_MORE_ACTIONS_NEEDED")
                break
            
            tool_name, tool_args = action
            self.action_history.append(action)
            emit(f"ACTION: Calling {tool_name}")
            
            # Execute tool
            try:
                if tool_name == 'ehr':
                    result = self.tools['ehr'](patient_id)
                elif tool_name == 'labs':
                    result = self.tools['labs'](patient_id)
                elif tool_name == 'meds':
                    result = self.tools['meds'](patient_id)
                elif tool_name == 'imaging':
                    result = self.tools['imaging'](patient_id)
                elif tool_name == 'ddi':
                    # Need meds first
                    if 'meds' not in observations:
                        meds_data = self.tools['meds'](patient_id)
                        observations['meds'] = meds_data
                    result = self.tools['ddi'](observations['meds'].get('active', []))
                elif tool_name == 'guidelines':
                    keyword = tool_args.get('keyword', 'general')
                    result = self.tools['guidelines'](keyword)
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}
                
                observations[tool_name] = result
                self.observation_history.append({tool_name: result})
                emit(f"OBSERVATION: Retrieved {tool_name} data")
                
            except Exception as e:
                emit(f"ERROR: {tool_name} failed - {str(e)}")
                observations[tool_name] = {"error": str(e)}
            
            # Update context
            context = self._build_context(patient_id, complaint, observations)
        
        emit(f"REACT_COMPLETED after {iteration} iterations")
        return observations
    
    def _generate_thought(self, context: str, observations: Dict, complaint: str) -> str:
        """
        Generate next reasoning step.
        
        This is a simplified version. In production, you'd use the LLM here.
        """
        # Simple rule-based reasoning for now
        # In production, call LLM with: "Given {context} and {observations}, what should I do next?"
        
        if not observations:
            return "THOUGHT: Need to start by getting patient demographics and conditions. Action: get_ehr"
        
        if 'ehr' in observations and 'labs' not in observations:
            conditions = observations['ehr'].get('conditions', [])
            if any('kidney' in c.get('name', '').lower() or 'ckd' in c.get('name', '').lower() 
                   for c in conditions):
                return "THOUGHT: Patient has CKD. Need labs to assess renal function. Action: get_labs"
            return "THOUGHT: Need lab data to assess current status. Action: get_labs"
        
        if 'labs' in observations and 'meds' not in observations:
            labs = observations['labs'].get('results', [])
            abnormal = [l for l in labs if l.get('status') in ['HIGH', 'LOW']]
            if abnormal:
                return "THOUGHT: Found abnormal labs. Need to check medications. Action: get_meds"
            return "THOUGHT: Should check current medications. Action: get_meds"
        
        if 'meds' in observations and 'ddi' not in observations:
            med_count = len(observations['meds'].get('active', []))
            if med_count >= 3:
                return "THOUGHT: Multiple medications. Should check for interactions. Action: get_ddi"
        
        if 'ehr' in observations and 'guidelines' not in observations:
            conditions = observations['ehr'].get('conditions', [])
            if conditions:
                condition_name = conditions[0].get('name', 'general')
                return f"THOUGHT: Need guidelines for {condition_name}. Action: search_guidelines with keyword"
        
        return "THOUGHT: SUFFICIENT information gathered. FINISH"
    
    def _choose_action(self, thought: str, observations: Dict) -> Optional[Tuple[str, Dict]]:
        """
        Extract action from thought.
        
        Returns:
            Tuple of (tool_name, args) or None
        """
        thought_lower = thought.lower()
        
        # Parse action from thought
        if 'get_ehr' in thought_lower or 'demographics' in thought_lower:
            return ('ehr', {})
        elif 'get_labs' in thought_lower or 'lab' in thought_lower:
            return ('labs', {})
        elif 'get_meds' in thought_lower or 'medication' in thought_lower:
            return ('meds', {})
        elif 'imaging' in thought_lower:
            return ('imaging', {})
        elif 'ddi' in thought_lower or 'interaction' in thought_lower:
            return ('ddi', {})
        elif 'guideline' in thought_lower:
            # Extract keyword from thought
            if 'ckd' in thought_lower or 'kidney' in thought_lower:
                keyword = 'ckd'
            elif 'diabetes' in thought_lower:
                keyword = 'diabetes'
            else:
                keyword = 'general'
            return ('guidelines', {'keyword': keyword})
        
        return None
    
    def _build_context(self, patient_id: str, complaint: str, observations: Dict) -> str:
        """Build updated context for next reasoning step."""
        context = f"Patient {patient_id}: {complaint}\n\n"
        context += "Data gathered so far:\n"
        for key, value in observations.items():
            if isinstance(value, dict) and 'error' not in value:
                context += f"- {key}: ✓\n"
            elif 'error' in str(value):
                context += f"- {key}: ✗ (error)\n"
        return context
    
    def get_trace(self) -> str:
        """Get human-readable trace of agent's reasoning."""
        trace = "=== ReAct Agent Trace ===\n\n"
        for i, (thought, action, obs) in enumerate(zip(
            self.thought_history, 
            self.action_history, 
            self.observation_history
        ), 1):
            trace += f"Iteration {i}:\n"
            trace += f"  THOUGHT: {thought}\n"
            trace += f"  ACTION: {action[0]}({action[1]})\n"
            trace += f"  OBSERVATION: {list(obs.keys())}\n\n"
        return trace

