"""
Multi-Agent Collaborative System.

Multiple specialized agents work together:
- Data Gatherer Agent: Collects information
- Analyzer Agent: Identifies patterns and trends
- Risk Assessment Agent: Evaluates safety concerns
- Guideline Agent: Matches to evidence-based protocols
- Coordinator Agent: Synthesizes all perspectives
"""
import asyncio
from typing import Dict, List, Callable, Any
from dataclasses import dataclass


@dataclass
class AgentMessage:
    """Message passed between agents."""
    from_agent: str
    to_agent: str
    content: Dict
    priority: int = 5  # 1-10, 10 = highest


class BaseSpecializedAgent:
    """Base class for specialized agents."""
    
    def __init__(self, name: str, tools: Dict, llm):
        self.name = name
        self.tools = tools
        self.llm = llm
    
    async def process(self, patient_data: Dict) -> Dict:
        """Process patient data and return insights."""
        raise NotImplementedError


class DataGathererAgent(BaseSpecializedAgent):
    """Specialist in efficient data collection."""
    
    async def process(self, patient_data: Dict) -> Dict:
        """
        Intelligently gather data based on complaint and initial findings.
        """
        patient_id = patient_data['patient_id']
        complaint = patient_data['complaint']
        
        insights = {
            'agent': self.name,
            'data_collected': {},
            'rationale': []
        }
        
        # Always get EHR
        ehr_data = await self.tools['ehr'](patient_id)
        insights['data_collected']['EHR'] = ehr_data
        insights['rationale'].append("EHR: Always needed for demographics and conditions")
        
        # Prepare parallel tasks
        tasks = []
        task_names = []
        
        # Smart decisions based on complaint
        if any(word in complaint.lower() for word in ['fatigue', 'tired', 'weak', 'dizzy']):
            tasks.append(self.tools['labs'](patient_id))
            task_names.append('LABS')
            insights['rationale'].append("LABS: Fatigue/weakness suggests need for CBC, metabolic panel")
        
        if any(word in complaint.lower() for word in ['pain', 'chest', 'breath']):
            tasks.append(self.tools['imaging'](patient_id))
            task_names.append('IMAGING')
            insights['rationale'].append("IMAGING: Chest symptoms require imaging review")
        
        # Always check meds if multiple conditions
        conditions = ehr_data.get('conditions', [])
        if len(conditions) >= 2:
            tasks.append(self.tools['meds'](patient_id))
            task_names.append('MEDS')
            insights['rationale'].append("MEDS: Multiple conditions likely mean multiple medications")
            
        # Execute parallel tasks
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                name = task_names[i]
                if not isinstance(result, Exception):
                    insights['data_collected'][name] = result
        
        return insights


