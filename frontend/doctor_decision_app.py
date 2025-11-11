#!/usr/bin/env python3
"""
Doctor Decision & Prescription Management Service
Separate Streamlit app for handling doctor decisions and prescription safety checks.
Runs on port 8503
"""

import streamlit as st
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Page configuration
st.set_page_config(
    page_title="Doctor Decision & Prescription Management",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e40af 0%, #3b82f6 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .prescription-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .safety-warning {
        background: #fef2f2;
        border-left: 4px solid #dc2626;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
    }
    
    .safety-info {
        background: #eff6ff;
        border-left: 4px solid #2563eb;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
    }
    
    /* Dramatic Safety Alert Modal */
    .safety-alert-modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        z-index: 9999;
        display: flex;
        justify-content: center;
        align-items: center;
        animation: fadeIn 0.3s ease-in;
    }
    
    .safety-alert-content {
        background: #ffffff;
        border: 3px solid #dc2626;
        border-radius: 15px;
        padding: 2rem;
        max-width: 600px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        animation: slideIn 0.4s ease-out;
    }
    
    .safety-alert-header {
        background: linear-gradient(135deg, #dc2626, #ef4444);
        color: white;
        padding: 1.5rem;
        margin: -2rem -2rem 1.5rem -2rem;
        border-radius: 12px 12px 0 0;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        box-shadow: 0 4px 8px rgba(220, 38, 38, 0.3);
    }
    
    .safety-alert-warning {
        background: #fef2f2;
        border: 2px solid #dc2626;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        animation: pulse 2s infinite;
    }
    
    .safety-alert-warning h4 {
        color: #dc2626;
        margin: 0 0 0.5rem 0;
        font-size: 1.2rem;
        font-weight: bold;
    }
    
    .safety-alert-warning p {
        color: #991b1b;
        margin: 0.5rem 0;
        line-height: 1.5;
    }
    
    .safety-alert-warning .recommendation {
        background: #fef3c7;
        border-left: 4px solid #d97706;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
        font-style: italic;
        color: #92400e;
    }
    
    .safety-alert-close {
        background: #dc2626;
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 8px;
        font-size: 1.1rem;
        font-weight: bold;
        cursor: pointer;
        width: 100%;
        margin-top: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .safety-alert-close:hover {
        background: #b91c1c;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    .safety-alert-alternative {
        background: #f0f9ff;
        border: 2px solid #0ea5e9;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .safety-alert-alternative h4 {
        color: #0c4a6e;
        margin: 0 0 0.5rem 0;
        font-size: 1.2rem;
        font-weight: bold;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideIn {
        from { 
            opacity: 0;
            transform: translateY(-50px) scale(0.9);
        }
        to { 
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(220, 38, 38, 0); }
        100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
    }
    
    /* Progress Step Cards */
    .step-card {
        background: white;
        border: 2px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        display: flex;
        align-items: center;
        gap: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .step-card.active {
        border-color: #3b82f6;
        background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
        animation: pulse-blue 2s ease-in-out infinite;
    }
    
    .step-card.completed {
        border-color: #22c55e;
        background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
    }
    
    .step-card.failed {
        border-color: #ef4444;
        background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
    }
    
    .step-card.skipped {
        border-color: #94a3b8;
        background: #f8fafc;
        opacity: 0.7;
    }
    
    .step-icon {
        font-size: 1.5rem;
        width: 3rem;
        height: 3rem;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        flex-shrink: 0;
    }
    
    .step-card.active .step-icon {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white;
        animation: icon-pulse 1.5s ease-in-out infinite;
    }
    
    .step-card.completed .step-icon {
        background: linear-gradient(135deg, #22c55e, #16a34a);
        color: white;
    }
    
    .step-card.failed .step-icon {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
    }
    
    .step-card.skipped .step-icon {
        background: #cbd5e1;
        color: #64748b;
    }
    
    .step-content {
        flex: 1;
        min-width: 0;
    }
    
    .step-title {
        font-weight: 600;
        font-size: 1rem;
        color: #1e293b;
        margin-bottom: 0.25rem;
    }
    
    .step-description {
        font-size: 0.875rem;
        color: #64748b;
        line-height: 1.4;
    }
    
    .step-status {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .step-card.active .step-status {
        background: #3b82f6;
        color: white;
    }
    
    .step-card.completed .step-status {
        background: #22c55e;
        color: white;
    }
    
    .phase-group {
        margin: 2rem 0;
        padding: 1.5rem;
        background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
        border-radius: 16px;
        border: 1px solid #e2e8f0;
    }
    
    .phase-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #e5e7eb;
    }
    
    .phase-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1e293b;
    }
    
    .phase-progress {
        font-size: 0.875rem;
        color: #64748b;
        font-weight: 500;
    }
    
    @keyframes pulse-blue {
        0%, 100% { box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15); }
        50% { box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3); }
    }
    
    @keyframes icon-pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    
    @keyframes sparkle-icon {
        0%, 100% { opacity: 1; transform: scale(1) rotate(0deg); }
        50% { opacity: 0.7; transform: scale(1.2) rotate(180deg); }
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'prescriptions' not in st.session_state:
        st.session_state['prescriptions'] = []
    if 'treatment_notes' not in st.session_state:
        st.session_state['treatment_notes'] = ""
    if 'doctor_decision' not in st.session_state:
        st.session_state['doctor_decision'] = None
    if 'safety_result' not in st.session_state:
        st.session_state['safety_result'] = None
    if 'patient_data' not in st.session_state:
        st.session_state['patient_data'] = {}
    if 'show_dramatic_alert' not in st.session_state:
        st.session_state['show_dramatic_alert'] = False

def load_patient_database():
    """Load patient database"""
    try:
        with open('demo_data/patient_database.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"patients": []}

def load_patient_data(patient_id=None):
    """Load patient data from the database"""
    if patient_id:
        try:
            with open('demo_data/patient_database.json', 'r') as f:
                database = json.load(f)
                for patient in database.get('patients', []):
                    if patient['patient_id'] == patient_id:
                        return patient
        except FileNotFoundError:
            pass
    
    # Fallback to old patient_data.json for backward compatibility
    try:
        with open('demo_data/patient_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            'patient_id': 'P001',
            'name': 'John Smith',
            'demographics': {'age': 68, 'gender': 'Male'},
            'conditions': ['Osteoarthritis', 'Chronic Heart Failure (Class II)', 'Chronic Kidney Disease (Stage 3b)'],
            'allergies': ['Penicillin'],
            'medications': ['Lisinopril 10mg once daily (ACE inhibitor)', 'Furosemide 40mg once daily'],
            'labs': {'eGFR': 35, 'Creatinine': 2.1}
        }

def save_patient_data(patient_data):
    """Save patient data to file"""
    with open('demo_data/patient_data.json', 'w') as f:
        json.dump(patient_data, f, indent=2)

# Safety Monitor Step Definitions
SAFETY_STEP_DEFINITIONS = {
    'SAFETY_MONITOR_STARTED': {
        'title': 'Initializing Safety Monitor',
        'icon': 'fa-shield-halved',
        'description': 'Starting comprehensive safety analysis',
        'phase': 1,
        'phase_name': 'Initialization',
        'order': 1
    },
    'SAFETY_CHECKING': {
        'title': 'Checking Prescriptions',
        'icon': 'fa-pills',
        'description': 'Validating each prescription for safety',
        'phase': 1,
        'phase_name': 'Initialization',
        'order': 2
    },
    'SAFETY_MONITOR_DDI_ANALYSIS': {
        'title': 'Drug Interaction Analysis',
        'icon': 'fa-exclamation-triangle',
        'description': 'Checking for drug-drug interactions',
        'phase': 2,
        'phase_name': 'Safety Checks',
        'order': 1
    },
    'SAFETY_MONITOR_CONTRAINDICATION_CHECK': {
        'title': 'Contraindication Check',
        'icon': 'fa-ban',
        'description': 'Checking allergies and contraindications',
        'phase': 2,
        'phase_name': 'Safety Checks',
        'order': 2
    },
    'SAFETY_MONITOR_DOSING_ANALYSIS': {
        'title': 'Dosage Validation',
        'icon': 'fa-calculator',
        'description': 'Verifying appropriate dosing',
        'phase': 2,
        'phase_name': 'Safety Checks',
        'order': 3
    },
    'SAFETY_MONITOR_GUIDELINES_CHECK': {
        'title': 'Guidelines Review',
        'icon': 'fa-book-medical',
        'description': 'Checking clinical guidelines',
        'phase': 2,
        'phase_name': 'Safety Checks',
        'order': 4
    },
    'SAFETY_MONITOR_PHARMACOLOGY_CHECK': {
        'title': 'Pharmacology Analysis',
        'icon': 'fa-flask',
        'description': 'Reviewing drug mechanisms and interactions',
        'phase': 2,
        'phase_name': 'Safety Checks',
        'order': 5
    },
    'SAFETY_MONITOR_EHR_HISTORY_CHECK': {
        'title': 'Historical EHR Review',
        'icon': 'fa-history',
        'description': 'Analyzing patient history patterns',
        'phase': 2,
        'phase_name': 'Safety Checks',
        'order': 6
    },
    'SAFETY_MONITOR_LLM_REASONING': {
        'title': 'AI Safety Reasoning',
        'icon': 'fa-brain',
        'description': 'Using AI to analyze complex safety scenarios',
        'phase': 3,
        'phase_name': 'Intelligent Analysis',
        'order': 1
    },
    'SAFETY_MONITOR_FINAL_ASSESSMENT': {
        'title': 'Final Assessment',
        'icon': 'fa-check-circle',
        'description': 'Generating safety recommendations',
        'phase': 3,
        'phase_name': 'Intelligent Analysis',
        'order': 2
    },
    'SAFETY_MONITOR_COMPLETED': {
        'title': 'Safety Check Complete',
        'icon': 'fa-check-double',
        'description': 'All safety checks completed',
        'phase': 3,
        'phase_name': 'Intelligent Analysis',
        'order': 3
    }
}

def render_safety_step_card(step_data: dict, state: str = None) -> str:
    """Render a single safety step card with modern styling."""
    import html
    
    status = state if state else step_data.get('status', 'pending')
    title = html.escape(step_data.get('title', 'Unknown Step'))
    description = html.escape(step_data.get('description', ''))
    icon = step_data.get('icon', 'fa-circle')
    
    # Determine icon based on status
    if status == 'active':
        icon_html = f'<i class="fas {icon}"></i>'
        status_text = 'In progress'
    elif status == 'completed':
        icon_html = '<i class="fas fa-check"></i>'
        status_text = 'Complete'
    elif status == 'failed':
        icon_html = '<i class="fas fa-times"></i>'
        status_text = 'Failed'
    elif status == 'skipped':
        icon_html = '<i class="fas fa-info-circle"></i>'
        status_text = 'Not relevant'
    else:  # pending
        icon_html = f'<i class="fas {icon}"></i>'
        status_text = ''
    
    # Add AI sparkle icon for active steps
    ai_indicator = ''
    if status == 'active':
        ai_indicator = '<i class="fas fa-sparkles" style="position: absolute; top: -8px; right: -8px; color: #3b82f6; font-size: 0.875rem; animation: sparkle-icon 1.5s ease-in-out infinite;"></i>'
    
    status_div = f'<div class="step-status">{html.escape(status_text)}</div>' if status_text else ''
    
    html_output = f'<div class="step-card {status}" style="position: relative;"><div class="step-icon">{icon_html}</div>{ai_indicator}<div class="step-content"><div class="step-title">{title}</div><div class="step-description">{description}</div></div>{status_div}</div>'
    
    return html_output

def render_safety_phase_group(phase_num: int, phase_name: str, steps: list, completed_count: int = 0) -> str:
    """Render a phase group with header and step cards."""
    import html
    
    total_steps = len(steps)
    progress_text = f"{completed_count} of {total_steps} complete" if total_steps > 0 else ""
    
    phase_descriptions = {
        1: "Initializing safety monitor and preparing prescription data",
        2: "Running comprehensive safety checks on all prescriptions",
        3: "Using AI to analyze complex scenarios and generate recommendations"
    }
    
    description = phase_descriptions.get(phase_num, "")
    steps_html = '\n'.join(steps)
    description_html = f'<div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.5rem;">{html.escape(description)}</div>' if description else ''
    
    html_output = f'<div class="phase-group"><div class="phase-header"><div class="phase-title" style="display: flex; align-items: center; gap: 0.5rem;"><i class="fas fa-sparkles" style="color: #3b82f6; font-size: 0.9rem;"></i>Phase {phase_num}: {html.escape(phase_name)}</div><div class="phase-progress">{html.escape(progress_text)}</div>{description_html}</div>{steps_html}</div>'
    
    return html_output

def translate_safety_message(message: str) -> dict:
    """Translate safety monitor messages to step information."""
    message_upper = message.upper()
    
    # Map messages to step keys
    for step_key in SAFETY_STEP_DEFINITIONS.keys():
        if step_key in message_upper:
            step_info = SAFETY_STEP_DEFINITIONS[step_key].copy()
            
            # Determine status
            if 'STARTED' in message_upper or 'CHECKING' in message_upper:
                step_info['status'] = 'active'
            elif 'COMPLETED' in message_upper:
                step_info['status'] = 'completed'
            elif 'FAILED' in message_upper or 'ERROR' in message_upper:
                step_info['status'] = 'failed'
            else:
                step_info['status'] = 'active'
            
            return step_info
    
    # Handle SAFETY_CHECKING_[drug_name] pattern
    if 'SAFETY_CHECKING_' in message_upper:
        step_info = SAFETY_STEP_DEFINITIONS['SAFETY_CHECKING'].copy()
        step_info['status'] = 'active'
        return step_info
    
    return None

def render_safety_progress(container, states):
    """Render safety monitor progress."""
    phase_1_steps = []
    phase_2_steps = []
    phase_3_steps = []
    
    phase_1_completed = 0
    phase_2_completed = 0
    phase_3_completed = 0
    
    phase_1_items = []
    phase_2_items = []
    phase_3_items = []
    
    for step_key, step_def in SAFETY_STEP_DEFINITIONS.items():
        state = states.get(step_key, 'pending')
        
        if state == 'pending':
            phase = step_def['phase']
            phase_has_activity = any(
                states.get(k, 'pending') != 'pending' 
                for k, v in SAFETY_STEP_DEFINITIONS.items() 
                if v['phase'] == phase
            )
            if not phase_has_activity:
                continue
        
        step_def_copy = step_def.copy()
        step_def_copy['status'] = state
        card_html = render_safety_step_card(step_def_copy, state)
        order = step_def.get('order', 999)
        
        if step_def['phase'] == 1:
            phase_1_items.append((order, card_html, state))
            if state == 'completed':
                phase_1_completed += 1
        elif step_def['phase'] == 2:
            phase_2_items.append((order, card_html, state))
            if state == 'completed':
                phase_2_completed += 1
        elif step_def['phase'] == 3:
            phase_3_items.append((order, card_html, state))
            if state == 'completed':
                phase_3_completed += 1
    
    phase_1_steps = [html_str for _, html_str, _ in sorted(phase_1_items)]
    phase_2_steps = [html_str for _, html_str, _ in sorted(phase_2_items)]
    phase_3_steps = [html_str for _, html_str, _ in sorted(phase_3_items)]
    
    html_parts = []
    if phase_1_steps:
        html_parts.append(render_safety_phase_group(1, 'Initialization', phase_1_steps, phase_1_completed))
    if phase_2_steps:
        html_parts.append(render_safety_phase_group(2, 'Safety Checks', phase_2_steps, phase_2_completed))
    if phase_3_steps:
        html_parts.append(render_safety_phase_group(3, 'Intelligent Analysis', phase_3_steps, phase_3_completed))
    
    container.markdown('\n'.join(html_parts), unsafe_allow_html=True)

def run_safety_check(doctor_decision, patient_data, progress_container=None, step_states=None):
    """Run safety check on prescriptions using the Safety Monitor Agent"""
    import sys
    import os
    
    # Add parent directory to path to import agent modules
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from agent.orchestrator import run_safety_monitor
        
        # Extract patient_id from patient_data
        patient_id = patient_data.get('patient_id', 'P001')
        
        # Convert patient_data format to patient_context format expected by agent
        patient_context = {
            'EHR': {
                'demographics': patient_data.get('demographics', {}),
                'conditions': [{'name': c} if isinstance(c, str) else c for c in patient_data.get('conditions', [])],
                'allergies': [
                    {'name': a, 'allergen': a} if isinstance(a, str) else a 
                    for a in patient_data.get('allergies', [])
                ]
            },
            'LABS': {
                'results': [
                    {'test': k, 'value': v, 'unit': ''} 
                    for k, v in patient_data.get('labs', {}).items()
                ]
            },
            'MEDS': {
                'active': [
                    {'name': m} if isinstance(m, str) else m 
                    for m in patient_data.get('medications', [])
                ]
            }
        }
        
        # Progress callback for emit
        def emit(message):
            if progress_container and step_states is not None:
                # Translate message to step info
                step_info = translate_safety_message(message)
                
                if step_info:
                    step_key = None
                    message_upper = message.upper()
                    
                    # Find matching step key
                    for key in SAFETY_STEP_DEFINITIONS.keys():
                        if key in message_upper:
                            step_key = key
                            break
                    
                    if not step_key and 'SAFETY_CHECKING_' in message_upper:
                        step_key = 'SAFETY_CHECKING'
                    
                    if step_key:
                        # Update step state
                        if 'COMPLETED' in message_upper:
                            step_states[step_key] = 'completed'
                            # Mark previous active as completed
                            for other_key in step_states:
                                if other_key != step_key and step_states[other_key] == 'active':
                                    step_states[other_key] = 'completed'
                        elif 'FAILED' in message_upper or 'ERROR' in message_upper:
                            step_states[step_key] = 'failed'
                        elif 'STARTED' in message_upper or 'CHECKING' in message_upper:
                            # Mark previous active as completed
                            for other_key in step_states:
                                if other_key != step_key and step_states[other_key] == 'active':
                                    step_states[other_key] = 'completed'
                            step_states[step_key] = 'active'
                        
                        # Render progress
                        render_safety_progress(progress_container, step_states)
                        time.sleep(0.3)  # Small delay for visual effect
        
        # Run the actual safety monitor agent
        safety_result = run_safety_monitor(patient_id, doctor_decision, patient_context, emit)
        
        # Convert agent warnings format to frontend format
        warnings = []
        for warning in safety_result.get('warnings', []):
            warnings.append({
                'drug_name': warning.get('drug_name', ''),
                'severity': warning.get('severity', 'medium'),
                'message': warning.get('message', ''),
                'recommendation': warning.get('recommendation', ''),
                'category': warning.get('warning_type', 'general'),
                'source': warning.get('source', '')
            })
        
        return {
            'status': safety_result.get('status', 'completed'),
            'warnings': warnings,
            'alternatives': safety_result.get('alternatives', []),
            'summary': safety_result.get('summary', 'Safety analysis completed'),
            'recommendations': safety_result.get('recommendations', []),
            'llm_insights': safety_result.get('llm_insights', [])
        }
        
    except Exception as e:
        # Fallback to basic check if agent fails
        import traceback
        print(f"Safety monitor agent error: {e}")
        print(traceback.format_exc())
        
        # Return basic error response
        return {
            'status': 'error',
            'warnings': [{
                'drug_name': 'System',
                'severity': 'medium',
                'message': f'Safety check encountered an error: {str(e)}',
                'recommendation': 'Please review prescriptions manually',
                'category': 'system_error'
            }],
            'alternatives': [],
            'summary': f'Safety check failed: {str(e)}'
        }

def main():
    """Main application function"""
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🩺 Doctor Decision & Prescription Management</h1>
        <p>Review patient data and enter treatment decisions with safety checks</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Patient Selection
    st.markdown("### 👤 Patient Selection")
    
    # Load patient database
    database = load_patient_database()
    patients = database.get('patients', [])
    
    if patients:
        # Create patient options for dropdown
        patient_options = {}
        for patient in patients:
            display_name = f"{patient['patient_id']} - {patient['name']} ({patient['demographics']['age']}yo {patient['demographics']['gender']})"
            patient_options[display_name] = patient['patient_id']
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Patient selector
            selected_patient_display = st.selectbox(
                "Select Patient:",
                options=list(patient_options.keys()),
                index=0,  # Default to first patient
                key="patient_selector"
            )
        
        with col2:
            # Demo button for P001 (Ibuprofen scenario)
            if st.button("🎯 Demo P001", help="Load P001 for Ibuprofen safety demo"):
                selected_patient_display = "P001 - John Smith (68yo Male)"
        
        selected_patient_id = patient_options[selected_patient_display]
        
        # Load selected patient data
        patient_data = load_patient_data(selected_patient_id)
    else:
        st.warning("⚠️ No patients found in database. Using default patient data.")
        patient_data = load_patient_data()
    
    st.session_state['patient_data'] = patient_data
    
    # Patient information sidebar
    with st.sidebar:
        st.markdown("### 👤 Patient Information")
        st.write(f"**Patient ID:** {patient_data['patient_id']}")
        if 'name' in patient_data:
            st.write(f"**Name:** {patient_data['name']}")
        st.write(f"**Age:** {patient_data['demographics']['age']}")
        st.write(f"**Gender:** {patient_data['demographics']['gender']}")
        
        if 'visit_reason' in patient_data:
            st.markdown("### 🏥 Visit Reason")
            st.write(patient_data['visit_reason'])
        
        st.markdown("### 🏥 Current Conditions")
        for condition in patient_data['conditions']:
            st.write(f"• {condition}")
        
        st.markdown("### ⚠️ Allergies")
        for allergy in patient_data['allergies']:
            st.write(f"• {allergy}")
        
        st.markdown("### 💊 Current Medications")
        for med in patient_data['medications']:
            st.write(f"• {med}")
        
        st.markdown("### 🧪 Recent Labs")
        for lab, value in patient_data['labs'].items():
            st.write(f"**{lab}:** {value}")
    
    # Main content
    st.markdown("### 📋 Treatment Plan")
    
    # Prescriptions section
    st.markdown("#### 💊 Prescriptions & Medications")
    
    # Add prescription button
    col_add, col_info = st.columns([1, 3])
    with col_add:
        if st.button("➕ Add Prescription", type="secondary", use_container_width=True):
            st.session_state['prescriptions'].append({
                'name': '',
                'dose': '',
                'frequency': 'once daily',
                'duration': '',
                'instructions': ''
            })
            st.rerun()
    
    with col_info:
        st.caption(f"📋 {len(st.session_state['prescriptions'])} prescription(s) added")
    
    # Display prescriptions
    for i, prescription in enumerate(st.session_state['prescriptions']):
        with st.container():
            st.markdown(f"**Prescription {i+1}**")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                prescription['name'] = st.text_input(
                    "Drug Name",
                    value=prescription['name'],
                    key=f"drug_name_{i}",
                    placeholder="e.g., Metformin, Lisinopril"
                )
            
            with col2:
                prescription['dose'] = st.text_input(
                    "Dose",
                    value=prescription['dose'],
                    key=f"dose_{i}",
                    placeholder="e.g., 500mg, 10mg"
                )
            
            with col3:
                prescription['frequency'] = st.selectbox(
                    "Frequency",
                    options=["once daily", "twice daily", "three times daily", "four times daily", "as needed"],
                    index=0 if not prescription['frequency'] else ["once daily", "twice daily", "three times daily", "four times daily", "as needed"].index(prescription['frequency']) if prescription['frequency'] in ["once daily", "twice daily", "three times daily", "four times daily", "as needed"] else 0,
                    key=f"frequency_{i}"
                )
            
            col4, col5 = st.columns([1, 1])
            
            with col4:
                prescription['duration'] = st.text_input(
                    "Duration",
                    value=prescription['duration'],
                    key=f"duration_{i}",
                    placeholder="e.g., 7 days, 30 days, ongoing"
                )
            
            with col5:
                if st.button("🗑️ Remove", key=f"remove_{i}", type="secondary", use_container_width=True):
                    if len(st.session_state['prescriptions']) > 0:
                        st.session_state['prescriptions'].pop(i)
                        st.rerun()
            
            prescription['instructions'] = st.text_area(
                "Special Instructions",
                value=prescription['instructions'],
                key=f"instructions_{i}",
                placeholder="e.g., Take with food, Monitor blood pressure"
            )
            
            st.markdown("---")
    
    # Treatment notes
    st.markdown("#### 📋 Treatment Plan Notes")
    treatment_notes = st.text_area(
        "Additional Treatment Notes",
        value=st.session_state.get('treatment_notes', ''),
        placeholder="Enter any additional treatment decisions, follow-up plans, or clinical notes...",
        key="treatment_notes"
    )
    
    # Treatment notes are automatically stored in session state by the widget
    
    # Action buttons
    col_submit, col_clear = st.columns([1, 1])
    
    with col_submit:
        submit_decision = st.button("💊 Prescribe", type="primary", use_container_width=True)
    
    with col_clear:
        if st.button("🗑️ Clear Form", use_container_width=True):
            st.session_state['prescriptions'] = []
            st.session_state['doctor_decision'] = None
            st.session_state['safety_result'] = None
            st.rerun()
    
    # Handle prescription submission
    if submit_decision:
        if not st.session_state['prescriptions'] or not any(p.get('name') for p in st.session_state['prescriptions']):
            st.warning("⚠️ Please add at least one prescription before prescribing.")
        else:
            # Prepare doctor decision
            doctor_decision = {
                'prescriptions': [p for p in st.session_state['prescriptions'] if p.get('name')],
                'treatment_notes': treatment_notes,
                'timestamp': datetime.now().isoformat()
            }
            
            # Store in session state
            st.session_state['doctor_decision'] = doctor_decision
            
            # Run safety check using Safety Monitor Agent with progress display
            st.markdown("")
            st.markdown("""
            <div style='display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;'>
                <i class="fas fa-shield-halved" style='color: #dc2626; font-size: 1.5rem; animation: sparkle 2s ease-in-out infinite;'></i>
                <h3 style='margin: 0; display: inline;'>🛡️ Safety Monitor Analysis in Progress</h3>
                <i class="fas fa-shield-halved" style='color: #dc2626; font-size: 1.5rem; animation: sparkle 2s ease-in-out infinite 0.5s;'></i>
            </div>
            <style>
            @keyframes sparkle {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.6; transform: scale(1.2); }
            }
            </style>
            """, unsafe_allow_html=True)
            st.markdown("<p style='color: #64748b; margin-bottom: 1.5rem;'>Comprehensive safety analysis: checking interactions, contraindications, guidelines, pharmacology, and patient history.</p>", unsafe_allow_html=True)
            
            # Progress display container
            progress_display_container = st.empty()
            
            # Track step states
            step_states = {}
            for step_key in SAFETY_STEP_DEFINITIONS.keys():
                step_states[step_key] = 'pending'
            
            # Initial render
            render_safety_progress(progress_display_container, step_states)
            
            safety_result = run_safety_check(doctor_decision, patient_data, progress_display_container, step_states)
            st.session_state['safety_result'] = safety_result
            
            # Check if we have critical/high warnings for dramatic alert
            warnings = safety_result.get('warnings', [])
            critical_warnings = [w for w in warnings if w.get('severity') == 'critical']
            high_warnings = [w for w in warnings if w.get('severity') == 'high']
            
            if critical_warnings or high_warnings:
                # Set flag to show dramatic alert
                st.session_state['show_dramatic_alert'] = True
                st.rerun()
            else:
                st.success("✅ Prescription appears safe!")
                st.rerun()
    
    # Display safety results if available
    if 'safety_result' in st.session_state and st.session_state['safety_result']:
        safety_result = st.session_state['safety_result']
        
        if safety_result.get('status') == 'completed':
            warnings = safety_result.get('warnings', [])
            
            if not warnings:
                st.success("✅ All prescriptions appear safe based on current patient data.")
            else:
                # Check if we should show dramatic popup automatically
                critical_warnings = [w for w in warnings if w['severity'] == 'critical']
                high_warnings = [w for w in warnings if w['severity'] == 'high']
                
                # Show dramatic alert if we have critical/high warnings
                if (critical_warnings or high_warnings) and st.session_state.get('show_dramatic_alert', False):
                    # Create prominent alert section (Streamlit-friendly approach)
                    st.markdown("""
                    <div style="
                        background: linear-gradient(135deg, #dc2626, #ef4444);
                        color: white;
                        padding: 2rem;
                        border-radius: 15px;
                        margin: 2rem 0;
                        box-shadow: 0 10px 30px rgba(220, 38, 38, 0.4);
                        border: 4px solid #991b1b;
                        animation: pulse-alert 2s ease-in-out infinite;
                    ">
                        <div style="text-align: center; font-size: 2rem; font-weight: bold; margin-bottom: 1.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                            🚨 CRITICAL SAFETY ALERT 🚨
                        </div>
                    </div>
                    <style>
                    @keyframes pulse-alert {
                        0%, 100% { box-shadow: 0 10px 30px rgba(220, 38, 38, 0.4); }
                        50% { box-shadow: 0 10px 40px rgba(220, 38, 38, 0.6); }
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Display critical warnings
                    if critical_warnings:
                        st.markdown("### 🚨 CRITICAL SAFETY ISSUES")
                        for warning in critical_warnings:
                            st.error(f"**🚨 {warning['drug_name']}**")
                            st.error(f"**Issue:** {warning['message']}")
                            st.warning(f"**⚠️ RECOMMENDATION:** {warning['recommendation']}")
                            if warning.get('source'):
                                st.caption(f"*Source: {warning['source']}*")
                            st.markdown("---")
                    
                    # Display high warnings
                    if high_warnings:
                        st.markdown("### ⚠️ HIGH PRIORITY WARNINGS")
                        for warning in high_warnings:
                            st.warning(f"**⚠️ {warning['drug_name']}**")
                            st.warning(f"**Issue:** {warning['message']}")
                            st.info(f"**⚠️ RECOMMENDATION:** {warning['recommendation']}")
                            if warning.get('source'):
                                st.caption(f"*Source: {warning['source']}*")
                            st.markdown("---")
                    
                    # Display alternatives
                    alternatives = safety_result.get('alternatives', [])
                    if alternatives:
                        st.markdown("### 🔄 ALTERNATIVE SUGGESTIONS")
                        for alt in alternatives:
                            st.info(f"**💡 Consider Alternative**")
                            st.info(f"**Instead of:** {alt.get('original_drug', 'Unknown')}")
                            st.info(f"**Try:** {alt.get('alternative', 'Unknown')}")
                            st.info(f"**Reason:** {alt.get('reason', 'Safety concern')}")
                            st.markdown("---")
                    
                    # Close button - properly placed
                    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                    with col_btn2:
                        if st.button("✅ ACKNOWLEDGE & DISMISS ALERT", type="primary", use_container_width=True, key="acknowledge_alert_btn"):
                            st.session_state['show_dramatic_alert'] = False
                            st.rerun()
                    
                    st.markdown("---")
                    st.markdown("### 📋 Detailed Safety Analysis")
                
                # Display warnings by severity (regular display)
                critical_warnings = [w for w in warnings if w['severity'] == 'critical']
                high_warnings = [w for w in warnings if w['severity'] == 'high']
                medium_warnings = [w for w in warnings if w['severity'] == 'medium']
                low_warnings = [w for w in warnings if w['severity'] == 'low']
                
                # Critical warnings
                if critical_warnings:
                    st.error("🚨 **CRITICAL SAFETY ISSUES**")
                    for warning in critical_warnings:
                        st.markdown(f"""
                        <div class="safety-warning">
                            <strong style='color: #dc2626;'>{warning['drug_name']}</strong><br>
                            {warning['message']}<br>
                            <em style='color: #991b1b;'>{warning['recommendation']}</em>
                        </div>
                        """, unsafe_allow_html=True)
                
                # High warnings
                if high_warnings:
                    st.warning("⚠️ **HIGH PRIORITY WARNINGS**")
                    for warning in high_warnings:
                        st.markdown(f"""
                        <div style='
                            background: #fef3c7;
                            border-left: 4px solid #d97706;
                            padding: 1rem;
                            margin: 0.5rem 0;
                            border-radius: 8px;
                        '>
                            <strong style='color: #d97706;'>{warning['drug_name']}</strong><br>
                            {warning['message']}<br>
                            <em style='color: #92400e;'>{warning['recommendation']}</em>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Medium warnings
                if medium_warnings:
                    st.info("ℹ️ **MEDIUM PRIORITY NOTES**")
                    for warning in medium_warnings:
                        st.markdown(f"""
                        <div class="safety-info">
                            <strong style='color: #2563eb;'>{warning['drug_name']}</strong><br>
                            {warning['message']}<br>
                            <em style='color: #1e40af;'>{warning['recommendation']}</em>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Low warnings
                if low_warnings:
                    st.info("📝 **ADDITIONAL NOTES**")
                    for warning in low_warnings:
                        st.markdown(f"""
                        <div style='
                            background: #f8fafc;
                            border-left: 4px solid #64748b;
                            padding: 1rem;
                            margin: 0.5rem 0;
                            border-radius: 8px;
                        '>
                            <strong style='color: #64748b;'>{warning['drug_name']}</strong><br>
                            {warning['message']}<br>
                            <em style='color: #475569;'>{warning['recommendation']}</em>
                        </div>
                        """, unsafe_allow_html=True)
        
        elif safety_result.get('status') == 'error':
            st.error(f"❌ Safety analysis failed: {safety_result.get('summary', 'Unknown error')}")
        else:
            st.info(safety_result.get('summary', 'No safety analysis available'))
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #94a3b8; font-size: 0.8rem; padding: 1rem 0;'>
        Doctor Decision & Prescription Management Service | Port 8503<br>
        Powered by Streamlit | Built for Clinical Safety
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
