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
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
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
    
    /* Clinical Section Cards - Enhanced Design */
    .clinical-section-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.75rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        border: 1px solid #e2e8f0;
        border-left: 4px solid #cbd5e1;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .clinical-section-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
        border-color: #cbd5e1;
    }
    
    /* Section-specific styling */
    .section-diagnosis {
        border-left-color: #3b82f6;
        background: linear-gradient(to right, #eff6ff 0%, #ffffff 15%);
    }
    
    .section-reasoning {
        border-left-color: #60a5fa;
        background: linear-gradient(to right, #f0f9ff 0%, #ffffff 15%);
    }
    
    .section-differential {
        border-left-color: #64748b;
        background: #ffffff;
    }
    
    .section-attention {
        border-left-color: #f59e0b;
        background: linear-gradient(to right, #fffbeb 0%, #ffffff 15%);
    }
    
    .section-recommendations {
        border-left-color: #22c55e;
        background: linear-gradient(to right, #f0fdf4 0%, #ffffff 15%);
    }
    
    /* Section header with icon */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #f1f5f9;
    }
    
    .section-icon {
        font-size: 1.2rem;
        width: 2rem;
        height: 2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        flex-shrink: 0;
    }
    
    .section-diagnosis .section-icon {
        background: #dbeafe;
        color: #2563eb;
    }
    
    .section-reasoning .section-icon {
        background: #e0f2fe;
        color: #0284c7;
    }
    
    .section-differential .section-icon {
        background: #f1f5f9;
        color: #475569;
    }
    
    .section-attention .section-icon {
        background: #fef3c7;
        color: #d97706;
    }
    
    .section-recommendations .section-icon {
        background: #dcfce7;
        color: #16a34a;
    }
    
    .section-title {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        margin: 0;
        flex: 1;
    }
    
    /* Custom typography per section */
    .section-diagnosis .section-title {
        font-size: 1.5rem;
        color: #1e40af;
    }
    
    .section-reasoning .section-title {
        font-size: 1.1rem;
        color: #0c4a6e;
    }
    
    .section-differential .section-title {
        font-size: 1rem;
        color: #334155;
    }
    
    .section-attention .section-title {
        font-size: 1.15rem;
        color: #92400e;
        font-weight: 700;
    }
    
    .section-recommendations .section-title {
        font-size: 1.1rem;
        color: #166534;
    }
    
    /* Section content styling */
    .section-content {
        color: #334155;
        line-height: 1.7;
        font-size: 0.95rem;
    }
    
    .section-content ul {
        margin: 0.75rem 0;
        padding-left: 1.5rem;
    }
    
    .section-content li {
        margin: 0.5rem 0;
        line-height: 1.6;
    }
    
    .section-content strong {
        color: #1e293b;
        font-weight: 600;
    }
    
    .section-content h4 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1rem;
        margin-top: 1.25rem;
        margin-bottom: 0.75rem;
        color: #475569;
    }
    
    /* Badge styling for severity levels */
    .severity-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-critical {
        background: #fee2e2;
        color: #991b1b;
    }
    
    .badge-high {
        background: #fef3c7;
        color: #92400e;
    }
    
    .badge-medium {
        background: #dbeafe;
        color: #1e40af;
    }
    
    .badge-low {
        background: #f0fdf4;
        color: #166534;
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

# Load patient database from JSON file
def load_patient_database():
    """Load patient database from JSON file"""
    try:
        with open('patient_database.json', 'r') as f:
            database = json.load(f)
            return database.get('patients', [])
    except FileNotFoundError:
        st.error("⚠️ patient_database.json not found. Using fallback data.")
        return []

# Transform database format to frontend format
def transform_patient_data(patients_list):
    """Transform patient database format to frontend format"""
    patient_data = {}
    default_complaints = {
        "P001": "Fatigue and dizziness for 2 weeks. Reports decreased appetite.",
        "P002": "Increased shortness of breath and wheezing for 3 days.",
        "P003": "Chest discomfort and irregular heartbeat.",
        "P004": "Routine prenatal care visit.",
        "P005": "Increased shortness of breath, cough with sputum, and wheezing.",
        "P006": "knee pain and swelling for 3 weeks"  # Omar - no default complaint, user will add
    }
    
    for patient in patients_list:
        pid = patient.get('patient_id', '')
        demographics = patient.get('demographics', {})
        conditions = patient.get('conditions', [])
        
        # Determine risk level based on conditions
        risk_level = "MEDIUM"
        if any('kidney' in c.lower() or 'ckd' in c.lower() or 'heart failure' in c.lower() for c in conditions):
            risk_level = "HIGH"
        elif len(conditions) <= 1:
            risk_level = "LOW"
        
        patient_data[pid] = {
            "name": patient.get('name', 'Unknown'),
            "age": demographics.get('age', 0),
            "gender": demographics.get('gender', 'Unknown'),
            "conditions": conditions,
            "risk_level": risk_level,
            "default_complaint": default_complaints.get(pid, "")
        }
    
    return patient_data

# Load and transform patient data
patients_list = load_patient_database()
patient_data = transform_patient_data(patients_list)

# Fallback if database is empty
if not patient_data:
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
# CLINICAL REPORT PARSER AND RENDERER
# ============================================================================

def parse_clinical_report(markdown_text: str) -> list:
    """
    Parse markdown clinical report into structured sections.
    
    Args:
        markdown_text: Raw markdown report text
        
    Returns:
        List of dicts with 'type', 'title', 'content', 'css_class', 'icon'
    """
    import re
    
    # Icon mapping for different section types
    icon_mapping = {
        'PRIMARY DIAGNOSIS': 'fa-stethoscope',
        'CLINICAL REASONING': 'fa-brain',
        'DIFFERENTIAL DIAGNOSIS': 'fa-list-check',
        'ATTENTION NEEDED': 'fa-exclamation-triangle',
        'RECOMMENDATIONS': 'fa-clipboard-check',
        'CURRENT MEDICATIONS': 'fa-pills',
        'CLINICAL ASSESSMENT': 'fa-file-medical'
    }
    
    # CSS class mapping
    css_mapping = {
        'PRIMARY DIAGNOSIS': 'section-diagnosis',
        'CLINICAL REASONING': 'section-reasoning',
        'DIFFERENTIAL DIAGNOSIS': 'section-differential',
        'ATTENTION NEEDED': 'section-attention',
        'RECOMMENDATIONS': 'section-recommendations',
        'CURRENT MEDICATIONS': 'section-attention',
        'CLINICAL ASSESSMENT': None  # Container, not a card
    }
    
    sections = []
    lines = markdown_text.split('\n')
    current_section = None
    current_content = []
    skip_main_header = True
    
    for line in lines:
        line_stripped = line.strip()
        
        # Skip empty lines at the start
        if not line_stripped and not current_section:
            continue
            
        # Check for section headers (### or ##)
        header_match = re.match(r'^#{2,3}\s+(.+)$', line_stripped)
        if header_match:
            # Save previous section if exists
            if current_section and current_content:
                content_text = '\n'.join(current_content).strip()
                if content_text:  # Only add if there's content
                    sections.append({
                        'type': current_section['type'],
                        'title': current_section['title'],
                        'content': content_text,
                        'css_class': current_section['css_class'],
                        'icon': current_section['icon']
                    })
            
            # Start new section
            title = header_match.group(1).strip()
            title_upper = title.upper()
            
            # Skip main "CLINICAL ASSESSMENT" header
            if 'CLINICAL ASSESSMENT' in title_upper and skip_main_header:
                skip_main_header = False
                current_section = None
                current_content = []
                continue
            
            # Determine section type (case-insensitive matching)
            section_type = None
            css_class = None
            icon = None
            
            # Normalize title for matching
            title_normalized = title_upper.strip()
            
            if 'PRIMARY DIAGNOSIS' in title_normalized:
                section_type = 'PRIMARY DIAGNOSIS'
                css_class = 'section-diagnosis'
                icon = 'fa-stethoscope'
            elif 'CLINICAL REASONING' in title_normalized:
                section_type = 'CLINICAL REASONING'
                css_class = 'section-reasoning'
                icon = 'fa-brain'
            elif 'DIFFERENTIAL DIAGNOSIS' in title_normalized:
                section_type = 'DIFFERENTIAL DIAGNOSIS'
                css_class = 'section-differential'
                icon = 'fa-list-check'
            elif 'ATTENTION NEEDED' in title_normalized or 'ATTENTION' in title_normalized:
                section_type = 'ATTENTION NEEDED'
                css_class = 'section-attention'
                icon = 'fa-exclamation-triangle'
            elif 'RECOMMENDATIONS' in title_normalized:
                section_type = 'RECOMMENDATIONS'
                css_class = 'section-recommendations'
                icon = 'fa-clipboard-check'
            elif 'CURRENT MEDICATIONS' in title_normalized or ('MEDICATIONS' in title_normalized and 'CURRENT' in title_normalized):
                section_type = 'CURRENT MEDICATIONS'
                css_class = 'section-attention'
                icon = 'fa-pills'
            
            if section_type:
                current_section = {
                    'type': section_type,
                    'title': title,
                    'css_class': css_class,
                    'icon': icon
                }
                current_content = []
            else:
                # Unknown section header - treat as content if we're in a section
                if current_section:
                    current_content.append(line)
        else:
            # Content line
            if current_section:
                current_content.append(line)
    
    # Add last section
    if current_section and current_content:
        content_text = '\n'.join(current_content).strip()
        if content_text:
            sections.append({
                'type': current_section['type'],
                'title': current_section['title'],
                'content': content_text,
                'css_class': current_section['css_class'],
                'icon': current_section['icon']
            })
    
    return sections


def render_clinical_sections(sections: list) -> str:
    """
    Render parsed sections as HTML with icons and styling.
    
    Args:
        sections: List of section dicts from parse_clinical_report
        
    Returns:
        HTML string with styled section cards
    """
    import re
    import html
    
    html_parts = []
    
    for section in sections:
        css_class = section.get('css_class', 'clinical-section-card')
        icon = section.get('icon', 'fa-circle')
        title = html.escape(section.get('title', ''))
        content = section.get('content', '')
        
        # Convert markdown to HTML
        lines = content.split('\n')
        html_lines = []
        in_list = False
        in_paragraph = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                if in_paragraph:
                    html_lines.append('</p>')
                    in_paragraph = False
                continue
            
            # Check for markdown headers (###)
            header_match = re.match(r'^###\s+(.+)$', line_stripped)
            if header_match:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                if in_paragraph:
                    html_lines.append('</p>')
                    in_paragraph = False
                header_text = html.escape(header_match.group(1))
                html_lines.append(f'<h4>{header_text}</h4>')
                continue
            
            # Check if line is a bullet point
            if line_stripped.startswith('- '):
                if in_paragraph:
                    html_lines.append('</p>')
                    in_paragraph = False
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                # Extract content after "- "
                list_content = line_stripped[2:].strip()
                # Convert **bold** to <strong> (but escape HTML first)
                list_content = html.escape(list_content)
                list_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', list_content)
                html_lines.append(f'<li>{list_content}</li>')
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                # Regular paragraph text
                if not in_paragraph:
                    html_lines.append('<p>')
                    in_paragraph = True
                else:
                    html_lines.append('<br>')
                
                # Convert **bold** to <strong> (but escape HTML first)
                line_escaped = html.escape(line_stripped)
                line_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line_escaped)
                html_lines.append(line_html)
        
        # Close any open tags
        if in_list:
            html_lines.append('</ul>')
        if in_paragraph:
            html_lines.append('</p>')
        
        content_html = '\n'.join(html_lines)
        
        # Build HTML output with proper escaping
        html_output = f"""<div class="clinical-section-card {css_class}">
    <div class="section-header">
        <div class="section-icon">
            <i class="fas {icon}"></i>
        </div>
        <h3 class="section-title">{title}</h3>
    </div>
    <div class="section-content">
        {content_html}
    </div>
</div>"""
        html_parts.append(html_output)
    
    return '\n'.join(html_parts)


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
            tab1, tab2, tab3, tab4 = st.tabs([
                "📄 Clinical Summary",
                "📈 Data Insights",
                "🔍 Raw Output",
                "📋 Execution Log"
            ])
            
            with tab1:
                # Use result from current run or session state
                display_result = result if result else st.session_state.get('result', 'No results available')
                
                # Parse and render clinical report with enhanced UI
                if display_result and display_result != 'No results available':
                    try:
                        sections = parse_clinical_report(display_result)
                        if sections and len(sections) > 0:
                            # Render sections as styled cards with icons
                            html_output = render_clinical_sections(sections)
                            # Use st.components.v1.html or st.markdown with unsafe_allow_html
                            st.markdown(html_output, unsafe_allow_html=True)
                        else:
                            # Fallback to plain markdown if parsing fails
                            st.markdown(display_result)
                            if st.session_state.get('debug_mode', False):
                                st.warning(f"Parsing returned {len(sections) if sections else 0} sections")
                    except Exception as e:
                        # Fallback to plain markdown on error
                        st.markdown(display_result)
                        if st.session_state.get('debug_mode', False):
                            st.error(f"Rendering error: {str(e)}")
                        else:
                            st.warning("Note: Enhanced rendering unavailable. Showing plain format.")
                else:
                    st.info("No clinical summary available. Run an analysis to generate a report.")
                
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
        
        # ============================================================================
        # DOCTOR DECISION FORM - REMOVED
        # ============================================================================
        
        # Prescription and treatment plan functionality has been moved to 
        # the separate Doctor Decision Service (port 8503)

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
