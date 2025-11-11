# 👤 Patient Selection Feature - Doctor Decision Service

## 🎯 New Feature Added

The Doctor Decision & Prescription Management service now includes a **patient selection dropdown** with 5 diverse patient cases for testing different drug safety scenarios.

## 📋 Available Patients

### **P001 - John Smith (68yo Male)** 🎯 **DEMO PATIENT**
- **Conditions**: Osteoarthritis, CHF, CKD Stage 3b, Hypertension
- **Medications**: Lisinopril (ACE inhibitor), Furosemide, Metoprolol
- **Labs**: eGFR 35, Creatinine 2.1
- **Demo Scenario**: Prescribe Ibuprofen → 3 high-priority warnings
- **Alternative**: Acetaminophen

### **P002 - Sarah Johnson (45yo Female)**
- **Conditions**: Type 2 Diabetes, Hypertension, Hyperlipidemia
- **Medications**: Metformin, Lisinopril, Atorvastatin
- **Labs**: eGFR 85, HbA1c 7.2
- **Test Scenario**: Diabetes management, drug interactions

### **P003 - Michael Brown (72yo Male)**
- **Conditions**: Atrial Fibrillation, Hypertension, Osteoporosis
- **Medications**: Warfarin, Digoxin, Calcium
- **Labs**: INR 2.5, eGFR 65
- **Test Scenario**: Anticoagulation, bleeding risk

### **P004 - Emily Davis (35yo Female)**
- **Conditions**: Pregnancy (32 weeks), Gestational Diabetes, Anemia
- **Medications**: Prenatal vitamins, Iron, Folic acid
- **Labs**: Hemoglobin 10.5, Glucose 95
- **Test Scenario**: Pregnancy-safe medications

### **P005 - Robert Wilson (55yo Male)**
- **Conditions**: COPD, Smoking History, Depression
- **Medications**: Albuterol, Fluticasone, Sertraline
- **Labs**: Oxygen Sat 92%, FEV1 65%
- **Test Scenario**: Respiratory medications, drug interactions

## 🚀 How to Use Patient Selection

### **1. Start the Service**
```bash
python run_doctor_service.py
```

### **2. Access the Interface**
- **URL**: http://localhost:8503
- **Feature**: Patient selection dropdown at the top

### **3. Select a Patient**
1. **Dropdown Menu**: Choose from 5 patients
2. **Demo Button**: Click "🎯 Demo P001" for quick demo
3. **Patient Info**: View in sidebar (demographics, conditions, medications, labs)

### **4. Test Different Scenarios**
- **P001**: Ibuprofen safety demo (3 warnings)
- **P002**: Diabetes medication interactions
- **P003**: Warfarin bleeding risk scenarios
- **P004**: Pregnancy-safe medication testing
- **P005**: COPD medication interactions

## 🎯 Demo Scenarios by Patient

### **P001 - Ibuprofen Safety Demo**
1. Select P001 (or click "🎯 Demo P001")
2. Add prescription: "Ibuprofen 400mg three times daily"
3. Run safety check
4. **Result**: 3 high-priority warnings
   - Drug interaction with ACE inhibitor
   - Kidney function concern (eGFR 35)
   - Heart failure contraindication
5. **Alternative**: Acetaminophen suggested

### **P002 - Diabetes Management**
1. Select P002 (Sarah Johnson)
2. Test diabetes medications
3. Check for Metformin interactions
4. Review HbA1c management

### **P003 - Anticoagulation Safety**
1. Select P003 (Michael Brown)
2. Test anticoagulation scenarios
3. Check INR monitoring
4. Review bleeding risk factors

### **P004 - Pregnancy Safety**
1. Select P004 (Emily Davis)
2. Test pregnancy-safe medications
3. Check for teratogenic risks
4. Review prenatal care medications

### **P005 - COPD Management**
1. Select P005 (Robert Wilson)
2. Test respiratory medications
3. Check for drug interactions
4. Review oxygen saturation concerns

## 🔧 Technical Features

### **Patient Database Structure**
```json
{
  "patients": [
    {
      "patient_id": "P001",
      "name": "John Smith",
      "demographics": {"age": 68, "gender": "Male"},
      "conditions": ["Osteoarthritis", "CHF", "CKD Stage 3b"],
      "medications": ["Lisinopril", "Furosemide", "Metoprolol"],
      "labs": {"eGFR": 35, "Creatinine": 2.1},
      "visit_reason": "Joint pain - osteoarthritis"
    }
  ]
}
```

### **Key Features**
- **✅ Patient Dropdown**: Easy selection from 5 patients
- **✅ Demo Button**: Quick access to P001 demo scenario
- **✅ Patient Info Sidebar**: Complete medical history display
- **✅ Dynamic Loading**: Patient data updates based on selection
- **✅ Backward Compatibility**: Falls back to old patient_data.json

## 🎉 Benefits

### **✅ Diverse Testing Scenarios**
- Different age groups (35-72 years)
- Various medical conditions
- Multiple drug interaction scenarios
- Different safety check requirements

### **✅ Realistic Patient Cases**
- Complete medical histories
- Realistic lab values
- Current medication lists
- Visit reasons and symptoms

### **✅ Easy Demo Setup**
- One-click demo button for P001
- Clear patient identification
- Comprehensive medical information
- Professional interface

## 🚀 Ready to Test!

The patient selection feature is now fully integrated and ready for testing. Each patient provides a unique scenario for testing the drug safety agent's capabilities.

**Start the service and explore different patient scenarios!** 🎉
