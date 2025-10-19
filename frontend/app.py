"""
Streamlit Frontend for Clinical Assistant Agent.

Modern medical-grade UI with professional design.
Run with: streamlit run frontend/app.py
"""
import streamlit as st
import sys
import os
import json
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.orchestrator import run_agent
from config import Config


# Page configuration - Light theme enforced via .streamlit/config.toml
st.set_page_config(
    page_title="Clinical Decision Support System",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'About': "Clinical Decision Support System - AI-powered assistant for clinicians"
    }
)

# Professional Medical UI - Custom CSS
st.markdown("""
<style>
    /* Import professional fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Poppins:wght@400;500;600;700&display=swap');
    
    /* Global typography and base styles */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 16px;
        line-height: 1.6;
        color: #1e293b;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    /* Main container - Clean white background with subtle texture */
    .main {
        background: #ffffff;
        padding: 2.5rem 3rem;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    .block-container {
        padding: 1rem 2rem;
        max-width: 1400px;
    }
    
    /* Typography hierarchy */
    h1 {
        font-family: 'Poppins', sans-serif;
        color: #0f172a;
        font-weight: 700;
        font-size: 2.5rem;
        letter-spacing: -0.03em;
        margin-bottom: 0.5rem;
        line-height: 1.2;
    }
    
    h2 {
        font-family: 'Poppins', sans-serif;
        color: #1e293b;
        font-weight: 600;
        font-size: 1.75rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
        letter-spacing: -0.02em;
    }
    
    h3 {
        font-family: 'Inter', sans-serif;
        color: #334155;
        font-weight: 600;
        font-size: 1.25rem;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
        letter-spacing: -0.01em;
    }
    
    /* Card System - Elevated, clean design */
    .medical-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 10px 15px -3px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .medical-card:hover {
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05), 0 20px 25px -5px rgba(0, 0, 0, 0.08);
        transform: translateY(-2px);
        border-color: #cbd5e1;
    }
    
    /* Patient card - Professional gradient */
    .patient-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        color: white;
        border-radius: 20px;
        padding: 2.5rem;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    
    .patient-card::before {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
        border-radius: 50%;
        transform: translate(30%, -30%);
    }
    
    .patient-name {
        font-family: 'Poppins', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
        position: relative;
        z-index: 1;
    }
    
    .patient-id {
        font-size: 0.95rem;
        opacity: 0.8;
        font-weight: 500;
        position: relative;
        z-index: 1;
    }
    
    .patient-meta {
        display: flex;
        gap: 2.5rem;
        margin-top: 1.5rem;
        font-size: 1rem;
        position: relative;
        z-index: 1;
    }
    
    /* Status badge system */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        padding: 0.5rem 1rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 600;
        margin: 0.25rem;
        transition: all 0.2s ease;
        letter-spacing: 0.01em;
    }
    
    .status-success {
        background: #ecfdf5;
        color: #065f46;
        border: 1.5px solid #6ee7b7;
    }
    
    .status-warning {
        background: #fef3c7;
        color: #92400e;
        border: 1.5px solid #fcd34d;
    }
    
    .status-critical {
        background: #fee2e2;
        color: #991b1b;
        border: 1.5px solid #fca5a5;
    }
    
    .status-warning {
        background: #fef3c7;
        color: #92400e;
        border: 1px solid #fcd34d;
    }
    
    .status-error {
        background: #fee2e2;
        color: #991b1b;
        border: 1px solid #fca5a5;
    }
    
    .status-info {
        background: #dbeafe;
        color: #1e40af;
        border: 1px solid #93c5fd;
    }
    
    .status-processing {
        background: #e0e7ff;
        color: #3730a3;
        border: 1px solid #a5b4fc;
        animation: pulse 2s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Progress bar custom */
    .progress-container {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        margin: 1rem 0;
    }
    
    .progress-step {
        padding: 0.8rem 1.2rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        font-size: 0.9rem;
        transition: all 0.3s;
    }
    
    .step-pending {
        background: #f3f4f6;
        color: #6b7280;
        border-left: 3px solid #d1d5db;
    }
    
    .step-active {
        background: #dbeafe;
        color: #1e40af;
        border-left: 3px solid #3b82f6;
        font-weight: 600;
    }
    
    .step-complete {
        background: #dcfce7;
        color: #166534;
        border-left: 3px solid #22c55e;
    }
    
    .step-error {
        background: #fee2e2;
        color: #991b1b;
        border-left: 3px solid #ef4444;
    }
    
    /* Results container */
    .results-container {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        margin-top: 2rem;
    }
    
    /* Button System - Professional & Polished */
    .stButton > button {
        font-family: 'Inter', sans-serif;
        border-radius: 12px;
        font-weight: 600;
        font-size: 1rem;
        padding: 0.875rem 2rem;
        border: none;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        letter-spacing: 0.01em;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Primary button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
    }
    
    /* Select boxes - Modern dropdown */
    .stSelectbox > div > div {
        border-radius: 12px;
        border: 1.5px solid #e2e8f0;
        background: #ffffff;
        transition: all 0.2s ease;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #cbd5e1;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        background: #ffffff;
    }
    
    /* Text areas - Clean input fields */
    .stTextArea > div > div > textarea {
        border-radius: 12px;
        border: 1.5px solid #e2e8f0;
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        padding: 1rem;
        line-height: 1.6;
        transition: all 0.2s ease;
        background: #ffffff;
    }
    
    .stTextArea > div > div > textarea:hover {
        border-color: #cbd5e1;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        outline: none;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: white;
        border-radius: 12px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        color: #6b7280;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6;
        color: white;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #1e3a8a;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.9rem;
        font-weight: 600;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom badge */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-critical {
        background: #fef2f2;
        color: #991b1b;
        border: 1px solid #fca5a5;
    }
    
    .badge-warning {
        background: #fffbeb;
        color: #92400e;
        border: 1px solid #fcd34d;
    }
    
    .badge-success {
        background: #f0fdf4;
        color: #166534;
        border: 1px solid #86efac;
    }
    
    .badge-info {
        background: #eff6ff;
        color: #1e40af;
        border: 1px solid #93c5fd;
    }
    
    /* Risk gauge styling */
    .risk-gauge {
        text-align: center;
        padding: 1rem;
        border-radius: 12px;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    
    .risk-low { border-left: 4px solid #22c55e; }
    .risk-medium { border-left: 4px solid #eab308; }
    .risk-high { border-left: 4px solid #ef4444; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER & BRANDING
# ============================================================================

# Professional header with clean layout
st.markdown("""
<div style='background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); 
            padding: 2rem 2.5rem; border-radius: 20px; margin-bottom: 2rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);'>
    <div style='display: flex; align-items: center; justify-content: space-between;'>
        <div>
            <h1 style='margin: 0; color: #ffffff; font-size: 2.25rem; font-weight: 700; 
                       font-family: "Poppins", sans-serif; letter-spacing: -0.02em;'>
                ⚕️ Clinical Decision Support
            </h1>
            <p style='margin: 0.5rem 0 0 0; color: #94a3b8; font-size: 1rem; font-weight: 500;'>
                AI-Powered Clinical Intelligence • Powered by MedGemma
            </p>
        </div>
        <div style='text-align: right;'>
            <div style='background: rgba(59, 130, 246, 0.2); padding: 0.75rem 1.5rem; 
                        border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.3);'>
                <p style='margin: 0; color: #93c5fd; font-size: 0.875rem; font-weight: 600;'>
                    System Status
                </p>
                <p style='margin: 0.25rem 0 0 0; color: #ffffff; font-size: 1.25rem; font-weight: 700;'>
                    🟢 Online
                </p>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Clean separator
