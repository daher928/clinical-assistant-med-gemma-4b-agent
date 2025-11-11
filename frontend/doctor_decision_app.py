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

def run_safety_check(doctor_decision, patient_data):
    """Run safety check on prescriptions"""
    # Simulate safety check
    time.sleep(2)  # Simulate processing time
    
    warnings = []
    alternatives = []
    
    # Get patient data
    current_meds = patient_data.get('medications', [])
    new_meds = [p['name'] for p in doctor_decision['prescriptions']]
    conditions = patient_data.get('conditions', [])
    allergies = patient_data.get('allergies', [])
    labs = patient_data.get('labs', {})
    
    # DEMO SCENARIO: Ibuprofen + ACE inhibitor + Kidney Disease
    for prescription in doctor_decision['prescriptions']:
        drug_name = prescription['name'].lower()
        
        # Check for Ibuprofen (NSAID) with ACE inhibitor and kidney disease
        if 'ibuprofen' in drug_name or 'nsaid' in drug_name:
            # Check if patient is on ACE inhibitor
            ace_inhibitor = any('lisinopril' in med.lower() or 'ace inhibitor' in med.lower() for med in current_meds)
            kidney_disease = any('kidney' in condition.lower() or 'ckd' in condition.lower() for condition in conditions)
            heart_failure = any('heart failure' in condition.lower() or 'chf' in condition.lower() for condition in conditions)
            
            if ace_inhibitor and (kidney_disease or heart_failure):
                warnings.append({
                    'drug_name': prescription['name'],
                    'severity': 'high',
                    'message': 'High-risk combination detected: Ibuprofen (NSAID) may worsen kidney function and heart failure in patients on ACE inhibitors',
                    'recommendation': 'Recommend alternative pain relief such as Acetaminophen. Monitor kidney function closely if NSAID is necessary.',
                    'category': 'Drug Interaction & Contraindication'
                })
                
                # Add alternative suggestion
                alternatives.append({
                    'original_drug': prescription['name'],
                    'alternative': 'Acetaminophen 500-1000mg every 6-8 hours',
                    'reason': 'Safer for patients with kidney disease and heart failure'
                })
        
        # Check for kidney function with NSAIDs
        if 'ibuprofen' in drug_name or 'nsaid' in drug_name:
            egfr = labs.get('eGFR', 0)
            if egfr < 60:
                warnings.append({
                    'drug_name': prescription['name'],
                    'severity': 'high',
                    'message': f'Patient has reduced kidney function (eGFR: {egfr}). NSAIDs can further impair kidney function.',
                    'recommendation': 'Consider alternative pain management. If NSAID necessary, use lowest effective dose and monitor kidney function.',
                    'category': 'Kidney Function'
                })
        
        # Check for heart failure with NSAIDs
        if 'ibuprofen' in drug_name or 'nsaid' in drug_name:
            if any('heart failure' in condition.lower() or 'chf' in condition.lower() for condition in conditions):
                warnings.append({
                    'drug_name': prescription['name'],
                    'severity': 'high',
                    'message': 'NSAIDs can worsen heart failure by causing fluid retention and reducing effectiveness of heart failure medications.',
                    'recommendation': 'Avoid NSAIDs in heart failure patients. Consider Acetaminophen or topical pain relief.',
                    'category': 'Heart Failure'
                })
    
    # Check for allergies
    for prescription in doctor_decision['prescriptions']:
        drug_name = prescription['name'].lower()
        for allergy in allergies:
            if allergy.lower() in drug_name or drug_name in allergy.lower():
                warnings.append({
                    'drug_name': prescription['name'],
                    'severity': 'critical',
                    'message': f'Patient has allergy to {allergy}',
                    'recommendation': 'DO NOT PRESCRIBE - Consider alternative',
                    'category': 'Allergy'
                })
    
    # Check for other contraindications
    for prescription in doctor_decision['prescriptions']:
        drug_name = prescription['name'].lower()
        
        # Check for Metformin in kidney disease
        if 'metformin' in drug_name:
            egfr = labs.get('eGFR', 0)
            if egfr < 45:
                warnings.append({
                    'drug_name': prescription['name'],
                    'severity': 'high',
                    'message': f'Metformin contraindicated in severe kidney disease (eGFR: {egfr} < 45)',
                    'recommendation': 'Consider alternative diabetes medication or reduce dose with close monitoring',
                    'category': 'Contraindication'
                })
    
    return {
        'status': 'completed',
        'warnings': warnings,
        'alternatives': alternatives,
        'summary': f'Safety analysis completed with {len(warnings)} warnings'
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
            
            # Run safety check with dramatic thinking
            with st.spinner("🧠 Analyzing prescription safety..."):
                time.sleep(2)  # Dramatic thinking pause
                safety_result = run_safety_check(doctor_decision, patient_data)
                st.session_state['safety_result'] = safety_result
                
                # Check if we have critical/high warnings for dramatic popup
                warnings = safety_result.get('warnings', [])
                critical_warnings = [w for w in warnings if w['severity'] == 'critical']
                high_warnings = [w for w in warnings if w['severity'] == 'high']
                
                if critical_warnings or high_warnings:
                    # Set flag to show dramatic popup
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
                
                # Show dramatic popup automatically if we have critical/high warnings
                if (critical_warnings or high_warnings) and st.session_state.get('show_dramatic_alert', False):
                    # Create a dramatic alert using Streamlit components with custom styling
                    st.markdown("""
                    <div style="
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
                    ">
                        <div style="
                            background: white;
                            border: 4px solid #dc2626;
                            border-radius: 15px;
                            padding: 2rem;
                            max-width: 700px;
                            width: 90%;
                            max-height: 80vh;
                            overflow-y: auto;
                            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
                        ">
                            <div style="
                                background: linear-gradient(135deg, #dc2626, #ef4444);
                                color: white;
                                padding: 1.5rem;
                                margin: -2rem -2rem 2rem -2rem;
                                border-radius: 12px 12px 0 0;
                                text-align: center;
                                font-size: 1.8rem;
                                font-weight: bold;
                                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                            ">
                                🚨 CRITICAL SAFETY ALERT 🚨
                            </div>
                    """, unsafe_allow_html=True)
                    
                    # Display critical warnings
                    if critical_warnings:
                        st.markdown("### 🚨 CRITICAL SAFETY ISSUES")
                        for warning in critical_warnings:
                            st.error(f"**🚨 {warning['drug_name']}**")
                            st.error(f"**Issue:** {warning['message']}")
                            st.warning(f"**⚠️ RECOMMENDATION:** {warning['recommendation']}")
                            st.markdown("---")
                    
                    # Display high warnings
                    if high_warnings:
                        st.markdown("### ⚠️ HIGH PRIORITY WARNINGS")
                        for warning in high_warnings:
                            st.warning(f"**⚠️ {warning['drug_name']}**")
                            st.warning(f"**Issue:** {warning['message']}")
                            st.info(f"**⚠️ RECOMMENDATION:** {warning['recommendation']}")
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
                    
                    # Urgent Alert Info button
                    if st.button("🚨 URGENT ALERT INFO", type="primary", use_container_width=True):
                        st.session_state['show_dramatic_alert'] = False
                        st.rerun()
                    
                    # Acknowledge button
                    if st.button("🚨 ACKNOWLEDGE SAFETY ALERT", type="primary", use_container_width=True):
                        st.session_state['show_dramatic_alert'] = False
                        st.rerun()
                    
                    # Close the popup div
                    st.markdown("""
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Reset the alert flag
                    st.session_state['show_dramatic_alert'] = False
                    
                    # Also show regular warnings below
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
