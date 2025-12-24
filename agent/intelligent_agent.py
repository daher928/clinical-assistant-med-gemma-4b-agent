"""
Intelligent Diagnosis Agent - Single agent with LLM-based tool selection.

This agent demonstrates the core AI agent pattern:
- Brain: MedGemma LLM for reasoning and decision-making
- Context: Patient information (EHR, labs, meds, etc.)
- Tools: Available actions (get_ehr, get_labs, get_meds, get_imaging, query_ddi, search_guidelines)

The agent uses a ReAct-style reasoning loop:
1. Think: Reason about what information is needed
2. Act: Execute selected tools
3. Observe: Collect results
4. Think: Decide if more information is needed or synthesize diagnosis
"""
import json
import asyncio
from typing import Dict, List, Callable, Optional, Any
from tools import ehr, labs, meds, imaging, ddi, guidelines
from llm.med_gemma_wrapper import MedGemmaLLM


class IntelligentDiagnosisAgent:
    """
    Single intelligent agent that uses LLM reasoning to select and execute tools.
    
    This agent demonstrates how an AI agent works:
    - Uses its "brain" (LLM) to reason about what to do
    - Maintains "context" (patient data) to understand the situation
    - Uses "tools" (actions) to gather information and act
    """
    
    # Available tools with descriptions
    TOOLS = {
        'get_ehr': {
            'function': ehr.get_ehr,
            'description': 'Get Electronic Health Record: demographics, conditions, allergies, vitals, social history. Always call this first for patient context.',
            'requires': ['patient_id']
        },
        'get_labs': {
            'function': labs.get_labs,
            'description': 'Get Laboratory Results: blood tests, chemistry panels, trends over time. Use when complaint involves symptoms that labs can diagnose (fatigue, infection, kidney issues, anemia, etc.).',
            'requires': ['patient_id']
        },
        'get_meds': {
            'function': meds.get_meds,
            'description': 'Get Medications: active medications, doses, indications. Use when complaint might be medication-related, or when checking for drug interactions.',
            'requires': ['patient_id']
        },
        'get_imaging': {
            'function': imaging.get_imaging,
            'description': 'Get Imaging Reports: X-rays, CT scans, MRIs, ultrasounds. Use when complaint involves pain, trauma, respiratory issues, or when imaging is clinically indicated.',
            'requires': ['patient_id']
        },
        'query_ddi': {
            'function': ddi.query_ddi,
            'description': 'Check Drug-Drug Interactions: analyzes medication combinations for dangerous interactions. Requires medications list from get_meds first.',
            'requires': ['medications']
        },
        'search_guidelines': {
            'function': guidelines.search_guidelines,
            'description': 'Search Clinical Guidelines: evidence-based treatment protocols. Use when you have a diagnosis or condition and need treatment recommendations.',
            'requires': ['keyword']
        }
    }
    
    def __init__(self, llm: Optional[MedGemmaLLM] = None):
        """
        Initialize the intelligent diagnosis agent.
        
        Args:
            llm: MedGemma LLM instance (creates new if None)
        """
        self.llm = llm or MedGemmaLLM()
        self.observations: Dict[str, Any] = {}
        self.tools_called: List[str] = []
        self.max_iterations = 5  # Prevent infinite loops
        
    def _reason_about_tools(self, complaint: str, current_context: Dict) -> List[str]:
        """
        Use LLM to reason about which tools to call next.
        
        Args:
            complaint: Patient's chief complaint
            current_context: Currently collected patient data
            
        Returns:
            List of tool names to execute next
        """
        # Build reasoning prompt
        available_tools = "\n".join([
            f"- {name}: {info['description']}"
            for name, info in self.TOOLS.items()
        ])
        
        context_summary = self._summarize_context(current_context)
        tools_already_called = ", ".join(self.tools_called) if self.tools_called else "none"
        
        reasoning_prompt = f"""You are a clinical diagnosis agent. Your job is to decide which tools to use to help diagnose a patient.

PATIENT COMPLAINT: "{complaint}"

CURRENT CONTEXT:
{context_summary}

TOOLS ALREADY CALLED: {tools_already_called}

AVAILABLE TOOLS:
{available_tools}

REASONING FRAMEWORK:
1. What is the chief concern from the complaint?
2. What information do I need to diagnose this?
3. Which tools provide that information?
4. What's the priority order?

IMPORTANT RULES:
- Always call get_ehr FIRST if you haven't called it yet (needed for patient context)
- Only call query_ddi if you have medications from get_meds
- Only call search_guidelines if you have a condition or diagnosis to search for
- Don't call the same tool twice unless you have new information that changes the need
- Be selective - only call tools that are relevant to the complaint

Respond with ONLY a JSON array of tool names you want to call next, in priority order.
Example: ["get_ehr"]
Example: ["get_labs", "get_meds"]
Example: ["query_ddi"]
Example: ["search_guidelines"]

If you have enough information to diagnose, respond with: ["synthesize"]

Your decision:"""
        
        try:
            # Use LLM to reason (for mock mode, use simple logic)
            if hasattr(self.llm, '_lazy_load'):
                # Real LLM mode - use simple reasoning for now
                # In production, this would call the LLM
                return self._simple_tool_selection(complaint, current_context, tools_already_called)
            else:
                # Mock mode - use simple logic
                return self._simple_tool_selection(complaint, current_context, tools_already_called)
        except Exception as e:
            # Fallback to simple selection
            return self._simple_tool_selection(complaint, current_context, tools_already_called)
    
    def _simple_tool_selection(self, complaint: str, current_context: Dict, tools_called: str) -> List[str]:
        """
        Simple tool selection logic (fallback when LLM reasoning isn't available).
        
        This demonstrates the reasoning pattern even without full LLM reasoning.
        """
        complaint_lower = complaint.lower()
        selected = []
        
        # Always get EHR first if not done
        if 'EHR' not in current_context and 'get_ehr' not in self.tools_called:
            return ['get_ehr']
        
        # After EHR, reason about what's needed
        ehr_data = current_context.get('EHR', {})
        conditions = [c.get('name', '').lower() for c in ehr_data.get('conditions', [])]
        
        # Check for lab-related complaints
        lab_keywords = ['fatigue', 'dizzy', 'weakness', 'anemia', 'kidney', 'creatinine', 'glucose', 'blood', 'lab', 'test']
        if any(kw in complaint_lower for kw in lab_keywords) and 'LABS' not in current_context:
            selected.append('get_labs')
        
        # Check for medication-related complaints
        med_keywords = ['medication', 'drug', 'prescription', 'side effect', 'interaction', 'taking']
        if any(kw in complaint_lower for kw in med_keywords) and 'MEDS' not in current_context:
            selected.append('get_meds')
        
        # Check for imaging-related complaints
        imaging_keywords = ['pain', 'chest', 'x-ray', 'ct', 'mri', 'scan', 'imaging', 'fracture', 'trauma']
        if any(kw in complaint_lower for kw in imaging_keywords) and 'IMAGING' not in current_context:
            selected.append('get_imaging')
        
        # If we have meds but no DDI check
        if 'MEDS' in current_context and 'DDI' not in current_context:
            meds_data = current_context.get('MEDS', {})
            active_meds = meds_data.get('active', [])
            if len(active_meds) > 1:  # Multiple meds = check interactions
                selected.append('query_ddi')
        
        # If we have conditions but no guidelines
        if conditions and 'GUIDE' not in current_context:
            # Check if complaint suggests need for guidelines
            if any(c in ['ckd', 'diabetes', 'hypertension', 'asthma'] for c in conditions):
                selected.append('search_guidelines')
        
        # If no specific tools selected, get labs and meds as defaults
        if not selected:
            if 'LABS' not in current_context:
                selected.append('get_labs')
            if 'MEDS' not in current_context:
                selected.append('get_meds')
        
        # If we have enough data, suggest synthesis
        if len(current_context) >= 3 and 'LABS' in current_context and 'MEDS' in current_context:
            return ['synthesize']
        
        return selected[:3]  # Limit to 3 tools per iteration
    
    def _summarize_context(self, context: Dict) -> str:
        """Create a readable summary of current context."""
        if not context:
            return "No data collected yet."
        
        summary = []
        
        if 'EHR' in context:
            ehr = context['EHR']
            demo = ehr.get('demographics', {})
            summary.append(f"Patient: {demo.get('age')}yo {demo.get('gender')}")
            conditions = [c.get('name', '') for c in ehr.get('conditions', [])]
            if conditions:
                summary.append(f"Conditions: {', '.join(conditions)}")
        
        if 'LABS' in context:
            labs_data = context['LABS']
            summary.append(f"Labs: {len(labs_data.get('results', []))} results available")
        
        if 'MEDS' in context:
            meds_data = context['MEDS']
            active = meds_data.get('active', [])
            summary.append(f"Medications: {len(active)} active medications")
        
        if 'IMAGING' in context:
            summary.append("Imaging: Reports available")
        
        if 'DDI' in context:
            ddi_data = context['DDI']
            summary.append(f"Drug Interactions: {len(ddi_data) if isinstance(ddi_data, list) else 0} found")
        
        if 'GUIDE' in context:
            guide_data = context['GUIDE']
            summary.append(f"Guidelines: {len(guide_data) if isinstance(guide_data, list) else 0} found")
        
        return "\n".join(summary) if summary else "No data collected yet."
    
    async def _execute_tool(self, tool_name: str, params: Dict, emit: Callable[[str], None]) -> Any:
        """
        Execute a tool and return its result.
        
        Args:
            tool_name: Name of the tool to execute
            params: Parameters for the tool
            emit: Progress callback
            
        Returns:
            Tool execution result
        """
        if tool_name not in self.TOOLS:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool_info = self.TOOLS[tool_name]
        tool_func = tool_info['function']
        
        try:
            emit(f"EXECUTING_TOOL: {tool_name}")
            
            # Call tool with appropriate parameters
            if tool_name == 'get_ehr':
                result = await tool_func(params['patient_id'])
            elif tool_name == 'get_labs':
                result = await tool_func(params['patient_id'])
            elif tool_name == 'get_meds':
                result = await tool_func(params['patient_id'])
            elif tool_name == 'get_imaging':
                result = await tool_func(params['patient_id'])
            elif tool_name == 'query_ddi':
                result = await tool_func(params['medications'])
            elif tool_name == 'search_guidelines':
                result = await tool_func(params['keyword'])
            else:
                raise ValueError(f"Tool {tool_name} not implemented")
            
            emit(f"TOOL_COMPLETED: {tool_name}")
            return result
            
        except Exception as e:
            emit(f"TOOL_ERROR: {tool_name} - {str(e)}")
            return {'error': str(e)}
    
    def _prepare_tool_params(self, tool_name: str, patient_id: str, current_context: Dict) -> Dict:
        """Prepare parameters for a tool call."""
        if tool_name == 'query_ddi':
            # Need medications from MEDS
            meds_data = current_context.get('MEDS', {})
            active_meds = meds_data.get('active', [])
            if not active_meds:
                raise ValueError("Cannot call query_ddi without medications from get_meds")
            return {'medications': active_meds}
        
        elif tool_name == 'search_guidelines':
            # Extract keyword from complaint or conditions
            # Simple extraction - in production, LLM would decide keyword
            ehr = current_context.get('EHR', {})
            conditions = [c.get('name', '').lower() for c in ehr.get('conditions', [])]
            if conditions:
                # Use first condition as keyword, or extract from condition name
                keyword = conditions[0].split()[0] if conditions else 'general'
                # Handle multi-word conditions like "Chronic Kidney Disease"
                if len(conditions[0].split()) > 1:
                    # Try to extract meaningful keyword
                    condition_lower = conditions[0].lower()
                    if 'kidney' in condition_lower or 'ckd' in condition_lower:
                        keyword = 'ckd'
                    elif 'diabetes' in condition_lower:
                        keyword = 'diabetes'
                    elif 'hypertension' in condition_lower or 'htn' in condition_lower:
                        keyword = 'hypertension'
                    elif 'asthma' in condition_lower:
                        keyword = 'asthma'
            else:
                keyword = 'general'
            return {'keyword': keyword}
        
        else:
            # All other tools need patient_id
            return {'patient_id': patient_id}
    
    async def run(self, patient_id: str, complaint: str, emit: Callable[[str], None]) -> tuple:
        """
        Main execution loop - ReAct pattern: Think → Act → Observe → Think
        
        Args:
            patient_id: Patient identifier
            complaint: Patient's chief complaint
            emit: Progress callback function
            
        Returns:
            Tuple of (clinical_summary, observations_dict)
        """
        emit("AGENT_STARTED: Intelligent Diagnosis Agent")
        emit(f"COMPLAINT: {complaint}")
        
        self.observations = {}
        self.tools_called = []
        iteration = 0
        
        # ReAct Loop: Think → Act → Observe → Think
        while iteration < self.max_iterations:
            iteration += 1
            emit(f"ITERATION_{iteration}_STARTED")
            
            # THINK: Reason about what tools to use
            emit("REASONING: Analyzing complaint and deciding which tools to use...")
            tools_to_call = self._reason_about_tools(complaint, self.observations)
            
            # Check if we should synthesize
            if 'synthesize' in tools_to_call:
                emit("DECISION: Enough information collected, synthesizing diagnosis...")
                break
            
            if not tools_to_call:
                emit("DECISION: No more tools needed, synthesizing diagnosis...")
                break
            
            # ACT: Execute selected tools
            # We can run these in parallel using asyncio.gather
            tasks = []
            task_tool_names = []
            
            for tool_name in tools_to_call:
                if tool_name in self.tools_called:
                    emit(f"SKIPPING: {tool_name} (already called)")
                    continue
                
                try:
                    # Prepare parameters
                    params = self._prepare_tool_params(tool_name, patient_id, self.observations)
                    
                    # Add to tasks
                    tasks.append(self._execute_tool(tool_name, params, emit))
                    task_tool_names.append(tool_name)
                    
                except Exception as e:
                    emit(f"ERROR: Failed to prepare {tool_name}: {str(e)}")
                    continue
            
            if tasks:
                results = await asyncio.gather(*tasks)
                
                # OBSERVE: Store results
                for i, result in enumerate(results):
                    tool_name = task_tool_names[i]
                    # Map tool names to observation keys
                    observation_key = {
                        'get_ehr': 'EHR',
                        'get_labs': 'LABS',
                        'get_meds': 'MEDS',
                        'get_imaging': 'IMAGING',
                        'query_ddi': 'DDI',
                        'search_guidelines': 'GUIDE'
                    }.get(tool_name, tool_name.upper())
                    
                    self.observations[observation_key] = result
                    self.tools_called.append(tool_name)
            
            emit(f"ITERATION_{iteration}_COMPLETED")
        
        # Final synthesis
        emit("SYNTHESIS_STARTED: Generating clinical diagnosis summary...")
        
        try:
            # Load system prompt
            try:
                with open("prompts/system.txt", 'r') as f:
                    system_prompt = f.read()
            except Exception as e:
                system_prompt = "You are a clinical decision support assistant."
                emit(f"WARNING: Could not load system prompt: {str(e)}")
            
            # Build user prompt
            user_prompt = f"patient_id: {patient_id}\ncomplaint: \"{complaint}\""
            
            # Synthesize with LLM
            summary = self.llm.synthesize(system_prompt, user_prompt, self.observations)
            
            emit("SYNTHESIS_COMPLETED")
            emit("AGENT_COMPLETED")
            
            return summary, self.observations
            
        except Exception as e:
            emit(f"SYNTHESIS_ERROR: {str(e)}")
            error_summary = f"❌ Error during synthesis: {str(e)}\n\nObservations collected:\n{json.dumps(self.observations, indent=2)}"
            return error_summary, self.observations
