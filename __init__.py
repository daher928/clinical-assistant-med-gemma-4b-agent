"""
Clinical Assistant Agent

A production-ready clinical decision support system powered by MedGemma-4B.

Key Components:
- tools: Data retrieval from EHR, labs, meds, imaging, guidelines
- llm: MedGemma language model wrapper with singleton pattern
- agent: Orchestrator coordinating workflows
- frontend: Streamlit web interface

Usage:
    streamlit run frontend/app.py

For more information, see README.md
"""

__version__ = "1.0.0"
__author__ = "Clinical AI Team"

