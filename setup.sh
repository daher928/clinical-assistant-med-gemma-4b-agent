#!/bin/bash

# Clinical Assistant Agent - Setup Script

echo "🩺 Clinical Assistant Agent - Setup"
echo "===================================="
echo ""

# Check Python version
echo "📍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "medgemma_env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv medgemma_env
    echo "   ✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source medgemma_env/bin/activate
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip -q
echo "   ✅ Pip upgraded"
echo ""

# Install requirements
echo "📥 Installing dependencies..."
echo "   This may take a few minutes..."
pip install -r requirements.txt -q
echo "   ✅ Dependencies installed"
echo ""

# Verify installation
echo "🔍 Verifying installation..."
python3 -c "import torch; import transformers; import streamlit; print('   ✅ All core packages imported successfully')"
echo ""

# Display next steps
echo "✅ Setup complete!"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Activate the environment (if not already):"
echo "   source medgemma_env/bin/activate"
echo ""
echo "2. Run in Mock Mode (fast, no model download):"
echo "   export USE_MOCK_LLM=true"
echo "   streamlit run frontend/app.py"
echo ""
echo "3. Or run with real MedGemma model (requires 16GB+ RAM, 8GB download):"
echo "   export USE_MOCK_LLM=false"
echo "   streamlit run frontend/app.py"
echo ""
echo "🌐 The app will open in your browser at http://localhost:8501"
echo ""
echo "📚 For more information, see README.md"
echo ""

