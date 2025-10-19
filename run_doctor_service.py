#!/usr/bin/env python3
"""
Startup script for Doctor Decision & Prescription Management Service
Runs on port 8503
"""

import subprocess
import sys
import os

def main():
    """Start the doctor decision service"""
    print("🩺 Starting Doctor Decision & Prescription Management Service...")
    print("📍 Service will be available at: http://localhost:8503")
    print("🔧 Port: 8503")
    print("=" * 60)
    
    # Run the Streamlit app from the frontend directory
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            'frontend/doctor_decision_app.py',
            '--server.port', '8503',
            '--server.address', 'localhost',
            '--server.headless', 'true'
        ])
    except KeyboardInterrupt:
        print("\n🛑 Service stopped by user")
    except Exception as e:
        print(f"❌ Error starting service: {e}")

if __name__ == "__main__":
    main()
