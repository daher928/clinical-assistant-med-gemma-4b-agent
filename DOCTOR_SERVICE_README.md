# 🩺 Doctor Decision & Prescription Management Service

A separate Streamlit service for handling doctor decisions and prescription safety checks.

## 🚀 Quick Start

### Run the Service
```bash
# Start the doctor decision service
python run_doctor_service.py
```

### Access the Service
- **URL**: http://localhost:8503
- **Port**: 8503
- **Service**: Doctor Decision & Prescription Management

## 🎯 Features

### 📋 Patient Information
- Patient demographics and medical history
- Current conditions and allergies
- Current medications and recent labs
- Sidebar display for easy reference

### 💊 Prescription Management
- Add multiple prescriptions
- Drug name, dose, frequency, duration
- Special instructions for each prescription
- Remove prescriptions as needed

### 🛡️ Safety Analysis
- Comprehensive drug safety checks
- Drug-drug interaction warnings
- Allergy contraindication alerts
- Condition-based contraindications
- Severity-based warning system (Critical, High, Medium, Low)

### 📝 Treatment Notes
- Additional treatment decisions
- Follow-up plans
- Clinical notes

## 🔧 Technical Details

### File Structure
```
frontend/
├── doctor_decision_app.py    # Main service application
├── app.py                    # Main clinical analysis app (port 8501)
└── ...

run_doctor_service.py         # Startup script for doctor service
patient_data.json            # Sample patient data
```

### Key Functions
- `initialize_session_state()` - Initialize Streamlit session state
- `load_patient_data()` - Load patient information
- `run_safety_check()` - Perform drug safety analysis
- `main()` - Main application function

### Safety Check Features
- **Drug Interactions**: Check for dangerous drug combinations
- **Allergy Checks**: Verify against patient allergies
- **Contraindications**: Check for condition-based restrictions
- **Dosage Validation**: Basic dosage appropriateness checks

## 🌐 Service Architecture

### Main Clinical App (Port 8501)
- Clinical data analysis
- Multi-agent system
- Diagnostic recommendations
- Data insights and execution logs

### Doctor Decision Service (Port 8503)
- Prescription management
- Drug safety analysis
- Treatment plan creation
- Safety warnings and alerts

## 🚀 Usage Workflow

1. **Run Main App**: Start the clinical analysis service
2. **Analyze Patient**: Get diagnostic recommendations
3. **Open Doctor Service**: Navigate to http://localhost:8503
4. **Review Patient Data**: Check patient information in sidebar
5. **Add Prescriptions**: Enter treatment decisions
6. **Run Safety Check**: Analyze drug safety
7. **Review Warnings**: Address any safety concerns
8. **Finalize Treatment**: Complete treatment plan

## 🔒 Safety Features

### Warning Severity Levels
- **🚨 Critical**: Immediate action required (allergies, severe interactions)
- **⚠️ High**: Important safety concerns (contraindications, major interactions)
- **ℹ️ Medium**: Moderate concerns (dosing, monitoring)
- **📝 Low**: Additional notes and recommendations

### Safety Checks Include
- Drug-drug interactions
- Allergy contraindications
- Condition-based contraindications
- Basic dosage validation
- Patient-specific warnings

## 📊 Benefits

### ✅ Complete Isolation
- No conflicts with main application
- Independent service architecture
- Clean separation of concerns

### ✅ Professional Interface
- Medical-grade UI design
- Clear safety warnings
- Intuitive prescription management

### ✅ Comprehensive Safety
- Multi-layered safety checks
- Severity-based warnings
- Professional clinical workflow

## 🎉 Ready to Use!

The doctor decision service is now completely separate and ready to use. Simply run:

```bash
python run_doctor_service.py
```

And navigate to http://localhost:8503 to start managing prescriptions and treatment decisions!
