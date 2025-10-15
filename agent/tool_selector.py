"""
Intelligent tool selection based on clinical complaint.

This module analyzes the patient complaint and determines which tools
are most relevant to call, improving efficiency and relevance.
"""
from typing import List, Dict
import re


class ToolSelector:
    """Selects appropriate tools based on clinical context."""
    
    # Define tool relevance rules
    TOOL_KEYWORDS = {
        'labs': [
            'blood', 'lab', 'test', 'results', 'cbc', 'bmp', 'creatinine',
            'glucose', 'hemoglobin', 'a1c', 'liver', 'kidney', 'electrolyte'
        ],
        'imaging': [
            'x-ray', 'ct', 'mri', 'ultrasound', 'scan', 'imaging', 'chest',
            'radiograph', 'echo', 'echocardiogram'
        ],
        'meds': [
            'medication', 'drug', 'pill', 'prescription', 'taking', 'dose',
            'side effect', 'adverse', 'reaction'
        ],
        'ddi': [
            'interaction', 'multiple medications', 'new medication',
            'changed medication', 'drug interaction'
        ],
        'guidelines': [
            'protocol', 'treatment', 'management', 'guideline', 'standard',
            'recommendation', 'therapy'
        ]
    }
    
    # Critical tools that always run
    CRITICAL_TOOLS = ['ehr']  # Always need demographics and conditions
    
    @staticmethod
    def select_tools(complaint: str, ehr_data: Dict = None) -> List[str]:
        """
        Determine which tools to call based on complaint and initial EHR data.
        
        Args:
            complaint: Patient's chief complaint
            ehr_data: Optional EHR data if already retrieved
            
        Returns:
            List of tool names to execute
        """
        complaint_lower = complaint.lower()
        selected_tools = set(ToolSelector.CRITICAL_TOOLS)
        
        # Score each tool based on keyword matches
        tool_scores = {}
        for tool, keywords in ToolSelector.TOOL_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in complaint_lower)
            tool_scores[tool] = score
        
        # Add high-scoring tools
        for tool, score in tool_scores.items():
            if score > 0:
                selected_tools.add(tool)
        
        # Smart defaults based on complaint type
        if any(word in complaint_lower for word in ['pain', 'ache', 'discomfort']):
            selected_tools.update(['labs', 'meds', 'guidelines'])
        
        if any(word in complaint_lower for word in ['shortness', 'breath', 'sob', 'dyspnea']):
            selected_tools.update(['labs', 'imaging', 'meds'])
        
        if any(word in complaint_lower for word in ['dizzy', 'fatigue', 'weakness', 'tired']):
            selected_tools.update(['labs', 'meds'])
        
        # If patient on multiple meds, check DDI
        if ehr_data and len(ehr_data.get('conditions', [])) >= 3:
            selected_tools.add('ddi')
        
        # Always check guidelines if we have condition data
        if ehr_data and ehr_data.get('conditions'):
            selected_tools.add('guidelines')
        
        # Default: if unsure, get everything (safety first)
        if len(selected_tools) <= 2:
            selected_tools = {'ehr', 'labs', 'meds', 'imaging', 'ddi', 'guidelines'}
        
        return list(selected_tools)
    
    @staticmethod
    def prioritize_tools(selected_tools: List[str]) -> List[str]:
        """
        Order tools by priority for sequential execution.
        
        Args:
            selected_tools: List of tool names
            
        Returns:
            Ordered list with critical tools first
        """
        priority_order = ['ehr', 'labs', 'meds', 'imaging', 'ddi', 'guidelines']
        return [tool for tool in priority_order if tool in selected_tools]
    
    @staticmethod
    def explain_selection(complaint: str, selected_tools: List[str]) -> str:
        """
        Generate human-readable explanation of tool selection.
        
        Args:
            complaint: Patient complaint
            selected_tools: Tools that were selected
            
        Returns:
            Explanation string
        """
        skipped = set(['ehr', 'labs', 'meds', 'imaging', 'ddi', 'guidelines']) - set(selected_tools)
        
        explanation = f"Based on complaint '{complaint[:50]}...', selected tools:\n"
        for tool in selected_tools:
            explanation += f"  ✓ {tool}\n"
        
        if skipped:
            explanation += "Skipped (not relevant):\n"
            for tool in skipped:
                explanation += f"  ✗ {tool}\n"
        
        return explanation

