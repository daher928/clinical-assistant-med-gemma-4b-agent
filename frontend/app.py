"""
Streamlit Frontend for Clinical Assistant Agent.

Modern medical-grade UI with professional design.
Run with: streamlit run frontend/app.py
"""
import streamlit as st
import sys
import os
import json
import base64
import tempfile
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from audio_recorder_streamlit import audio_recorder
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
    
    /* Modern Step Cards for Agent Progress */
    .step-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.75rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .step-card.active {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border: 2px solid #3b82f6;
        box-shadow: 0 8px 16px rgba(59, 130, 246, 0.2);
        animation: pulse-glow 2s ease-in-out infinite;
        transform: scale(1);
    }
    
    .step-card.completed {
        background: #f0fdf4;
        border-left: 4px solid #22c55e;
        opacity: 1;
        animation: fade-in 0.5s ease-out;
    }
    
    .step-card.pending {
        opacity: 0.5;
        background: #f9fafb;
        border-color: #e5e7eb;
    }
    
    .step-card.failed {
        background: #fef2f2;
        border-left: 4px solid #ef4444;
    }
    
    .step-card.skipped {
        background: #fffbeb !important;
        border-left: 4px solid #f59e0b !important;
        border-color: #f59e0b !important;
        opacity: 1 !important;
    }
    
    .step-icon {
        width: 3rem;
        height: 3rem;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 10px;
        font-size: 1.5rem;
        flex-shrink: 0;
        position: relative;
    }
    
    .step-card.active .step-icon {
        background: #3b82f6;
        color: white;
        animation: pulse-icon 1.5s ease-in-out infinite;
        position: relative;
    }
    
    .step-card.active .step-icon::after {
        content: '✨';
        position: absolute;
        top: -5px;
        right: -5px;
        font-size: 0.75rem;
        animation: sparkle-icon 1.5s ease-in-out infinite;
    }
    
    @keyframes sparkle-icon {
        0%, 100% { opacity: 1; transform: scale(1) rotate(0deg); }
        50% { opacity: 0.8; transform: scale(1.3) rotate(180deg); }
    }
    
    @keyframes pulse-icon {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    
    .step-card.completed .step-icon {
        background: #22c55e;
        color: white;
    }
    
    .step-card.pending .step-icon {
        background: #e5e7eb;
        color: #94a3b8;
    }
    
    .step-card.failed .step-icon {
        background: #ef4444;
        color: white;
    }
    
    .step-card.skipped .step-icon {
        background: #fbbf24 !important;
        color: white !important;
    }
    
    .step-card.skipped .step-title {
        color: #92400e !important;
    }
    
    .step-card.skipped .step-description {
        color: #a16207 !important;
    }
    
    .step-content {
        flex: 1;
    }
    
    .step-title {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 1.1rem;
        color: #1e293b;
        margin: 0 0 0.25rem 0;
    }
    
    .step-card.active .step-title {
        font-size: 1.2rem;
        color: #1e40af;
    }
    
    .step-card.completed .step-title {
        color: #166534;
    }
    
    .step-description {
        font-size: 0.875rem;
        color: #64748b;
        margin: 0;
        line-height: 1.4;
    }
    
    .step-card.active .step-description {
        color: #475569;
    }
    
    .step-status {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .step-card.completed .step-status {
        color: #22c55e;
    }
    
    .step-card.failed .step-status {
        color: #ef4444;
    }
    
    .step-card.skipped .step-status {
        color: #d97706;
        font-weight: 600;
    }
    
    /* Phase Grouping */
    .phase-group {
        margin: 2rem 0;
    }
    
    .phase-header {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #3b82f6;
    }
    
    .phase-title {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 1.1rem;
        color: #1e293b;
        margin: 0 0 0.25rem 0;
    }
    
    .phase-progress {
        font-size: 0.875rem;
        color: #64748b;
        margin: 0;
    }
    
    /* Animations */
    @keyframes pulse-glow {
        0%, 100% { 
            transform: scale(1); 
            box-shadow: 0 8px 16px rgba(59, 130, 246, 0.2); 
        }
        50% { 
            transform: scale(1.01); 
            box-shadow: 0 12px 24px rgba(59, 130, 246, 0.3); 
        }
    }
    
    @keyframes fade-in {
        from { 
            opacity: 0; 
            transform: translateY(-10px); 
        }
        to { 
            opacity: 1; 
            transform: translateY(0); 
        }
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    @keyframes sparkle {
        0%, 100% { 
            opacity: 1; 
            transform: scale(1) rotate(0deg); 
        }
        50% { 
            opacity: 0.7; 
            transform: scale(1.2) rotate(180deg); 
        }
    }
    
    @keyframes sparkle-icon {
        0%, 100% { 
            opacity: 1; 
            transform: scale(1) rotate(0deg); 
        }
        50% { 
            opacity: 0.8; 
            transform: scale(1.3) rotate(180deg); 
        }
    }
    
    .step-icon .fa-spinner {
        animation: spin 1s linear infinite;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER & BRANDING
# ============================================================================

# Encode sparkle icon image
sparkle_icon_path = os.path.join(os.path.dirname(__file__), 'sparkle-icon.png')
sparkle_icon_base64 = ""
if os.path.exists(sparkle_icon_path):
    with open(sparkle_icon_path, 'rb') as img_file:
        sparkle_icon_base64 = base64.b64encode(img_file.read()).decode()

# Professional header with clean layout
st.markdown(f"""
<div style='background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); 
            padding: 2rem 2.5rem; border-radius: 20px; margin-bottom: 2rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);'>
    <div style='display: flex; align-items: center; justify-content: space-between;'>
        <div>
            <h1 style='margin: 0; color: #ffffff; font-size: 2.25rem; font-weight: 700; 
                       font-family: "Poppins", sans-serif; letter-spacing: -0.02em;
                       position: relative; padding-right: 2rem;'>
                ⚕️ Clinical Decision Support
                <i class="fas fa-sparkles" style='position: absolute; top: 0; right: 0; color: #60a5fa; font-size: 1.1rem; animation: sparkle 2s ease-in-out infinite;'></i>
            </h1>
            <p style='margin: 0.5rem 0 0 0; color: #94a3b8; font-size: 1rem; font-weight: 500; display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;'>
                AI-Powered Clinical Intelligence • Powered by 
                <span style='position: relative; display: inline-flex; align-items: center; gap: 0.4rem;'>
                    <img src="data:image/png;base64,{sparkle_icon_base64}" style='width: 20px; height: 20px; filter: brightness(0) saturate(100%) invert(85%) sepia(100%) saturate(2000%) hue-rotate(15deg) brightness(1.1) contrast(1.2);' />
                    MedGemma
                    <img src="data:image/png;base64,{sparkle_icon_base64}" style='width: 20px; height: 20px; filter: brightness(0) saturate(100%) invert(85%) sepia(100%) saturate(2000%) hue-rotate(15deg) brightness(1.1) contrast(1.2);' />
                </span>
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
# AUDIO TRANSCRIPTION UTILITIES
# ============================================================================

def transcribe_audio_with_gemini(audio_bytes, mime_type="audio/wav"):
    """
    Transcribe audio using Gemini API.
    
    Args:
        audio_bytes: Audio data as bytes
        mime_type: MIME type of the audio (default: audio/wav)
    
    Returns:
        Transcribed text string, or None if transcription fails
    """
    try:
        # Check if API key is configured
        if not Config.GEMINI_API_KEY:
            return None
        
        # Import Gemini client
        from google import genai
        from google.genai import types
        
        # Initialize client with API key
        client = genai.Client(api_key=Config.GEMINI_API_KEY)
        
        # Use inline audio data approach (for files < 20MB)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                'Generate a transcript of the speech.',
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type=mime_type,
                )
            ]
        )
        
        # Extract transcribed text
        if response and hasattr(response, 'text'):
            return response.text.strip()
        else:
            return None
            
    except Exception as e:
        st.error(f"Transcription error: {str(e)}")
        return None

# ============================================================================
# PATIENT SELECTION DASHBOARD
# ============================================================================

# Load patient database from JSON file
def load_patient_database():
    """Load patient database from JSON file"""
    try:
        with open('demo_data/patient_database.json', 'r') as f:
            database = json.load(f)
            return database.get('patients', [])
    except FileNotFoundError:
        st.error("⚠️ demo_data/patient_database.json not found. Using fallback data.")
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
# AGENT PROGRESS DISPLAY - STEP MAPPING AND RENDERING
# ============================================================================

# Step definitions with user-friendly descriptions
# Ordered by phase and logical sequence
STEP_DEFINITIONS = {
    'FETCH_EHR': {
        'title': 'Reviewing Medical History',
        'icon': 'fa-file-medical',
        'description': 'Gathering patient demographics, conditions, and medical history',
        'phase': 1,
        'phase_name': 'Gathering Information',
        'order': 1
    },
    'FETCH_LABS': {
        'title': 'Analyzing Lab Results',
        'icon': 'fa-flask',
        'description': 'Reviewing laboratory test results and vital signs',
        'phase': 1,
        'phase_name': 'Gathering Information',
        'order': 2
    },
    'FETCH_MEDS': {
        'title': 'Reviewing Medications',
        'icon': 'fa-pills',
        'description': 'Checking current medications and dosages',
        'phase': 1,
        'phase_name': 'Gathering Information',
        'order': 3
    },
    'FETCH_IMAGING': {
        'title': 'Checking Imaging Reports',
        'icon': 'fa-x-ray',
        'description': 'Reviewing radiology and imaging studies',
        'phase': 1,
        'phase_name': 'Gathering Information',
        'order': 4
    },
    'CHECK_DDI': {
        'title': 'Screening Drug Interactions',
        'icon': 'fa-exclamation-triangle',
        'description': 'Checking for potential medication interactions',
        'phase': 2,
        'phase_name': 'Safety Analysis',
        'order': 1
    },
    'SAFETY_CHECK': {
        'title': 'Checking Safety Issues',
        'icon': 'fa-shield-halved',
        'description': 'Identifying safety concerns and contraindications',
        'phase': 2,
        'phase_name': 'Safety Analysis',
        'order': 2
    },
    'SEARCH_GUIDELINES': {
        'title': 'Consulting Clinical Guidelines',
        'icon': 'fa-book-medical',
        'description': 'Reviewing evidence-based treatment guidelines',
        'phase': 3,
        'phase_name': 'Clinical Analysis',
        'order': 1
    },
    'REASONING': {
        'title': 'Analyzing Information',
        'icon': 'fa-brain',
        'description': 'Processing all data to form clinical insights',
        'phase': 3,
        'phase_name': 'Clinical Analysis',
        'order': 2
    },
    'SYNTHESIS': {
        'title': 'Generating Clinical Summary',
        'icon': 'fa-stethoscope',
        'description': 'Creating diagnosis and treatment recommendations',
        'phase': 3,
        'phase_name': 'Clinical Analysis',
        'order': 3
    }
}

def translate_step_message(message: str) -> dict:
    """
    Translate technical agent messages to user-friendly step information.
    
    Handles multiple message formats:
    - Standard: "FETCH_EHR_STARTED", "FETCH_EHR_COMPLETED"
    - Intelligent agent: "EXECUTING_TOOL: get_ehr", "TOOL_COMPLETED: get_ehr"
    - Reasoning: "REASONING: ..."
    - Synthesis: "SYNTHESIS_STARTED", "SYNTHESIS_COMPLETED"
    
    Args:
        message: Technical message from agent
        
    Returns:
        Dict with step info or None if not recognized
    """
    message_upper = message.upper()
    
    # Map tool names to step keys (for intelligent agent format)
    tool_name_to_step_key = {
        'GET_EHR': 'FETCH_EHR',
        'GET_LABS': 'FETCH_LABS',
        'GET_MEDS': 'FETCH_MEDS',
        'GET_IMAGING': 'FETCH_IMAGING',
        'QUERY_DDI': 'CHECK_DDI',
        'SEARCH_GUIDELINES': 'SEARCH_GUIDELINES',
        'EHR': 'FETCH_EHR',
        'LABS': 'FETCH_LABS',
        'MEDS': 'FETCH_MEDS',
        'IMAGING': 'FETCH_IMAGING',
        'DDI': 'CHECK_DDI',
        'GUIDELINES': 'SEARCH_GUIDELINES'
    }
    
    # Extract step key from message
    step_key = None
    
    # First, try direct match with STEP_DEFINITIONS keys
    for key in STEP_DEFINITIONS.keys():
        if key in message_upper:
            step_key = key
            break
    
    # If not found, try tool name mapping (for intelligent agent format)
    if not step_key:
        for tool_name, mapped_key in tool_name_to_step_key.items():
            if tool_name in message_upper:
                step_key = mapped_key
                break
    
    # Handle special cases
    if not step_key:
        if 'REASONING' in message_upper or 'ANALYZING' in message_upper:
            step_key = 'REASONING'
        elif 'SYNTHESIS' in message_upper:
            step_key = 'SYNTHESIS'
        elif 'SAFETY' in message_upper and 'CHECK' in message_upper:
            step_key = 'SAFETY_CHECK'
    
    if not step_key:
        return None
    
    step_info = STEP_DEFINITIONS[step_key].copy()
    
    # Determine status
    if 'STARTED' in message_upper or 'EXECUTING' in message_upper or 'REASONING' in message_upper:
        step_info['status'] = 'active'
    elif 'COMPLETED' in message_upper:
        step_info['status'] = 'completed'
    elif 'FAILED' in message_upper or 'ERROR' in message_upper:
        step_info['status'] = 'failed'
    elif 'SKIPPED' in message_upper:
        step_info['status'] = 'skipped'
    else:
        # Default to active if we matched a step but status is unclear
        step_info['status'] = 'active'
    
    step_info['raw_message'] = message
    return step_info


def render_step_card(step_data: dict, state: str = None) -> str:
    """
    Render a single step card with modern styling.
    
    Args:
        step_data: Step information dict from translate_step_message
        state: Override state (active, completed, pending, failed, skipped)
        
    Returns:
        HTML string for the step card
    """
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
    
    # Build HTML output without extra whitespace
    status_div = f'<div class="step-status">{html.escape(status_text)}</div>' if status_text else ''
    
    html_output = f'<div class="step-card {status}" style="position: relative;"><div class="step-icon">{icon_html}</div>{ai_indicator}<div class="step-content"><div class="step-title">{title}</div><div class="step-description">{description}</div></div>{status_div}</div>'
    
    return html_output


def render_phase_group(phase_num: int, phase_name: str, steps: list, completed_count: int = 0) -> str:
    """
    Render a phase group with header and step cards.
    
    Args:
        phase_num: Phase number (1, 2, or 3)
        phase_name: Phase name
        steps: List of step cards HTML
        completed_count: Number of completed steps in this phase
        
    Returns:
        HTML string for the phase group
    """
    import html
    
    total_steps = len(steps)
    progress_text = f"{completed_count} of {total_steps} complete" if total_steps > 0 else ""
    
    # Phase descriptions for contextual help
    phase_descriptions = {
        1: "Collecting patient medical records, test results, and current medications",
        2: "Checking for drug interactions and safety concerns",
        3: "Analyzing data and generating clinical recommendations"
    }
    
    description = phase_descriptions.get(phase_num, "")
    
    steps_html = '\n'.join(steps)
    
    description_html = f'<div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.5rem;">{html.escape(description)}</div>' if description else ''
    
    html_output = f'<div class="phase-group"><div class="phase-header"><div class="phase-title" style="display: flex; align-items: center; gap: 0.5rem;"><i class="fas fa-sparkles" style="color: #3b82f6; font-size: 0.9rem;"></i>Phase {phase_num}: {html.escape(phase_name)}</div><div class="phase-progress">{html.escape(progress_text)}</div>{description_html}</div>{steps_html}</div>'
    
    return html_output


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
st.markdown("### 📝 Chief Complaint")

# Initialize session state for complaint text if not exists or patient changed
if 'complaint_text' not in st.session_state or st.session_state.get('last_patient_id') != patient_id:
    st.session_state.complaint_text = selected_patient_data['default_complaint']
    st.session_state.last_patient_id = patient_id

# Audio recording section with modern design
col_title_audio, col_recorder = st.columns([3, 1])
with col_title_audio:
    st.markdown('<p style="margin-bottom: 0.5rem; color: #64748b; font-size: 0.9rem;">Record audio complaint</p>', unsafe_allow_html=True)
with col_recorder:
    audio = audio_recorder("Record", "Stop", icon_name="microphone", icon_size="2x", 
                          neutral_color="#3b82f6", recording_color="#ef4444")

# Handle audio recording and transcription
if audio is not None and len(audio) > 0:
    # audio_recorder returns bytes directly
    audio_bytes = audio if isinstance(audio, bytes) else bytes(audio)
    
    # Check if this is a new recording (not already transcribed)
    audio_hash = hash(audio_bytes[:100]) if len(audio_bytes) > 100 else hash(audio_bytes)
    
    if st.session_state.get('last_audio_hash') != audio_hash:
        # Show recording status
        st.info("🎙️ Recording captured. Transcribing...")
        
        # Process audio transcription
        try:
            # Transcribe using Gemini (audio is already in bytes format)
            transcribed_text = transcribe_audio_with_gemini(audio_bytes, mime_type="audio/wav")
            
            if transcribed_text:
                # Replace (overwrite) the complaint text with transcribed text
                st.session_state.complaint_text = transcribed_text
                
                # Show success message
                st.success(f"✅ Transcribed: {transcribed_text[:50]}...")
                
                # Store audio hash to prevent re-transcription
                st.session_state.last_audio_hash = audio_hash
            else:
                # Show error if transcription failed
                if not Config.GEMINI_API_KEY:
                    st.warning("⚠️ GEMINI_API_KEY not configured. Please set it in your environment variables.")
                else:
                    st.error("❌ Transcription failed. Please try again.")
        except Exception as e:
            st.error(f"❌ Error processing audio: {str(e)}")
    
    # Display audio playback if available (audio is already bytes) - in collapsible section
    with st.expander("🎵 Playback recorded audio", expanded=False):
        st.audio(audio_bytes, format="audio/wav")

complaint = st.text_area(
    "Enter clinical complaint or reason for consultation",
    value=st.session_state.complaint_text,
    height=100,
    label_visibility="collapsed",
    help="Describe current symptoms, duration, and relevant context",
    key="complaint_input"
)

# Update session state when user manually edits the text
if complaint != st.session_state.complaint_text:
    st.session_state.complaint_text = complaint

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
        # MODERN STEP CARDS PROGRESS DISPLAY
        # ============================================================================
        
        st.markdown("")
        st.markdown("""
        <div style='display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;'>
            <i class="fas fa-sparkles" style='color: #3b82f6; font-size: 1.5rem; animation: sparkle 2s ease-in-out infinite;'></i>
            <h3 style='margin: 0; display: inline;'>AI-Powered Clinical Analysis in Progress</h3>
            <i class="fas fa-sparkles" style='color: #3b82f6; font-size: 1.5rem; animation: sparkle 2s ease-in-out infinite 0.5s;'></i>
        </div>
        <style>
        @keyframes sparkle {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.2); }
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown("<p style='color: #64748b; margin-bottom: 1.5rem;'>The AI assistant is reviewing patient information and generating clinical insights.</p>", unsafe_allow_html=True)
        
        # Progress display container
        progress_display_container = st.empty()
        
        logs = []
        
        # Track all steps by their key
        step_states = {}  # key -> state (pending, active, completed, failed, skipped)
        
        # Initialize all steps as pending
        for step_key in STEP_DEFINITIONS.keys():
            step_states[step_key] = 'pending'
        
        # Initial render to show all pending steps
        def render_all_steps():
            phase_1_steps = []
            phase_2_steps = []
            phase_3_steps = []
            
            phase_1_completed = 0
            phase_2_completed = 0
            phase_3_completed = 0
            
            # Group steps by phase, maintaining order
            phase_1_items = []
            phase_2_items = []
            phase_3_items = []
            
            for step_key, step_def in STEP_DEFINITIONS.items():
                state = step_states.get(step_key, 'pending')
                
                # Skip rendering steps that are still pending (not started, not completed, not skipped)
                # Only show steps that have been processed (active, completed, failed, or skipped)
                if state == 'pending':
                    # Check if any step in this phase has been processed
                    phase = step_def['phase']
                    phase_has_activity = False
                    for other_key, other_def in STEP_DEFINITIONS.items():
                        if other_def['phase'] == phase:
                            other_state = step_states.get(other_key, 'pending')
                            if other_state != 'pending':
                                phase_has_activity = True
                                break
                    
                    # If phase has no activity yet, skip rendering this step
                    if not phase_has_activity:
                        continue
                
                step_def_copy = step_def.copy()
                step_def_copy['status'] = state
                
                card_html = render_step_card(step_def_copy, state)
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
            
            # Sort by order and extract HTML
            phase_1_steps = [html for _, html, _ in sorted(phase_1_items)]
            phase_2_steps = [html for _, html, _ in sorted(phase_2_items)]
            phase_3_steps = [html for _, html, _ in sorted(phase_3_items)]
            
            # Render phase groups (only show phases that have activity and aren't all skipped)
            html_parts = []
            
            # Check if phases should be shown
            def phase_should_show(phase_num):
                """Check if phase should be displayed - show if has activity or at least one step processed"""
                phase_steps = [k for k, v in STEP_DEFINITIONS.items() if v['phase'] == phase_num]
                if not phase_steps:
                    return False
                
                # Get all states for this phase
                states = [step_states.get(k, 'pending') for k in phase_steps]
                
                # Hide if all steps are skipped (entire phase skipped)
                if all(s == 'skipped' for s in states):
                    return False
                
                # Show if any step is active, completed, failed, or skipped (has been processed)
                if any(s in ['active', 'completed', 'failed', 'skipped'] for s in states):
                    return True
                
                # Hide if all are still pending (phase hasn't started)
                return False
            
            phase_1_has_activity = phase_should_show(1)
            phase_2_has_activity = phase_should_show(2)
            phase_3_has_activity = phase_should_show(3)
            
            if phase_1_steps and phase_1_has_activity:
                html_parts.append(render_phase_group(1, 'Gathering Information', phase_1_steps, phase_1_completed))
            
            if phase_2_steps and phase_2_has_activity:
                html_parts.append(render_phase_group(2, 'Safety Analysis', phase_2_steps, phase_2_completed))
            
            if phase_3_steps and phase_3_has_activity:
                html_parts.append(render_phase_group(3, 'Clinical Analysis', phase_3_steps, phase_3_completed))
            
            return '\n'.join(html_parts)
        
        # Show initial state
        try:
            import streamlit.components.v1 as components
            progress_display_container.markdown(render_all_steps(), unsafe_allow_html=True)
        except:
            progress_display_container.markdown(render_all_steps(), unsafe_allow_html=True)
        
        def emit(message):
            """Callback to update progress with modern step cards."""
            logs.append({'message': message, 'timestamp': datetime.now()})
            
            # Translate message to step info
            step_info = translate_step_message(message)
            
            # Debug: Print message if it's not recognized (for troubleshooting)
            # if not step_info and any(keyword in message.upper() for keyword in ['FETCH', 'TOOL', 'COMPLETED', 'STARTED', 'SKIPPED']):
            #     print(f"Unrecognized message: {message}")
            
            if step_info:
                # Extract step key from the translated step info
                step_key = None
                message_upper = message.upper()
                
                # Map tool names to step keys
                tool_name_to_step_key = {
                    'GET_EHR': 'FETCH_EHR',
                    'GET_LABS': 'FETCH_LABS',
                    'GET_MEDS': 'FETCH_MEDS',
                    'GET_IMAGING': 'FETCH_IMAGING',
                    'QUERY_DDI': 'CHECK_DDI',
                    'SEARCH_GUIDELINES': 'SEARCH_GUIDELINES',
                    'EHR': 'FETCH_EHR',
                    'LABS': 'FETCH_LABS',
                    'MEDS': 'FETCH_MEDS',
                    'IMAGING': 'FETCH_IMAGING',
                    'DDI': 'CHECK_DDI',
                    'GUIDELINES': 'SEARCH_GUIDELINES'
                }
                
                # Try direct match first
                for key in STEP_DEFINITIONS.keys():
                    if key in message_upper:
                        step_key = key
                        break
                
                # Try tool name mapping (check for tool names in message)
                if not step_key:
                    # Check if message contains a tool name (e.g., "EXECUTING_TOOL: get_ehr" or "TOOL_COMPLETED: get_ehr")
                    for tool_name, mapped_key in tool_name_to_step_key.items():
                        # Check if tool name appears in the message (handle both "get_ehr" and "GET_EHR")
                        if tool_name in message_upper or tool_name.lower() in message.lower():
                            step_key = mapped_key
                            break
                    
                    # Also check for tool names directly (e.g., "get_ehr" -> "GET_EHR")
                    if not step_key:
                        # Extract tool name from messages like "EXECUTING_TOOL: get_ehr"
                        if ':' in message:
                            tool_part = message.split(':')[-1].strip().upper()
                            # Map common tool name variations
                            tool_variations = {
                                'GET_EHR': 'FETCH_EHR',
                                'GET_LABS': 'FETCH_LABS',
                                'GET_MEDS': 'FETCH_MEDS',
                                'GET_IMAGING': 'FETCH_IMAGING',
                                'QUERY_DDI': 'CHECK_DDI',
                                'SEARCH_GUIDELINES': 'SEARCH_GUIDELINES'
                            }
                            if tool_part in tool_variations:
                                step_key = tool_variations[tool_part]
                
                # Handle special cases
                if not step_key:
                    if 'REASONING' in message_upper:
                        step_key = 'REASONING'
                    elif 'SYNTHESIS' in message_upper:
                        step_key = 'SYNTHESIS'
                    elif 'SAFETY' in message_upper and 'CHECK' in message_upper:
                        step_key = 'SAFETY_CHECK'
                
                if step_key:
                    # Update step state based on message
                    if 'COMPLETED' in message_upper or 'TOOL_COMPLETED' in message_upper:
                        # Mark this step as completed
                        step_states[step_key] = 'completed'
                        # When a step completes, ensure any previously active step is also marked completed
                        for other_key in step_states:
                            if other_key != step_key and step_states[other_key] == 'active':
                                step_states[other_key] = 'completed'
                    elif 'FAILED' in message_upper or 'ERROR' in message_upper or 'TOOL_ERROR' in message_upper:
                        step_states[step_key] = 'failed'
                    elif 'SKIPPED' in message_upper:
                        step_states[step_key] = 'skipped'
                    elif 'STARTED' in message_upper or 'EXECUTING' in message_upper or 'REASONING' in message_upper:
                        # When a new step starts, mark previous active as completed
                        for other_key in step_states:
                            if other_key != step_key and step_states[other_key] == 'active':
                                step_states[other_key] = 'completed'
                        step_states[step_key] = 'active'
                    # Also handle implicit completion - if we see a new step starting and this one was active
                    # (This handles cases where COMPLETED message might be missing)
            
            # Add 0.5 second delay between step transitions for better UX
            import time
            time.sleep(0.5)
            
            # Update display using the render function
            progress_display_container.markdown(render_all_steps(), unsafe_allow_html=True)
        
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