st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)

# Sidebar configuration (collapsed by default)
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("Model Settings")
    use_mock = st.checkbox(
        "Fast Analysis Mode",
        value=Config.USE_MOCK_LLM,
        help="Use rule-based analysis for instant results"
    )
    Config.USE_MOCK_LLM = use_mock
    
    if not use_mock:
        st.info(f"📦 Model: {Config.MODEL_ID}")
        st.info(f"🖥️ Device: {Config.get_device()}")
        st.warning("⚠️ First run will take 2-5 minutes to load the model")
    
    st.divider()
    
    st.subheader("About")
    st.markdown("""
    This agent demonstrates clinical decision support by:
    - Retrieving patient EHR data
    - Analyzing lab results
    - Checking medications
    - Reviewing imaging reports  
    - Screening drug interactions
    - Referencing clinical guidelines
    - Synthesizing actionable insights
    """)
    
    st.divider()
    st.caption("Built with MedGemma & Streamlit")
    st.caption("Version 2.0 - Hybrid Intelligent Mode")

# ============================================================================
# PATIENT SELECTION DASHBOARD
# ============================================================================

# Patient database
patient_data = {
    "P001": {
        "name": "John Doe",
        "age": 68,
        "gender": "Male",
        "conditions": ["CKD Stage 3b", "T2DM", "HTN", "Anemia"],
        "risk_level": "HIGH",
        "default_complaint": "Fatigue and dizziness for 2 weeks. Reports decreased appetite."
    },
    "P002": {
        "name": "Jane Smith",
        "age": 45,
        "gender": "Female",
        "conditions": ["Asthma", "Migraines", "Anxiety"],
        "risk_level": "MEDIUM",
        "default_complaint": "Increased shortness of breath and wheezing for 3 days."
    }
}