class AnalyzerAgent(BaseSpecializedAgent):
    """Specialist in pattern recognition and trend analysis."""
    
    async def process(self, patient_data: Dict) -> Dict:
        """
        Analyze trends, patterns, and correlations in the data.
        """
        insights = {
            'agent': self.name,
            'trends': [],
            'patterns': [],
            'correlations': []
        }
        
        # Analyze lab trends
        labs = patient_data.get('observations', {}).get('LABS', {})
        if 'historical_data' in labs:
            results = labs.get('results', [])
            historical = labs['historical_data']
            
            for result in results:
                test_name = result.get('test', '')
                current = result.get('value')
                trend = result.get('trend', 'stable')
                
                # Check historical data
                hist_key = test_name.lower().replace(' ', '_') + '_6mo_ago'
                if hist_key in historical:
                    past_value = historical[hist_key]
                    if current != past_value:
                        direction = "↑" if current > past_value else "↓"
                        insights['trends'].append({
                            'test': test_name,
                            'change': f"{past_value} → {current}",
                            'direction': direction,
                            'clinical_significance': self._assess_significance(test_name, past_value, current)
                        })
        
        # Pattern recognition
        ehr = patient_data.get('observations', {}).get('EHR', {})
        conditions = [c.get('name', '') for c in ehr.get('conditions', [])]
        
        # Common patterns
        if 'CKD' in str(conditions) and 'Diabetes' in str(conditions):
            insights['patterns'].append({
                'name': 'Diabetic Nephropathy Pattern',
                'description': 'CKD + Diabetes suggests diabetic kidney disease',
                'monitoring': 'Close monitoring of HbA1c, microalbuminuria, BP'
            })
        
        if 'Hypertension' in str(conditions) and 'CKD' in str(conditions):
            insights['patterns'].append({
                'name': 'Hypertensive Nephropathy',
                'description': 'HTN contributing to kidney disease',
                'monitoring': 'Aggressive BP control target <130/80'
            })
        
        return insights
    
    def _assess_significance(self, test_name: str, old_value: float, new_value: float) -> str:
        """Assess clinical significance of lab change."""
        try:
            change_percent = abs((new_value - old_value) / old_value * 100) if old_value != 0 else 0
            
            if 'creatinine' in test_name.lower():
                if change_percent > 20:
                    return "SIGNIFICANT: >20% change in creatinine"
                return "Monitor"
            
            if 'egfr' in test_name.lower():
                if change_percent > 15:
                    return "SIGNIFICANT: >15% decline in kidney function"
                return "Stable decline"
            
            if 'hemoglobin' in test_name.lower():
                if change_percent > 10:
                    return "SIGNIFICANT: >10% change in hemoglobin"
                return "Minor change"
            
            return "Assess clinically"
        except Exception:
            return "Assess clinically"


class RiskAssessmentAgent(BaseSpecializedAgent):
    """Specialist in identifying safety concerns and risks."""
    
    async def process(self, patient_data: Dict) -> Dict:
        """
        Assess risks: DDIs, contraindications, critical values.
        """
        insights = {
            'agent': self.name,
            'risks': [],
            'warnings': [],
            'critical_values': []
        }
        
        # Check DDIs
        ddi_data = patient_data.get('observations', {}).get('DDI', [])
        if isinstance(ddi_data, list):
            for interaction in ddi_data:
                severity = interaction.get('severity', 'unknown')
                risk_entry = {
                    'type': 'Drug Interaction',
                    'severity': severity,
                    'drugs': f"{interaction.get('a')} + {interaction.get('b')}",
                    'description': interaction.get('description'),
                    'action': 'Review and monitor' if severity == 'moderate' else 'Consider alternatives'
                }
                
                if severity in ['major', 'severe']:
                    insights['risks'].append(risk_entry)
                else:
                    insights['warnings'].append(risk_entry)
        
        # Check critical lab values
        labs = patient_data.get('observations', {}).get('LABS', {}).get('results', [])
        for lab in labs:
            if lab.get('status') in ['CRITICAL_HIGH', 'CRITICAL_LOW']:
                insights['critical_values'].append({
                    'test': lab['test'],
                    'value': f"{lab['value']} {lab['unit']}",
                    'status': lab['status'],
                    'action': 'Immediate clinical review required'
                })
            elif lab.get('status') in ['HIGH', 'LOW']:
                if 'potassium' in lab['test'].lower() or 'creatinine' in lab['test'].lower():
                    insights['warnings'].append({
                        'type': 'Abnormal Lab',
                        'test': lab['test'],
                        'value': f"{lab['value']} {lab['unit']}",
                        'action': 'Monitor and trend'
                    })
        
        return insights


