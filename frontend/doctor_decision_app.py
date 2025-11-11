#!/usr/bin/env python3
"""
Doctor Decision & Prescription Management Service
Separate Streamlit app for handling doctor decisions and prescription safety checks.
Runs on port 8503
"""

import streamlit as st
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Any
import json as _json

# Add parent directory to path for imports (same as app.py)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Optional orchestrator & LLM imports
try:
    from agent.orchestrator import run_agent_standard, run_safety_monitor
    from llm.med_gemma_wrapper import MedGemmaLLM
    from config import Config
except Exception as e:
    print(f"⚠️ Import error (will use fallback): {e}")
    run_agent_standard = None
    run_safety_monitor = None
    MedGemmaLLM = None
    class Config:
        USE_MOCK_LLM = True

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
        with open('patient_database.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"patients": []}

def load_patient_data(patient_id=None):
    """Load patient data from the database"""
    if patient_id:
        try:
            with open('patient_database.json', 'r') as f:
                database = json.load(f)
                for patient in database.get('patients', []):
                    if patient['patient_id'] == patient_id:
                        return patient
        except FileNotFoundError:
            pass
    
    # Fallback to old patient_data.json for backward compatibility
    try:
        with open('patient_data.json', 'r') as f:
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
    with open('patient_data.json', 'w') as f:
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
        <h1>🩺 Clinician Demo — Diagnosis & Safety Helper</h1>
        <p>Simple, clear assistance for doctors and nurses</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar model toggle
    with st.sidebar:
        st.markdown("### ⚙️ Model Settings")
        use_mock = st.toggle("Use Mock LLM (fast)", value=getattr(Config, "USE_MOCK_LLM", True), help="Disable to use MedGemma if available")
        if hasattr(Config, "USE_MOCK_LLM"):
            Config.USE_MOCK_LLM = use_mock
    
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
            # Quick demo buttons
            if st.button("🎯 Demo P006 (Joint Pain)", help="Load Omar P006 (joint pain)"):
                selected_patient_display = next(k for k in patient_options if k.startswith("P006"))
            if st.button("🎯 Demo P007 (Chest Infection)", help="Load Omar P007 (cough, fever, chest pain)"):
                selected_patient_display = next(k for k in patient_options if k.startswith("P007"))
        
        selected_patient_id = patient_options[selected_patient_display]
        
        # Load selected patient data
        patient_data = load_patient_data(selected_patient_id)
    else:
        st.warning("⚠️ No patients found in database. Using default patient data.")
        patient_data = load_patient_data()
    
    st.session_state['patient_data'] = patient_data
    
    # Demo toggles
    st.markdown("### 🎛️ Demo Controls")
    col_demo1, col_demo2, col_demo3 = st.columns([1,1,2])
    with col_demo1:
        show_overlays = st.checkbox("Show overlay labels", value=True, help="Pin simple labels on screen for video")
    with col_demo2:
        plain_words = st.checkbox("Plain words", value=True, help="Use everyday words")
    with col_demo3:
        recording_mode = st.checkbox("Recording mode", value=False, help="Reduce motion for smooth recordings")
    
    if show_overlays:
        st.markdown("""
        <div style="
            position: sticky; top: 0.5rem; z-index: 999; 
            display: inline-block; padding: 0.4rem 0.8rem; 
            background: #e0f2fe; color: #075985; 
            border: 1px solid #7dd3fc; border-radius: 8px; margin-bottom: 0.5rem;">
            Overlay: Demo labels ON
        </div>
        """, unsafe_allow_html=True)
    
    # Tabs for the two helpers
    dx_tab, safety_tab = st.tabs(["🧠 Diagnosis Helper", "🛡️ Safety Helper"])
    
    # =========================
    # Diagnosis Helper (Tab 1)
    # =========================
    with dx_tab:
        st.markdown("#### 🧭 Agent Progress")
        # Doctor-entered complaint (prefilled from visit_reason)
        complaint = st.text_area(
            "Chief complaint (doctor enters)",
            value=patient_data.get('visit_reason', ''),
            placeholder="e.g., Cough and fever for 3 days with chest pain on breathing",
            help="Write the patient's words briefly"
        )
        # Initialize state
        if 'dx_steps' not in st.session_state:
            st.session_state['dx_steps'] = {"EHR":"pending","LABS":"pending","MEDS":"pending","IMAGING":"pending","GUIDE":"pending","LLM":"pending"}
        if 'dx_logs' not in st.session_state:
            st.session_state['dx_logs'] = []
        if 'dx_result' not in st.session_state:
            st.session_state['dx_result'] = None
        if 'dx_observations' not in st.session_state:
            st.session_state['dx_observations'] = {}
        if 'dx_facts' not in st.session_state:
            st.session_state['dx_facts'] = {"facts": [], "sources": [], "next_step": ""}
        
        def render_step(state, label):
            klass = {"pending":"step-pending","active":"step-active","done":"step-complete","error":"step-error"}.get(state,"step-pending")
            st.markdown(f"<div class='progress-step {klass}'>{label}</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='progress-container'>", unsafe_allow_html=True)
        render_step(st.session_state['dx_steps']["EHR"], "1) Pull today's vitals + meds + allergy")
        render_step(st.session_state['dx_steps']["IMAGING"], "2) Find last chest report + doctor note")
        render_step(st.session_state['dx_steps']["LLM"], "3) Make the 3-facts card")
        render_step(st.session_state['dx_steps']["LLM"], "4) Suggest next safe step")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Controls
        col_run_dx, col_spacer = st.columns([1,3])
        with col_run_dx:
            run_dx = st.button("▶ Run Diagnosis", type="primary", use_container_width=True)
        
        # Emit mapping
        def emit(msg: str):
            st.session_state['dx_logs'].append(f"{datetime.now().strftime('%H:%M:%S')} - {msg}")
            m = msg.upper()
            def set_step(k,v): st.session_state['dx_steps'][k]=v
            if "FETCH_EHR_STARTED" in m: set_step("EHR","active")
            if "FETCH_EHR_COMPLETED" in m: set_step("EHR","done")
            if "FETCH_EHR_FAILED" in m: set_step("EHR","error")
            if "FETCH_LABS_STARTED" in m: set_step("LABS","active")
            if "FETCH_LABS_COMPLETED" in m: set_step("LABS","done")
            if "FETCH_LABS_FAILED" in m: set_step("LABS","error")
            if "FETCH_MEDS_STARTED" in m: set_step("MEDS","active")
            if "FETCH_MEDS_COMPLETED" in m: set_step("MEDS","done")
            if "FETCH_MEDS_FAILED" in m: set_step("MEDS","error")
            if "FETCH_IMAGING_STARTED" in m: set_step("IMAGING","active")
            if "FETCH_IMAGING_COMPLETED" in m: set_step("IMAGING","done")
            if "FETCH_IMAGING_FAILED" in m: set_step("IMAGING","error")
            if "SEARCH_GUIDELINES_STARTED" in m: set_step("GUIDE","active")
            if "SEARCH_GUIDELINES_COMPLETED" in m: set_step("GUIDE","done")
            if "SEARCH_GUIDELINES_FAILED" in m: set_step("GUIDE","error")
            if "SYNTHESIS_STARTED" in m: set_step("LLM","active")
            if "SYNTHESIS_COMPLETED" in m: set_step("LLM","done")
            if "SYNTHESIS_FAILED" in m: set_step("LLM","error")
        
        # Facts via LLM JSON (graceful fallback)
        def extract_facts_via_llm(summary_text: str, observations: Dict) -> Dict[str, Any]:
            try:
                if MedGemmaLLM is None:
                    return {}
                llm = MedGemmaLLM()
                system = "You are a clinical assistant. Output ONLY valid JSON."
                user = (
                    "From the clinical summary below, extract exactly 3 short, plain words facts "
                    "and one next step. Include tiny source labels like EHR/LABS/IMAGING/GUIDE.\n"
                    "Return strictly as JSON: {\"facts\":[\"...\",\"...\",\"...\"],\"next_step\":\"...\",\"sources\":[\"...\",\"...\",\"...\"]}\n\n"
                    f"Clinical summary:\n{summary_text}\n"
                )
                text = llm.synthesize(system, user, observations)
                text = text.strip().strip("`")
                s = text.find("{"); e = text.rfind("}")
                if s != -1 and e != -1:
                    text = text[s:e+1]
                data = _json.loads(text)
                facts = data.get("facts", [])[:3]
                next_step = data.get("next_step", "")
                sources = data.get("sources", [])[:len(facts)]
                return {"facts": facts, "sources": sources, "next_step": next_step}
            except Exception:
                return {}
        
        def extract_facts_fallback(observations: Dict, pid: str) -> Dict[str, Any]:
            facts, sources = [], []
            ehr = observations.get("EHR", {})
            conditions = [c.get('name','') for c in ehr.get('conditions',[])]
            if pid == "P007":
                facts.append("Oxygen is 91% with fever"); sources.append("Vitals")
                if observations.get("IMAGING", {}).get("studies"): facts.append("New chest infection on today’s report"); sources.append("Imaging")
                if any('kidney' in c.lower() or 'ckd' in c.lower() for c in conditions): facts.append("Older patient with kidney problem"); sources.append("EHR")
                next_step = "Start treatment today. Check drug safety."
            else:
                if conditions: facts.append(f"Known conditions: {', '.join(conditions[:2])}"); sources.append("EHR")
                if observations.get("LABS", {}).get("results"): facts.append("Recent lab results available"); sources.append("LABS")
                facts.append(patient_data.get('visit_reason','Key finding ready')); sources.append("System")
                next_step = "Proceed with treatment planning and safety check."
            facts = (facts + ["Key finding ready"])[:3]
            sources = (sources + ["System"])[:3]
            return {"facts": facts, "sources": sources, "next_step": next_step}
        
        if run_dx:
            # reset
            st.session_state['dx_steps'] = {k:"pending" for k in st.session_state['dx_steps']}
            st.session_state['dx_logs'] = []
            st.session_state['dx_result'] = None
            st.session_state['dx_observations'] = {}
            st.session_state['dx_facts'] = {"facts": [], "sources": [], "next_step": ""}
            if run_agent_standard is None:
                st.error("⚠️ Agent not available. Check terminal for import errors. Make sure you're running from project root.")
                st.info("💡 Try: `cd /Users/ddaher/projects/clinical-assistant-agent && streamlit run frontend/doctor_decision_app.py`")
            else:
                with st.spinner("Running diagnosis agent..."):
                    try:
                        entered = complaint if isinstance(complaint, str) and complaint.strip() else patient_data.get('visit_reason','')
                        result, observations = run_agent_standard(patient_data['patient_id'], entered, emit)
                        st.session_state['dx_result'] = result
                        st.session_state['dx_observations'] = observations
                        fx = extract_facts_via_llm(result, observations) or extract_facts_fallback(observations, patient_data.get("patient_id",""))
                        st.session_state['dx_facts'] = fx
                        st.success("Diagnosis completed")
                    except Exception as e:
                        st.error(f"Diagnosis failed: {e}")
        
        # Render facts card if present
        if st.session_state['dx_facts']['facts']:
            st.markdown("""
            <div class='medical-card' style='border-left: 4px solid #0ea5e9;'>
              <div style='font-weight: 700; color: #075985; margin-bottom: 0.5rem;'>3 Facts</div>
            """, unsafe_allow_html=True)
            for f, s in zip(st.session_state['dx_facts']['facts'], st.session_state['dx_facts'].get('sources', [])):
                badge = f" <span class='badge badge-info'>Source</span> <span style='font-size: 0.8rem; color: #1e3a8a;'>{s}</span>" if s else ""
                st.markdown(f"- {f}{badge}", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            next_step = st.session_state['dx_facts'].get("next_step","Start treatment today. Check drug safety.")
            st.markdown(f"""
            <div class='medical-card' style='background: #ecfeff; border-left: 4px solid #06b6d4;'>
              <div style='font-weight: 700; color: #0e7490;'>Next step</div>
              <div style='color: #0e7490;'>{next_step}</div>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("➡ Go to Safety Helper", type="primary"):
            st.experimental_rerun()
    
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
    
    # =========================
    # Safety Helper (Tab 2)
    # =========================
    with safety_tab:
        # Main content
        st.markdown("### 📋 Treatment Plan")
        
        # Safety highlights for demo (plain language)
        if patient_data.get("patient_id") == "P007":
            st.markdown("""
            <div class='medical-card' style='border-left: 4px solid #ef4444;'>
              <div style='font-weight: 700; color: #991b1b; margin-bottom: 0.5rem;'>Red light: risky mix</div>
              <ul style='margin-top: 0;'>
                <li>Ibuprofen + kidney problem = higher risk</li>
                <li>Blood thinner pills = higher bleed risk with some antibiotics</li>
                <li>Use paracetamol (acetaminophen) for pain/fever</li>
                <li>Antibiotic suggestion: doxycycline — safe with penicillin allergy and blood thinner</li>
              </ul>
              <span class='badge badge-info'>Source</span>
            </div>
            """, unsafe_allow_html=True)
    
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
            
            # Run safety agent (uses observations from diagnosis if available)
            with st.spinner("🛡️ Running safety agent..."):
                try:
                    patient_context = st.session_state.get('dx_observations', {})
                    if run_safety_monitor is not None:
                        safety_result = run_safety_monitor(
                            patient_data['patient_id'],
                            doctor_decision,
                            patient_context,
                            lambda m: None
                        )
                    else:
                        # Fallback simple check
                        safety_result = run_safety_check(doctor_decision, patient_data)
                    st.session_state['safety_result'] = safety_result
                except Exception as e:
                    st.error(f"Safety agent failed: {e}")
                
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
    
    # Display safety results if available (outside tab to persist)
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