# ============================================================================
# IMPROVEMENT 1: DROPDOWN PATIENT SELECTOR
# ============================================================================

st.markdown("### 👥 Patient Selection")
st.markdown("")

# Format dropdown options
def format_patient_option(pid):
    data = patient_data[pid]
    risk_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(data['risk_level'], "⚪")
    return f"{risk_emoji} {pid} - {data['name']} ({data['age']}yo {data['gender']}) - {', '.join(data['conditions'][:2])}"

# Dropdown selector
patient_id = st.selectbox(
    "Select patient from database",
    options=list(patient_data.keys()),
    format_func=format_patient_option,
    label_visibility="collapsed"
)

selected_patient_data = patient_data[patient_id]

# Display selected patient details in elegant card
risk_color = {"HIGH": "#ef4444", "MEDIUM": "#eab308", "LOW": "#22c55e"}.get(selected_patient_data['risk_level'], "#3b82f6")

st.markdown(f"""
<div style='
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    border-left: 5px solid {risk_color};
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
'>
    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;'>
        <div style='font-size: 1.4rem; font-weight: 700; color: #1e3a8a;'>
            {patient_id} - {selected_patient_data['name']}
        </div>
        <div style='background: {risk_color}20; color: {risk_color}; padding: 0.4rem 1rem; border-radius: 16px; font-size: 0.8rem; font-weight: 700; border: 2px solid {risk_color};'>
            {selected_patient_data['risk_level']} RISK
        </div>
    </div>
    <div style='color: #64748b; font-size: 0.95rem; margin-bottom: 0.5rem;'>
        <strong>Demographics:</strong> {selected_patient_data['age']} years old, {selected_patient_data['gender']}
    </div>
    <div style='color: #475569; font-size: 0.9rem;'>
        <strong style='color: #1e3a8a;'>Active Conditions:</strong> {', '.join(selected_patient_data['conditions'])}
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("")

# Clinical complaint section
col_title, col_audio_icon = st.columns([10, 1])
with col_title:
    st.markdown("### 📝 Chief Complaint")
with col_audio_icon:
    if st.button("🎤", help="Audio recording (coming soon)", key="audio_placeholder"):
        st.info("🎙️ Audio recording feature coming soon!")

complaint = st.text_area(
    "Enter clinical complaint or reason for consultation",
    value=selected_patient_data['default_complaint'],
    height=100,
    label_visibility="collapsed",
    help="Describe current symptoms, duration, and relevant context"
)

# ============================================================================
# ACTION PANEL
# ============================================================================

st.markdown("")
st.markdown("<hr style='margin: 1.5rem 0; border: none; border-top: 2px solid #e5e7eb;'>", unsafe_allow_html=True)

col_run, col_clear, col_settings = st.columns([2, 2, 3])

with col_run:
    run_button = st.button(
        "▶ Run Clinical Analysis",
        type="primary",
        use_container_width=True,
        disabled=not complaint.strip()
    )

with col_clear:
    if st.button("↻ Clear Results", use_container_width=True):
        if 'result' in st.session_state:
            del st.session_state['result']
        if 'logs' in st.session_state:
            del st.session_state['logs']
        if 'observations' in st.session_state:
            del st.session_state['observations']
        # Don't use st.rerun() - let Streamlit handle the state naturally

with col_settings:
    mode_display = "Fast Analysis" if Config.USE_MOCK_LLM else "AI-Powered Analysis"
    st.markdown(f"""
    <div style='text-align: right; padding: 0.5rem; color: #64748b; font-size: 0.85rem;'>
        <strong>Mode:</strong> {mode_display}
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# AGENT EXECUTION
# ============================================================================

if run_button:
    if not complaint.strip():
        st.error("Please enter a clinical complaint")
    else:
# ============================================================================
        # IMPROVEMENT 2: MODERN PROGRESS BAR
        # ============================================================================
        
        st.markdown("")
        st.markdown("### ⚡ Analysis in Progress")
        
        # Progress components
        progress_bar_container = st.empty()
        status_line_container = st.empty()  # Single line that updates in place
        progress_details_container = st.empty()
        
        logs = []
        total_steps = 8  # Estimate total steps
        
        # Use dict to store mutable counter (avoids nonlocal issues)
        progress_tracker = {'current_step': 0}
        
        def emit(message):
            """Callback to update progress - single line updates in place."""
            logs.append({'message': message, 'timestamp': datetime.now()})
            
            # Update step counter
            if "COMPLETED" in message or "SKIPPED" in message:
                progress_tracker['current_step'] += 1
            
            # Calculate progress percentage
            progress_percent = min(int((progress_tracker['current_step'] / total_steps) * 100), 100)
            
            # Update progress bar
            progress_bar_container.progress(progress_percent, text=f"Progress: {progress_percent}%")
            
            # Choose icon and styling based on message
            msg = message
            if "STARTED" in msg:
                status_icon = "⏳"
                status_color = "#3b82f6"
            elif "COMPLETED" in msg:
                status_icon = "✅"
                status_color = "#22c55e"
            elif "FAILED" in msg or "ERROR" in msg:
                status_icon = "❌"
                status_color = "#ef4444"
            elif "SKIPPED" in msg:
                status_icon = "➖"
                status_color = "#94a3b8"
            else:
                status_icon = "▪️"
                status_color = "#6366f1"
            
            # Update the SINGLE status line (this updates in place, not a new line)
            status_line_container.markdown(
                f"**{status_icon} Step {progress_tracker['current_step']}/{total_steps}:** {msg}",
                unsafe_allow_html=False
            )
            
            # Show detailed log (collapsible, below the updating line)
            if len(logs) > 1:
                with progress_details_container.expander("📋 View detailed execution log", expanded=False):
                    for log in logs:
                        msg_text = log['message']
                        time_str = log['timestamp'].strftime("%H:%M:%S")
                        
                        if "COMPLETED" in msg_text:
                            st.success(f"{time_str} - {msg_text}")
                        elif "FAILED" in msg_text or "ERROR" in msg_text:
                            st.error(f"{time_str} - {msg_text}")
                        elif "SKIPPED" in msg_text:
                            st.info(f"{time_str} - {msg_text}")
                        else:
                            st.write(f"{time_str} - {msg_text}")
        
        # Run the agent
        with st.spinner("Analyzing clinical data..."):
            try:
                result_data = run_agent(patient_id, complaint, emit)
                
                # Handle both tuple and string returns
                if isinstance(result_data, tuple):
                    result, observations = result_data
                else:
                    result = result_data
                    observations = {}
                
                st.session_state['result'] = result
                st.session_state['observations'] = observations
                st.session_state['logs'] = logs
                st.session_state['patient_id'] = patient_id
                st.session_state['complaint'] = complaint
                
                # Success notification
                st.markdown("""
                <div style='
                    background: #dcfce7;
                    border-left: 4px solid #22c55e;
                    padding: 1rem 1.5rem;
                    border-radius: 8px;
                    margin: 1rem 0;
                '>
                    <strong style='color: #166534;'>✓ Analysis Complete</strong>
                    <p style='margin: 0.5rem 0 0 0; color: #166534; font-size: 0.9rem;'>
                        Clinical summary generated successfully
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.markdown(f"""
                <div style='
                    background: #fee2e2;
                    border-left: 4px solid #ef4444;
                    padding: 1rem 1.5rem;
                    border-radius: 8px;
                    margin: 1rem 0;
                '>
                    <strong style='color: #991b1b;'>✗ Analysis Failed</strong>
                    <p style='margin: 0.5rem 0 0 0; color: #991b1b; font-size: 0.9rem;'>
                        {str(e)}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                st.exception(e)
                result = None
        
        # ============================================================================
        # RESULTS DASHBOARD
        # ============================================================================
        
        # Show results if we have them
        if result or 'result' in st.session_state:
            st.markdown("")
            st.markdown("<hr style='margin: 2rem 0; border: none; border-top: 2px solid #e5e7eb;'>", unsafe_allow_html=True)
            st.markdown("### 📊 Clinical Decision Support Summary")
            
            # Summary header card
            st.markdown("""
            <div class='medical-card' style='background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-left: 4px solid #2563eb;'>
                <div style='font-weight: 600; color: #1e40af; margin-bottom: 0.5rem;'>
                    Analysis Complete
                </div>
                <div style='font-size: 0.85rem; color: #3b82f6;'>
                    Comprehensive review of patient data completed with evidence-based recommendations
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Main results in tabs
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📄 Clinical Summary",
                "📈 Data Insights",
                "🔍 Raw Output",
                "📋 Execution Log",
                "🩺 Doctor Decision"
            ])
            
            with tab1:
                # Display clinical summary in a styled container
                st.markdown("""
                <div class='results-container'>
                """, unsafe_allow_html=True)
                
                # Use result from current run or session state
                display_result = result if result else st.session_state.get('result', 'No results available')
                st.markdown(display_result)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Download button
                col_dl1, col_dl2 = st.columns([1, 3])
                with col_dl1:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        label="⤓ Download Report",
                        data=result,
                        file_name=f"clinical_summary_{patient_id}_{timestamp}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                # ====================================================================
                # DOCTOR DECISION FORM
                # ====================================================================
                
                st.markdown("")
                st.markdown("---")
                st.markdown("#### 🩺 Doctor Decision & Treatment Plan")
                
                # Doctor decision form - ALWAYS visible if we have results
                with st.expander("📝 Enter Treatment Decision", expanded=True):
                    st.markdown("**Please review the clinical summary above and enter your treatment decisions:**")
                    
                    # Ensure session state is properly initialized
                    if 'prescriptions' not in st.session_state:
                        st.session_state['prescriptions'] = []
                    if 'treatment_notes' not in st.session_state:
                        st.session_state['treatment_notes'] = ""
                    
                    # Treatment plan section
                    st.markdown("##### 💊 Prescriptions & Medications")
                    
                    # Add prescription button
                    col_add, col_info = st.columns([1, 3])
                    with col_add:
                        if st.button("➕ Add Prescription", type="secondary", use_container_width=True, key="add_prescription_btn"):
                            st.session_state['prescriptions'].append({
                                'name': '',
                                'dose': '',
                                'frequency': 'once daily',
                                'duration': '',
                                'instructions': ''
                            })
                            # Don't use st.rerun() - let Streamlit handle the state naturally
                    
                    with col_info:
                        st.caption(f"📋 {len(st.session_state['prescriptions'])} prescription(s) added")
                        
                        # Debug info (remove in production)
                        if st.checkbox("🔧 Debug Info", key="debug_checkbox"):
                            st.json({
                                'prescriptions_count': len(st.session_state['prescriptions']),
                                'prescriptions': st.session_state['prescriptions'],
                                'treatment_notes': st.session_state.get('treatment_notes', ''),
                                'has_doctor_decision': 'doctor_decision' in st.session_state,
                                'has_safety_result': 'safety_result' in st.session_state
                            })
                    
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
                                        # Don't use st.rerun() - let Streamlit handle the state naturally
                            
                            prescription['instructions'] = st.text_area(
                                "Special Instructions",
                                value=prescription['instructions'],
                                key=f"instructions_{i}",
                                placeholder="e.g., Take with food, Monitor blood pressure"
                            )
                            
                            st.markdown("---")
                    
                    # Treatment notes
                    st.markdown("##### 📋 Treatment Plan Notes")
                    treatment_notes = st.text_area(
                        "Additional Treatment Notes",
                        value=st.session_state.get('treatment_notes', ''),
                        placeholder="Enter any additional treatment decisions, follow-up plans, or clinical notes...",
                        key="treatment_notes_input"
                    )
                    
                    # Update session state
                    st.session_state['treatment_notes'] = treatment_notes
                    
                    # Submit button
                    col_submit, col_clear = st.columns([1, 1])
                    
                    with col_submit:
                        submit_decision = st.button("🔍 Run Safety Check", type="primary", use_container_width=True, key="run_safety_check_btn")
                    
                    with col_clear:
                        if st.button("🗑️ Clear Form", use_container_width=True, key="clear_form_btn"):
                            st.session_state['prescriptions'] = []
                            st.session_state['treatment_notes'] = ""
                            st.session_state['doctor_decision'] = None
                            st.session_state['safety_result'] = None
                            # Don't use st.rerun() - let Streamlit handle the state naturally
                
                # Handle safety check
                if submit_decision:
                    if not st.session_state['prescriptions'] or not any(p.get('name') for p in st.session_state['prescriptions']):
                        st.warning("⚠️ Please add at least one prescription before running safety check.")
                    else:
                        # Prepare doctor decision
                        doctor_decision = {
                            'prescriptions': [p for p in st.session_state['prescriptions'] if p.get('name')],
                            'treatment_notes': treatment_notes,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        # Store in session state
                        st.session_state['doctor_decision'] = doctor_decision
                        
                        # Run safety monitor
                        with st.spinner("🔍 Running comprehensive safety analysis..."):
                            try:
                                from agent.orchestrator import run_safety_monitor
                                
                                # Get patient context from observations
                                patient_context = st.session_state.get('observations', {})
                                
                                # Run safety monitor
                                safety_result = run_safety_monitor(
                                    patient_id, 
                                    doctor_decision, 
                                    patient_context, 
                                    lambda msg: st.write(f"Safety Check: {msg}")
                                )
                                
                                # Store safety results
                                st.session_state['safety_result'] = safety_result
                                
                                st.success("✅ Safety analysis completed!")
                                # Don't use st.rerun() - let Streamlit handle the state naturally
                                
                            except Exception as e:
                                st.error(f"❌ Safety check failed: {str(e)}")
                
                # Display safety results if available
                if 'safety_result' in st.session_state:
                    st.markdown("")
                    st.markdown("---")
                    st.markdown("#### 🛡️ Safety Analysis Results")
                    
                    safety_result = st.session_state['safety_result']
                    
                    # Safety summary
                    if safety_result.get('status') == 'completed':
                        warnings = safety_result.get('warnings', [])
                        
                        if not warnings:
                            st.success("✅ All prescriptions appear safe based on current patient data.")
                        else:
                            # Display warnings by severity
                            critical_warnings = [w for w in warnings if w.severity == 'critical']
                            high_warnings = [w for w in warnings if w.severity == 'high']
                            medium_warnings = [w for w in warnings if w.severity == 'medium']
                            low_warnings = [w for w in warnings if w.severity == 'low']
                            
                            # Critical warnings
                            if critical_warnings:
                                st.error("🚨 **CRITICAL SAFETY ISSUES**")
                                for warning in critical_warnings:
                                    st.markdown(f"""
                                    <div style='
                                        background: #fee2e2;
                                        border-left: 4px solid #dc2626;
                                        padding: 1rem;
                                        margin: 0.5rem 0;
                                        border-radius: 8px;
                                    '>
                                        <strong style='color: #dc2626;'>{warning.drug_name}</strong><br>
                                        {warning.message}<br>
                                        <em style='color: #991b1b;'>{warning.recommendation}</em>
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
                                        <strong style='color: #d97706;'>{warning.drug_name}</strong><br>
                                        {warning.message}<br>
                                        <em style='color: #92400e;'>{warning.recommendation}</em>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            # Medium warnings
                            if medium_warnings:
                                st.info("ℹ️ **MEDIUM PRIORITY NOTES**")
                                for warning in medium_warnings:
                                    st.markdown(f"""
                                    <div style='
                                        background: #eff6ff;
                                        border-left: 4px solid #2563eb;
                                        padding: 1rem;
                                        margin: 0.5rem 0;
                                        border-radius: 8px;
                                    '>
                                        <strong style='color: #2563eb;'>{warning.drug_name}</strong><br>
                                        {warning.message}<br>
                                        <em style='color: #1e40af;'>{warning.recommendation}</em>
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
                                        <strong style='color: #64748b;'>{warning.drug_name}</strong><br>
                                        {warning.message}<br>
                                        <em style='color: #475569;'>{warning.recommendation}</em>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            # Alternative suggestions
                            alternatives = safety_result.get('alternatives', [])
                            if alternatives:
                                st.markdown("#### 🔄 Alternative Suggestions")
                                for alt in alternatives:
                                    st.markdown(f"""
                                    <div style='
                                        background: #f0f9ff;
                                        border-left: 4px solid #0ea5e9;
                                        padding: 1rem;
                                        margin: 0.5rem 0;
                                        border-radius: 8px;
                                    '>
                                        <strong style='color: #0c4a6e;'>Consider Alternative:</strong><br>
                                        <strong>{alt.get('original_drug', 'Unknown')}</strong> → <strong>{alt.get('alternative', 'Unknown')}</strong><br>
                                        <em style='color: #0369a1;'>Reason: {alt.get('reason', 'Safety concern')}</em>
                                    </div>
                                    """, unsafe_allow_html=True)
                    
                    elif safety_result.get('status') == 'error':
                        st.error(f"❌ Safety analysis failed: {safety_result.get('summary', 'Unknown error')}")
                    else:
                        st.info(safety_result.get('summary', 'No safety analysis available'))
                
                # ====================================================================
                # IMPROVEMENT 4: CHAT CONTINUATION
                # ====================================================================
                
                st.markdown("")
                st.markdown("---")
                st.markdown("#### 💬 Ask Follow-Up Questions")
            
            with tab5:
                # Doctor Decision Form
                st.markdown("#### 🩺 Doctor Decision & Treatment Plan")
                st.markdown("**Please review the clinical summary and enter your treatment decisions:**")
                
                # Ensure session state is properly initialized
                if 'prescriptions' not in st.session_state:
                    st.session_state['prescriptions'] = []
                if 'treatment_notes' not in st.session_state:
                    st.session_state['treatment_notes'] = ""
                
                # Treatment plan section
                st.markdown("##### 💊 Prescriptions & Medications")
                
                # Add prescription button
                col_add, col_info = st.columns([1, 3])
                with col_add:
                    if st.button("➕ Add Prescription", type="secondary", use_container_width=True, key="add_prescription_tab"):
                        st.session_state['prescriptions'].append({
                            'name': '',
                            'dose': '',
                            'frequency': 'once daily',
                            'duration': '',
                            'instructions': ''
                        })
                
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
                                key=f"drug_name_tab_{i}",
                                placeholder="e.g., Metformin, Lisinopril"
                            )
                        
                        with col2:
                            prescription['dose'] = st.text_input(
                                "Dose",
                                value=prescription['dose'],
                                key=f"dose_tab_{i}",
                                placeholder="e.g., 500mg, 10mg"
                            )
                        
                        with col3:
                            prescription['frequency'] = st.selectbox(
                                "Frequency",
                                options=["once daily", "twice daily", "three times daily", "four times daily", "as needed"],
                                index=0 if not prescription['frequency'] else ["once daily", "twice daily", "three times daily", "four times daily", "as needed"].index(prescription['frequency']) if prescription['frequency'] in ["once daily", "twice daily", "three times daily", "four times daily", "as needed"] else 0,
                                key=f"frequency_tab_{i}"
                            )
                        
                        col4, col5 = st.columns([1, 1])
                        
                        with col4:
                            prescription['duration'] = st.text_input(
                                "Duration",
                                value=prescription['duration'],
                                key=f"duration_tab_{i}",
                                placeholder="e.g., 7 days, 30 days, ongoing"
                            )
                        
                        with col5:
                            if st.button("🗑️ Remove", key=f"remove_tab_{i}", type="secondary", use_container_width=True):
                                if len(st.session_state['prescriptions']) > 0:
                                    st.session_state['prescriptions'].pop(i)
                                    st.rerun()
                        
                        prescription['instructions'] = st.text_area(
                            "Special Instructions",
                            value=prescription['instructions'],
                            key=f"instructions_tab_{i}",
                            placeholder="e.g., Take with food, Monitor blood pressure"
                        )
                        
                        st.markdown("---")
                
                # Treatment notes
                st.markdown("##### 📋 Treatment Plan Notes")
                treatment_notes = st.text_area(
                    "Additional Treatment Notes",
                    value=st.session_state.get('treatment_notes', ''),
                    placeholder="Enter any additional treatment decisions, follow-up plans, or clinical notes...",
                    key="treatment_notes_tab"
                )
                
                # Update session state
                st.session_state['treatment_notes'] = treatment_notes
                
                # Submit button
                col_submit, col_clear = st.columns([1, 1])
                
                with col_submit:
                    submit_decision = st.button("🔍 Run Safety Check", type="primary", use_container_width=True, key="run_safety_check_tab")
                
                with col_clear:
                    if st.button("🗑️ Clear Form", use_container_width=True, key="clear_form_tab"):
                        st.session_state['prescriptions'] = []
                        st.session_state['treatment_notes'] = ""
                        st.session_state['doctor_decision'] = None
                        st.session_state['safety_result'] = None
                        st.rerun()
                
                # Handle safety check
                if submit_decision:
                    if not st.session_state['prescriptions'] or not any(p.get('name') for p in st.session_state['prescriptions']):
                        st.warning("⚠️ Please add at least one prescription before running safety check.")
                    else:
                        # Prepare doctor decision
                        doctor_decision = {
                            'prescriptions': [p for p in st.session_state['prescriptions'] if p.get('name')],
                            'treatment_notes': treatment_notes,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        # Store in session state
                        st.session_state['doctor_decision'] = doctor_decision
                        
                        # Run safety monitor
                        with st.spinner("🔍 Running comprehensive safety analysis..."):
                            try:
                                from agent.orchestrator import run_safety_monitor
                                
                                # Get patient context from observations
                                patient_context = st.session_state.get('observations', {})
                                
                                # Run safety monitor
                                safety_result = run_safety_monitor(
                                    st.session_state.get('patient_id', 'P001'), 
                                    doctor_decision, 
                                    patient_context, 
                                    lambda msg: st.write(f"Safety Check: {msg}")
                                )
                                
                                # Store safety results
                                st.session_state['safety_result'] = safety_result
                                
                                st.success("✅ Safety analysis completed!")
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"❌ Safety check failed: {str(e)}")
                
                # Display safety results if available
                if 'safety_result' in st.session_state:
                    st.markdown("")
                    st.markdown("---")
                    st.markdown("#### 🛡️ Safety Analysis Results")
                    
                    safety_result = st.session_state['safety_result']
                    
                    # Safety summary
                    if safety_result.get('status') == 'completed':
                        warnings = safety_result.get('warnings', [])
                        
                        if not warnings:
                            st.success("✅ All prescriptions appear safe based on current patient data.")
                        else:
                            # Display warnings by severity
                            critical_warnings = [w for w in warnings if w.severity == 'critical']
                            high_warnings = [w for w in warnings if w.severity == 'high']
                            medium_warnings = [w for w in warnings if w.severity == 'medium']
                            low_warnings = [w for w in warnings if w.severity == 'low']
                            
                            # Critical warnings
                            if critical_warnings:
                                st.error("🚨 **CRITICAL SAFETY ISSUES**")
                                for warning in critical_warnings:
                                    st.markdown(f"""
                                    <div style='
                                        background: #fee2e2;
                                        border-left: 4px solid #dc2626;
                                        padding: 1rem;
                                        margin: 0.5rem 0;
                                        border-radius: 8px;
                                    '>
                                        <strong style='color: #dc2626;'>{warning.drug_name}</strong><br>
                                        {warning.message}<br>
                                        <em style='color: #991b1b;'>{warning.recommendation}</em>
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
                                        <strong style='color: #d97706;'>{warning.drug_name}</strong><br>
                                        {warning.message}<br>
                                        <em style='color: #92400e;'>{warning.recommendation}</em>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            # Medium warnings
                            if medium_warnings:
                                st.info("ℹ️ **MEDIUM PRIORITY NOTES**")
                                for warning in medium_warnings:
                                    st.markdown(f"""
                                    <div style='
                                        background: #eff6ff;
                                        border-left: 4px solid #2563eb;
                                        padding: 1rem;
                                        margin: 0.5rem 0;
                                        border-radius: 8px;
                                    '>
                                        <strong style='color: #2563eb;'>{warning.drug_name}</strong><br>
                                        {warning.message}<br>
                                        <em style='color: #1e40af;'>{warning.recommendation}</em>
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
                                        <strong style='color: #64748b;'>{warning.drug_name}</strong><br>
                                        {warning.message}<br>
                                        <em style='color: #475569;'>{warning.recommendation}</em>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            # Alternative suggestions
                            alternatives = safety_result.get('alternatives', [])
                            if alternatives:
                                st.markdown("#### 🔄 Alternative Suggestions")
                                for alt in alternatives:
                                    st.markdown(f"""
                                    <div style='
                                        background: #f0f9ff;
                                        border-left: 4px solid #0ea5e9;
                                        padding: 1rem;
                                        margin: 0.5rem 0;
                                        border-radius: 8px;
                                    '>
                                        <strong style='color: #0c4a6e;'>Consider Alternative:</strong><br>
                                        <strong>{alt.get('original_drug', 'Unknown')}</strong> → <strong>{alt.get('alternative', 'Unknown')}</strong><br>
                                        <em style='color: #0369a1;'>Reason: {alt.get('reason', 'Safety concern')}</em>
                                    </div>
                                    """, unsafe_allow_html=True)
                    
                    elif safety_result.get('status') == 'error':
                        st.error(f"❌ Safety analysis failed: {safety_result.get('summary', 'Unknown error')}")
                    else:
                        st.info(safety_result.get('summary', 'No safety analysis available'))
        
        # ============================================================================
        # OLD DOCTOR DECISION FORM - REMOVED (now in tab5)
        # ============================================================================
        
        # This section has been moved to tab5 to prevent conflicts

# ============================================================================
# CACHED RESULTS DISPLAY
# ============================================================================

# This section has been removed to prevent duplication

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("")
st.markdown("<hr style='margin: 3rem 0 1rem 0; border: none; border-top: 2px solid #e5e7eb;'>", unsafe_allow_html=True)

# Footer with disclaimer
st.markdown("""
<div style='
    background: #fef2f2;
    border: 1px solid #fca5a5;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    margin-bottom: 1rem;
'>
    <div style='color: #991b1b; font-weight: 600; margin-bottom: 0.5rem;'>
        ⚠️ Important Disclaimer
    </div>
    <div style='color: #7f1d1d; font-size: 0.85rem; line-height: 1.6;'>
        This is a demonstration system for <strong>educational and research purposes only</strong>. 
        It is NOT validated for clinical use and NOT FDA approved. All clinical decisions MUST be made by 
        qualified healthcare professionals. Always verify information with primary sources and follow 
        institutional protocols.
    </div>
</div>
""", unsafe_allow_html=True)

# Credits
st.markdown("""
<div style='text-align: center; color: #94a3b8; font-size: 0.8rem; padding: 1rem 0;'>
    Powered by MedGemma-4B | Built with Streamlit<br>
    Hybrid Intelligent Mode Active | Version 2.0
</div>
""", unsafe_allow_html=True)