class GuidelineAgent(BaseSpecializedAgent):
    """Specialist in matching to evidence-based guidelines."""
    
    async def process(self, patient_data: Dict) -> Dict:
        """
        Match findings to clinical guidelines and best practices.
        """
        insights = {
            'agent': self.name,
            'applicable_guidelines': [],
            'recommendations': []
        }
        
        # Get conditions
        ehr = patient_data.get('observations', {}).get('EHR', {})
        conditions = [c.get('name', '') for c in ehr.get('conditions', [])]
        
        # Search guidelines for each condition
        tasks = []
        for condition in conditions:
            keywords = condition.split()[0].lower()  # First word of condition
            tasks.append(self.tools['guidelines'](keywords))
            
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list) and result:
                    insights['applicable_guidelines'].extend(result)
        
        # Generate specific recommendations based on findings
        labs = patient_data.get('observations', {}).get('LABS', {}).get('results', [])
        
        for lab in labs:
            if lab.get('test') == 'eGFR' and lab.get('value', 100) < 35:
                insights['recommendations'].append({
                    'source': 'KDIGO CKD Guidelines',
                    'recommendation': 'Nephrology referral for eGFR <35',
                    'strength': 'Strong',
                    'urgency': 'Within 2-4 weeks'
                })
            
            if lab.get('test') == 'Hemoglobin' and lab.get('value', 15) < 11:
                insights['recommendations'].append({
                    'source': 'KDIGO Anemia Guidelines',
                    'recommendation': 'Consider ESA therapy for Hgb <11 in CKD',
                    'strength': 'Moderate',
                    'urgency': 'Non-urgent'
                })
        
        return insights


class CoordinatorAgent(BaseSpecializedAgent):
    """
    Meta-agent that coordinates all other agents and synthesizes final output.
    """
    
    def __init__(self, name: str, tools: Dict, llm):
        super().__init__(name, tools, llm)
        self.agents = {
            'gatherer': DataGathererAgent('DataGatherer', tools, llm),
            'analyzer': AnalyzerAgent('Analyzer', tools, llm),
            'risk': RiskAssessmentAgent('RiskAssessment', tools, llm),
            'guideline': GuidelineAgent('GuidelineExpert', tools, llm)
        }
    
    async def run(self, patient_id: str, complaint: str, emit: Callable) -> Dict:
        """
        Orchestrate all agents and synthesize their insights.
        """
        emit("COORDINATOR_STARTED")
        
        # Phase 1: Data Gathering
        emit("AGENT_DataGatherer_STARTED")
        gatherer_output = await self.agents['gatherer'].process({
            'patient_id': patient_id,
            'complaint': complaint
        })
        emit("AGENT_DataGatherer_COMPLETED")
        
        # Phase 2: Parallel Analysis
        emit("PARALLEL_ANALYSIS_STARTED")
        
        analysis_tasks = [
            self.agents['analyzer'].process({
                'patient_id': patient_id,
                'complaint': complaint,
                'observations': gatherer_output['data_collected']
            }),
            self.agents['risk'].process({
                'patient_id': patient_id,
                'complaint': complaint,
                'observations': gatherer_output['data_collected']
            }),
            self.agents['guideline'].process({
                'patient_id': patient_id,
                'complaint': complaint,
                'observations': gatherer_output['data_collected']
            })
        ]
        
        results = await asyncio.gather(*analysis_tasks)
        analyzer_output, risk_output, guideline_output = results
        
        emit("PARALLEL_ANALYSIS_COMPLETED")
        
        # Phase 3: Synthesis
        emit("SYNTHESIS_STARTED")
        final_summary = self._synthesize_perspectives(
            gatherer_output,
            analyzer_output,
            risk_output,
            guideline_output,
            patient_id,
            complaint
        )
        emit("SYNTHESIS_COMPLETED")
        
        return {
            'summary': final_summary,
            'agent_insights': {
                'gatherer': gatherer_output,
                'analyzer': analyzer_output,
                'risk': risk_output,
                'guideline': guideline_output
            }
        }
    
    def _synthesize_perspectives(self, gatherer, analyzer, risk, guideline, 
                                  patient_id, complaint) -> str:
        """Combine insights from all agents into final summary."""
        
        # Build enriched observations
        observations = gatherer['data_collected'].copy()
        observations['ANALYSIS'] = analyzer
        observations['RISKS'] = risk
        observations['GUIDELINES'] = guideline
        
        # Call LLM with enriched context
        try:
            with open('prompts/system.txt', 'r') as f:
                system_prompt = f.read()
        except Exception:
            system_prompt = "You are a clinical decision support assistant."
            
        user_prompt = f"patient_id: {patient_id}\ncomplaint: {complaint}"
        
        return self.llm.synthesize(system_prompt, user_prompt, observations)
