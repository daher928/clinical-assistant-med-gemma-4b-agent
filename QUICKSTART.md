# 🚀 Quick Start Guide

Get the Clinical Assistant Agent running in **under 5 minutes**.

## Option 1: Fast Testing (Mock Mode) - Recommended First

```bash
# 1. Run the automated setup
./setup.sh

# 2. Set mock mode
export USE_MOCK_LLM=true

# 3. Launch the app
streamlit run frontend/app.py
```

**What you get:**
- ✅ Instant startup (no model download)
- ✅ Full UI and workflow testing
- ✅ Real data pipeline validation
- ✅ Perfect for development

The app will open at http://localhost:8501

## Option 2: Full Model (Production Mode)

```bash
# 1. Ensure you have 16GB+ RAM and 20GB free disk space

# 2. Run setup
./setup.sh

# 3. Disable mock mode
export USE_MOCK_LLM=false

# 4. Launch (first run downloads 8GB model - takes 5-10 min)
streamlit run frontend/app.py
```

**First time:**
- Model download: 5-10 minutes
- Model loading: 2-5 minutes
- Subsequent runs: Fast (model cached)

## Using the Interface

### 1. Select a Patient
- **P001**: 68M with CKD, Diabetes, HTN
- **P002**: 45F with Asthma, Migraines

### 2. Review/Edit Complaint
Pre-filled complaints are provided, or write your own.

### 3. Configure Settings (Sidebar)
- Toggle Mock Mode
- View device info
- Check model status

### 4. Run Agent
Click "🚀 Run Agent" and watch real-time progress:
- ⏳ Fetching EHR...
- ⏳ Retrieving labs...
- ⏳ Checking medications...
- ⏳ Analyzing imaging...
- ⏳ Screening drug interactions...
- ⏳ Searching guidelines...
- ⏳ Synthesizing results...
- ✅ Complete!

### 5. Review Results
Three tabs available:
- **📄 Summary**: Formatted clinical output
- **🔍 Raw Output**: Plain text version
- **📋 Logs**: Detailed execution trace

### 6. Download Report
Export results as text file for record-keeping.

## Troubleshooting

### "Command not found: streamlit"
```bash
source medgemma_env/bin/activate
pip install streamlit
```

### "Out of memory" error
```bash
# Use mock mode or switch to CPU
export USE_MOCK_LLM=true
```

### "Patient data not found"
```bash
# Verify you're in project root
ls demo_data/ehr/  # Should show P001_ehr.json, P002_ehr.json
```

### Model loading hangs
```bash
# Check device compatibility
python3 -c "import torch; print(torch.cuda.is_available(), torch.backends.mps.is_available())"

# Fall back to CPU if needed
export USE_MOCK_LLM=true
```

## Environment Variables

```bash
# Model selection
export MODEL_ID="google/medgemma-4b-it"

# Enable/disable mock mode
export USE_MOCK_LLM="true"  # or "false"

# Generation parameters
export MAX_NEW_TOKENS="800"
export TEMPERATURE="0.7"
```

## What to Try

### Test Case 1: CKD Patient with Rising Creatinine
- Select: P001
- Complaint: "Fatigue and dizziness for 2 weeks"
- Expect: DDI warnings, renal dosing alerts, CKD guidelines

### Test Case 2: Asthma Exacerbation
- Select: P002
- Complaint: "Increased shortness of breath and wheezing"
- Expect: Asthma management guidelines, serotonin syndrome warning

### Test Case 3: Custom Scenario
- Select any patient
- Write your own complaint
- Observe dynamic guideline search

## Next Steps

- 📖 Read full [README.md](README.md) for architecture details
- 🔧 Explore `config.py` for customization
- 📊 Add your own patient data in `demo_data/`
- 🛠️ Extend tools in `tools/` directory
- 🧠 Integrate LangGraph for complex workflows

## Tips

1. **Start with Mock Mode** to understand the workflow
2. **Check logs tab** to see what data was retrieved
3. **Try different complaints** to see guideline search adapt
4. **Monitor memory** when running full model
5. **Cache results** - the UI saves last run

## Support

Issues? Check:
- Python version (3.8+)
- Virtual environment activated
- All dependencies installed
- Sufficient RAM for full mode
- Demo data files present

Still stuck? Review error messages in the terminal where you ran `streamlit run`.

---

**Happy Testing! 🎉**

*Remember: This is a demo system. Not for clinical use.*

