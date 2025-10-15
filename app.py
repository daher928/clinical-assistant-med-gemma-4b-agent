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
        st.rerun()

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
        
        if result:
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
            tab1, tab2, tab3, tab4 = st.tabs([
                "📄 Clinical Summary",
                "📈 Data Insights",
                "🔍 Raw Output",
                "📋 Execution Log"
            ])
            
            with tab1:
                # Display clinical summary in a styled container
                st.markdown("""
                <div class='results-container'>
                """, unsafe_allow_html=True)
                
                st.markdown(result)
                
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
                # IMPROVEMENT 4: CHAT CONTINUATION
                # ====================================================================
                
                st.markdown("")
                st.markdown("---")
                st.markdown("#### 💬 Ask Follow-Up Questions")
                
                # Initialize chat history
                if 'chat_history' not in st.session_state:
                    st.session_state['chat_history'] = []
                
                # Add initial summary to chat if not already there
                if result not in [msg.get('content') for msg in st.session_state['chat_history']]:
                    st.session_state['chat_history'] = [{
                        'role': 'assistant',
                        'content': result,
                        'timestamp': datetime.now()
                    }]
                
                # Follow-up question input
                follow_up_question = st.text_input(
                    "Ask a follow-up question about this patient",
                    placeholder="e.g., What are the risks of starting ESA therapy? Should we adjust metformin dose?",
                    key="follow_up_input"
                )
                
                col_ask, col_clear_chat = st.columns([3, 1])
                
                with col_ask:
                    ask_button = st.button("💬 Ask Question", use_container_width=True, type="primary")
                
                with col_clear_chat:
                    if st.button("🗑️ Clear Chat", use_container_width=True):
                        st.session_state['chat_history'] = []
                        st.rerun()
                
                # Handle follow-up question
                if ask_button and follow_up_question.strip():
                    # Add user question to history
                    st.session_state['chat_history'].append({
                        'role': 'user',
                        'content': follow_up_question,
                        'timestamp': datetime.now()
                    })
                    
                    # Generate response
                    with st.spinner("Thinking..."):
                        # Build context with chat history
                        chat_context = f"""
Previous clinical summary for patient {patient_id}:
{result}

Patient data available: EHR, Labs, Meds, Imaging, DDI, Guidelines

Follow-up question: {follow_up_question}

Provide a brief, focused answer (50-100 words) based on the patient data and clinical guidelines.
If the question requires data not in the summary, reference the appropriate source [EHR/LABS/MEDS/etc].
"""
                        
                        llm = MedGemmaLLM()
                        
                        # Get observations if available
                        obs = st.session_state.get('observations', {})
                        
                        try:
                            # Simple synthesis for follow-up
                            response = llm.synthesize(
                                system_prompt="You are a clinical assistant answering follow-up questions. Be concise and cite sources.",
                                user_prompt=chat_context,
                                observations=obs
                            )
                        except:
                            response = "I'm having trouble generating a response. Please try rephrasing your question or run a new analysis."
                        
                        # Add assistant response to history
                        st.session_state['chat_history'].append({
                            'role': 'assistant',
                            'content': response,
                            'timestamp': datetime.now()
                        })
                        
                        st.rerun()
                
                # Display chat history
                if len(st.session_state.get('chat_history', [])) > 1:
                    st.markdown("")
                    st.markdown("**Conversation History:**")
                    
                    for i, msg in enumerate(st.session_state['chat_history']):
                        if msg['role'] == 'user':
                            st.markdown(f"""
                            <div style='
                                background: #eff6ff;
                                border-left: 4px solid #3b82f6;
                                padding: 1rem;
                                border-radius: 8px;
                                margin: 0.5rem 0;
                            '>
                                <div style='color: #1e40af; font-weight: 600; font-size: 0.85rem; margin-bottom: 0.3rem;'>
                                    👤 You asked:
                                </div>
                                <div style='color: #475569;'>{msg['content']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Skip first assistant message (it's the main summary shown above)
                            if i > 0:
                                st.markdown(f"""
                                <div style='
                                    background: #f0fdf4;
                                    border-left: 4px solid #22c55e;
                                    padding: 1rem;
                                    border-radius: 8px;
                                    margin: 0.5rem 0;
                                '>
                                    <div style='color: #166534; font-weight: 600; font-size: 0.85rem; margin-bottom: 0.3rem;'>
                                        🤖 Assistant:
                                    </div>
                                    <div style='color: #475569;'>{msg['content']}</div>
                                </div>
                                """, unsafe_allow_html=True)
            
# ============================================================================
            # IMPROVEMENT 3: ENHANCED DATA INSIGHTS WITH GRAPHS
            # ============================================================================
            
            with tab2:
                st.markdown("#### 📊 Data Insights & Analysis")
                
                # Check if we have multi-agent insights
                observations = st.session_state.get('observations', {})
                has_analysis = 'ANALYSIS' in observations
                has_risks = 'RISKS' in observations
                has_guidelines = 'GUIDELINES' in observations
                
                if has_analysis or has_risks or has_guidelines:
                    # Multi-agent insights available
                    st.markdown("##### 🤖 AI Agent Analysis")
                    
                    # Analysis insights
                    if has_analysis:
                        analysis = observations['ANALYSIS']
                        
                        # Trends section
                        if analysis.get('trends'):
                            st.markdown("**📈 Lab Trends Detected:**")
                            for trend in analysis['trends']:
                                direction_icon = "📈" if trend['direction'] == "↑" else "📉"
                                st.markdown(f"""
                                <div style='background: #f8fafc; border-left: 4px solid #3b82f6; padding: 1rem; margin: 0.5rem 0; border-radius: 8px;'>
                                    <strong>{trend['test']}</strong>: {trend['change']} {direction_icon}<br>
                                    <small style='color: #64748b;'>{trend['clinical_significance']}</small>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Patterns section
                        if analysis.get('patterns'):
                            st.markdown("**🔍 Clinical Patterns Identified:**")
                            for pattern in analysis['patterns']:
                                st.markdown(f"""
                                <div style='background: #f0fdf4; border-left: 4px solid #22c55e; padding: 1rem; margin: 0.5rem 0; border-radius: 8px;'>
                                    <strong>{pattern['name']}</strong><br>
                                    <small style='color: #166534;'>{pattern['description']}</small><br>
                                    <small style='color: #64748b;'><strong>Monitoring:</strong> {pattern['monitoring']}</small>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    # Risk insights
                    if has_risks:
                        risks = observations['RISKS']
                        
                        if risks.get('risks'):
                            st.markdown("**⚠️ High-Risk Findings:**")
                            for risk in risks['risks']:
                                severity_color = {"major": "#ef4444", "moderate": "#eab308", "minor": "#22c55e"}.get(risk.get('severity', 'unknown'), "#3b82f6")
                                st.markdown(f"""
                                <div style='background: #fef2f2; border-left: 4px solid {severity_color}; padding: 1rem; margin: 0.5rem 0; border-radius: 8px;'>
                                    <strong>{risk['type']}</strong> - {risk['severity'].upper()}<br>
                                    <small style='color: #991b1b;'>{risk['description']}</small><br>
                                    <small style='color: #64748b;'><strong>Action:</strong> {risk['action']}</small>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        if risks.get('critical_values'):
                            st.markdown("**🚨 Critical Lab Values:**")
                            for critical in risks['critical_values']:
                                st.markdown(f"""
                                <div style='background: #fef2f2; border-left: 4px solid #ef4444; padding: 1rem; margin: 0.5rem 0; border-radius: 8px;'>
                                    <strong>{critical['test']}</strong>: {critical['value']} ({critical['status']})<br>
                                    <small style='color: #991b1b;'><strong>Action:</strong> {critical['action']}</small>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    # Guidelines insights
                    if has_guidelines:
                        guidelines = observations['GUIDELINES']
                        
                        if guidelines.get('recommendations'):
                            st.markdown("**📚 Evidence-Based Recommendations:**")
                            for rec in guidelines['recommendations']:
                                urgency_color = {"Within 2-4 weeks": "#ef4444", "Non-urgent": "#22c55e"}.get(rec.get('urgency', ''), "#3b82f6")
                                st.markdown(f"""
                                <div style='background: #eff6ff; border-left: 4px solid {urgency_color}; padding: 1rem; margin: 0.5rem 0; border-radius: 8px;'>
                                    <strong>{rec['source']}</strong><br>
                                    <small style='color: #1e40af;'>{rec['recommendation']}</small><br>
                                    <small style='color: #64748b;'><strong>Strength:</strong> {rec['strength']} | <strong>Urgency:</strong> {rec['urgency']}</small>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                
                # Data retrieval overview (existing functionality)
                st.markdown("#### 📊 Data Retrieval Overview")
                
                # Metrics row
                met_col1, met_col2, met_col3, met_col4 = st.columns(4)
                
                log_messages = [log['message'] for log in logs]
                observations = st.session_state.get('observations', {})
                
                # Calculate metrics from observations
                sources_retrieved = sum(1 for source in ['EHR', 'LABS', 'MEDS', 'IMAGING', 'DDI', 'GUIDE'] 
                                      if source in observations and observations[source] and 
                                      not (isinstance(observations[source], dict) and 'error' in observations[source]))
                sources_failed = sum(1 for source in ['EHR', 'LABS', 'MEDS', 'IMAGING', 'DDI', 'GUIDE'] 
                                   if source in observations and isinstance(observations[source], dict) and 'error' in observations[source])
                sources_skipped = sum(1 for source in ['EHR', 'LABS', 'MEDS', 'IMAGING', 'DDI', 'GUIDE'] 
                                    if source not in observations or not observations[source])
                total_time = len(logs) * 0.5  # Approximate
                
                with met_col1:
                    st.metric("✅ Retrieved", sources_retrieved)
                
                with met_col2:
                    st.metric("➖ Skipped", sources_skipped, delta="Optimized", delta_color="off")
                
                with met_col3:
                    st.metric("❌ Failed", sources_failed, delta_color="inverse")
                
                with met_col4:
                    st.metric("⏱️ Time", f"{total_time:.1f}s")
                
                st.markdown("")
                st.markdown("---")
                
                # Debug information (can be removed later)
                if st.checkbox("🔍 Show Debug Info", value=False):
                    st.markdown("**Debug Information:**")
                    st.json({
                        'observations_keys': list(observations.keys()),
                        'log_messages': log_messages[:5],  # First 5 messages
                        'source_status': source_status
                    })
                    st.markdown("---")
                
                # Visual breakdown of sources used
                st.markdown("#### 🗂️ Data Sources Breakdown")
                
                source_status = {}
                for source in ['EHR', 'LABS', 'MEDS', 'IMAGING', 'DDI', 'GUIDE']:
                    # Check if data exists in observations
                    if source in observations and observations[source]:
                        # Check if it's an error
                        if isinstance(observations[source], dict) and 'error' in observations[source]:
                            source_status[source] = "Failed"
                        else:
                            source_status[source] = "Retrieved"
                    else:
                        # Fallback to log message detection for backward compatibility
                        if any(source in msg for msg in log_messages if "COMPLETED" in msg):
                            source_status[source] = "Retrieved"
                        elif any(source in msg for msg in log_messages if "SKIPPED" in msg):
                            source_status[source] = "Skipped"
                        elif any(source in msg for msg in log_messages if "FAILED" in msg):
                            source_status[source] = "Failed"
                        else:
                            source_status[source] = "Not Attempted"
                
                # Create pie chart
                status_counts = {}
                for status in source_status.values():
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                col_chart, col_legend = st.columns([2, 1])
                
                with col_chart:
                    colors = {
                        "Retrieved": "#22c55e",
                        "Skipped": "#94a3b8",
                        "Failed": "#ef4444",
                        "Not Attempted": "#e5e7eb"
                    }
                    
                    fig = go.Figure(data=[go.Pie(
                        labels=list(status_counts.keys()),
                        values=list(status_counts.values()),
                        marker=dict(colors=[colors.get(k, "#3b82f6") for k in status_counts.keys()]),
                        hole=0.4,
                        textinfo='label+value',
                        textfont=dict(size=14, family='Inter')
                    )])
                    
                    fig.update_layout(
                        title="Source Retrieval Status",
                        showlegend=False,
                        height=300,
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                with col_legend:
                    st.markdown("**Status Legend:**")
                    for source, status in source_status.items():
                        color = colors.get(status, "#3b82f6")
                        st.markdown(f"""
                        <div style='padding: 0.5rem; margin: 0.3rem 0; background: {color}20; border-left: 3px solid {color}; border-radius: 4px;'>
                            <strong>{source}</strong>: {status}
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("")
                st.markdown("---")
                
                # Retrieved data details
                st.markdown("#### 📁 Retrieved Data Details")
                
                source_details = {
                    'EHR': {'icon': '👤', 'name': 'Electronic Health Record'},
                    'LABS': {'icon': '🧪', 'name': 'Laboratory Results'},
                    'MEDS': {'icon': '💊', 'name': 'Medications'},
                    'IMAGING': {'icon': '🔬', 'name': 'Imaging Reports'},
                    'DDI': {'icon': '⚠️', 'name': 'Drug Interactions'},
                    'GUIDE': {'icon': '📚', 'name': 'Clinical Guidelines'}
                }
                
                for source, details in source_details.items():
                    status = source_status.get(source, "Unknown")
                    
                    if status == "Retrieved":
                        with st.expander(f"{details['icon']} {details['name']} - {status}", expanded=False):
                            # Show structured preview instead of raw JSON
                            if source == 'EHR' and 'EHR' in st.session_state.get('observations', {}):
                                ehr_data = st.session_state['observations']['EHR']
                                st.write(f"**Patient:** {ehr_data.get('demographics', {}).get('name', 'N/A')}")
                                st.write(f"**Age/Gender:** {ehr_data.get('demographics', {}).get('age')} / {ehr_data.get('demographics', {}).get('gender')}")
                                st.write(f"**Conditions:** {len(ehr_data.get('conditions', []))} active")
                                st.write(f"**Allergies:** {len(ehr_data.get('allergies', []))}")
                                with st.expander("View full JSON"):
                                    st.json(ehr_data)
                            
                            elif source == 'LABS' and 'LABS' in st.session_state.get('observations', {}):
                                labs_data = st.session_state['observations']['LABS']
                                results = labs_data.get('results', [])
                                st.write(f"**Total Tests:** {len(results)}")
                                abnormal = [r for r in results if r.get('status') in ['HIGH', 'LOW']]
                                st.write(f"**Abnormal:** {len(abnormal)}")
                                if abnormal:
                                    st.write("**Abnormal Values:**")
                                    for r in abnormal[:5]:
                                        st.write(f"- {r['test']}: {r['value']} {r['unit']} ({r['status']})")
                                with st.expander("View full JSON"):
                                    st.json(labs_data)
                            
                            elif source == 'MEDS' and 'MEDS' in st.session_state.get('observations', {}):
                                meds_data = st.session_state['observations']['MEDS']
                                active = meds_data.get('active', [])
                                st.write(f"**Active Medications:** {len(active)}")
                                for med in active[:5]:
                                    st.write(f"- {med.get('name')} {med.get('dose')} - {med.get('indication')}")
                                with st.expander("View full JSON"):
                                    st.json(meds_data)
                            
                            elif source == 'DDI' and 'DDI' in st.session_state.get('observations', {}):
                                ddi_data = st.session_state['observations']['DDI']
                                if isinstance(ddi_data, list):
                                    st.write(f"**Interactions Found:** {len(ddi_data)}")
                                    for interaction in ddi_data[:5]:
                                        severity = interaction.get('severity', 'unknown')
                                        severity_color = {"major": "🔴", "moderate": "🟡", "minor": "🟢"}.get(severity, "⚪")
                                        st.write(f"{severity_color} {interaction.get('a')} + {interaction.get('b')} ({severity})")
                                with st.expander("View full JSON"):
                                    st.json(ddi_data)
                            
                            else:
                                # Default JSON view
                                if source in st.session_state.get('observations', {}):
                                    st.json(st.session_state['observations'][source])
                    else:
                        st.markdown(f"{details['icon']} {details['name']} - *{status}*")
            
            with tab3:
                # Raw output with copy button
                st.markdown("#### Raw Text Output")
                st.code(result, language="markdown")
            
            with tab4:
                # Execution timeline
                st.markdown("#### Execution Timeline")
                
                timeline_data = []
                for i, log in enumerate(logs):
                    step_type = "Processing"
                    if "COMPLETED" in log['message']:
                        step_type = "Completed"
                    elif "FAILED" in log['message']:
                        step_type = "Failed"
                    elif "SKIPPED" in log['message']:
                        step_type = "Skipped"
                    
                    timeline_data.append({
                        'Step': i + 1,
                        'Action': log['message'],
                        'Status': step_type,
                        'Time': log['timestamp'].strftime("%H:%M:%S.%f")[:-3]
                    })
                
                # Display as structured table
                for item in timeline_data:
                    status_class = {
                        'Completed': 'status-success',
                        'Failed': 'status-error',
                        'Skipped': 'status-info',
                        'Processing': 'status-processing'
                    }.get(item['Status'], 'status-info')
                    
                    st.markdown(f"""
                    <div style='
                        padding: 0.8rem;
                        margin: 0.5rem 0;
                        background: white;
                        border-radius: 8px;
                        border-left: 3px solid #3b82f6;
                    '>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div>
                                <span style='font-weight: 600; color: #475569;'>Step {item['Step']}</span>
                                <span style='margin-left: 1rem; color: #64748b;'>{item['Action']}</span>
                            </div>
                            <div>
                                <span class='status-indicator {status_class}'>{item['Status']}</span>
                                <span style='margin-left: 1rem; font-size: 0.85rem; color: #94a3b8;'>{item['Time']}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# ============================================================================
# CACHED RESULTS DISPLAY
# ============================================================================

elif 'result' in st.session_state:
    st.markdown("")
    st.markdown("<hr style='margin: 2rem 0; border: none; border-top: 2px solid #e5e7eb;'>", unsafe_allow_html=True)
    
    # Cached results banner
    st.markdown("""
    <div style='
        background: #fef3c7;
        border-left: 4px solid #eab308;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    '>
        <strong style='color: #92400e;'>ℹ Viewing Cached Results</strong>
        <p style='margin: 0.5rem 0 0 0; color: #92400e; font-size: 0.9rem;'>
            These are previously generated results. Click "Run Clinical Analysis" for fresh analysis.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📊 Clinical Summary")
    
    # Results container
    st.markdown("<div class='results-container'>", unsafe_allow_html=True)
    st.markdown(st.session_state['result'])
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Download button
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.download_button(
        label="⤓ Download Cached Report",
        data=st.session_state['result'],
        file_name=f"clinical_summary_{patient_id}_{timestamp}.txt",
        mime="text/plain"
    )

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

