"""
Self-Correcting Agent with Quality Checks.

This agent can:
1. Generate an initial summary
2. Critique its own work
3. Identify gaps or errors
4. Gather additional data
5. Regenerate improved summary
"""
from typing import Dict, Callable, List


class SelfCorrectingAgent:
    """
    Agent that critiques and improves its own outputs.
    
    Workflow:
    1. Initial synthesis
    2. Self-critique (identify issues)
    3. If issues found → gather more data → retry
    4. Repeat until quality threshold met or max iterations
    """
    
    MAX_ITERATIONS = 3
    
    def __init__(self, tools: Dict[str, Callable], llm):
        """
        Initialize self-correcting agent.
        
        Args:
            tools: Available tools
            llm: Language model
        """
        self.tools = tools
        self.llm = llm
        self.correction_history = []
    
    def run(self, patient_id: str, complaint: str, observations: Dict, emit: Callable) -> str:
        """
        Run agent with self-correction loop.
        
        Args:
            patient_id: Patient ID
            complaint: Chief complaint
            observations: Initial observations
            emit: Progress callback
            
        Returns:
            Final corrected summary
        """
        iteration = 0
        current_summary = None
        
        while iteration < self.MAX_ITERATIONS:
            iteration += 1
            emit(f"CORRECTION_ITERATION_{iteration}")
            
            # Generate summary
            if not current_summary:
                emit("GENERATING_INITIAL_SUMMARY")
                system_prompt = open('prompts/system.txt').read()
                user_prompt = f"patient_id: {patient_id}\ncomplaint: {complaint}"
                current_summary = self.llm.synthesize(system_prompt, user_prompt, observations)
            
            # Critique the summary
            emit("CRITIQUING_OUTPUT")
            critique = self._critique_summary(current_summary, observations)
            self.correction_history.append({
                'iteration': iteration,
                'summary': current_summary,
                'critique': critique
            })
            
            # Check if good enough
            if critique['quality_score'] >= 8.0:
                emit(f"QUALITY_THRESHOLD_MET (score: {critique['quality_score']})")
                break
            
            # Identify what to fix
            issues = critique['issues']
            if not issues:
                emit("NO_ISSUES_FOUND")
                break
            
            emit(f"FOUND_{len(issues)}_ISSUES")
            
            # Gather additional data if needed
            if self._needs_more_data(issues):
                emit("GATHERING_ADDITIONAL_DATA")
                observations = self._gather_missing_data(issues, patient_id, observations)
            
            # Regenerate with corrections
            emit("REGENERATING_SUMMARY")
            correction_prompt = self._build_correction_prompt(current_summary, issues)
            current_summary = self.llm.synthesize(
                correction_prompt,
                f"patient_id: {patient_id}\ncomplaint: {complaint}",
                observations
            )
        
        emit(f"SELF_CORRECTION_COMPLETED after {iteration} iterations")
        return current_summary
    
    def _critique_summary(self, summary: str, observations: Dict) -> Dict:
        """
        Critique the generated summary for quality and completeness.
        
        Returns:
            Dictionary with quality_score and list of issues
        """
        issues = []
        score = 10.0  # Start perfect, deduct for issues
        
        # Check 1: Are all data sources cited?
        expected_sources = list(observations.keys())
        for source in expected_sources:
            if f"[{source}]" not in summary:
                issues.append(f"Missing citation for {source} data")
                score -= 0.5
        
        # Check 2: Word count (should be 150-250)
        word_count = len(summary.split())
        if word_count > 300:
            issues.append(f"Too verbose ({word_count} words, target 150-250)")
            score -= 1.0
        elif word_count < 100:
            issues.append(f"Too brief ({word_count} words, target 150-250)")
            score -= 1.0
        
        # Check 3: Has required sections?
        required_sections = [
            "ONE-LINE SUMMARY",
            "SNAPSHOT",
            "ATTENTION NEEDED",
            "PLAN"
        ]
        for section in required_sections:
            if section not in summary:
                issues.append(f"Missing required section: {section}")
                score -= 1.5
        
        # Check 4: Specific values present?
        labs = observations.get('LABS', {}).get('results', [])
        for lab in labs:
            if lab.get('status') in ['HIGH', 'LOW']:
                test_name = lab['test']
                value = str(lab['value'])
                if value not in summary:
                    issues.append(f"Abnormal {test_name} value not mentioned")
                    score -= 0.5
        
        # Check 5: DDI warnings mentioned?
        ddi = observations.get('DDI', [])
        if isinstance(ddi, list) and len(ddi) > 0:
            if "interaction" not in summary.lower():
                issues.append("Drug interactions not addressed")
                score -= 1.0
        
        # Check 6: Action plan present?
        if "1." not in summary and "2." not in summary:
            issues.append("No numbered action plan")
            score -= 1.0
        
        return {
            'quality_score': max(0, score),
            'issues': issues,
            'word_count': word_count
        }
    
    def _needs_more_data(self, issues: List[str]) -> bool:
        """Determine if issues require gathering more data."""
        data_keywords = ['missing', 'incomplete', 'not found', 'unavailable']
        return any(any(keyword in issue.lower() for keyword in data_keywords) 
                   for issue in issues)
    
    def _gather_missing_data(self, issues: List[str], patient_id: str, 
                             observations: Dict) -> Dict:
        """Gather data for missing sources mentioned in issues."""
        for issue in issues:
            if 'IMAGING' in issue and 'IMAGING' not in observations:
                observations['IMAGING'] = self.tools['imaging'](patient_id)
            elif 'GUIDE' in issue and 'GUIDE' not in observations:
                # Search for relevant guidelines
                ehr = observations.get('EHR', {})
                conditions = ehr.get('conditions', [])
                if conditions:
                    keyword = conditions[0].get('name', 'general').split()[0].lower()
                    observations['GUIDE'] = self.tools['guidelines'](keyword)
        
        return observations
    
    def _build_correction_prompt(self, previous_summary: str, issues: List[str]) -> str:
        """Build prompt for corrected generation."""
        correction_instructions = open('prompts/system.txt').read()
        
        correction_instructions += f"\n\nPREVIOUS ATTEMPT HAD THESE ISSUES:\n"
        for i, issue in enumerate(issues, 1):
            correction_instructions += f"{i}. {issue}\n"
        
        correction_instructions += "\nPlease generate an IMPROVED summary addressing these issues.\n"
        
        return correction_instructions
    
    def get_correction_trace(self) -> str:
        """Get human-readable trace of corrections made."""
        trace = "=== Self-Correction Trace ===\n\n"
        for entry in self.correction_history:
            trace += f"Iteration {entry['iteration']}:\n"
            trace += f"  Quality Score: {entry['critique']['quality_score']}/10\n"
            if entry['critique']['issues']:
                trace += f"  Issues Found:\n"
                for issue in entry['critique']['issues']:
                    trace += f"    - {issue}\n"
            trace += "\n"
        return trace

