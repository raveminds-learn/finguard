#!/bin/bash

echo "================================"
echo "FinGuard Setup Script"
echo "================================"
echo ""

# Check Python version
echo "🔍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "   Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check Ollama
echo ""
echo "🔍 Checking Ollama installation..."
if command -v ollama &> /dev/null
then
    echo "   ✅ Ollama found"
    
    # Check if llama3.3 model exists
    if ollama list | grep -q "llama3.3"
    then
        echo "   ✅ llama3.3 model installed"
    else
        echo "   📥 Downloading llama3.3 model..."
        ollama pull llama3.3:latest
    fi
else
    echo "   ❌ Ollama not found"
    echo "   Please install Ollama from: https://ollama.ai"
    echo "   Then run: ollama pull llama3.3:latest"
fi

# Initialize database
echo ""
echo "🗄️  Initializing database..."
python backend/setup_db.py

echo ""
echo "================================"
echo "✅ Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "  1. Activate environment: source venv/bin/activate"
echo "  2. Process sample data: python main.py --sample"
echo "  3. Launch dashboard: streamlit run dashboard/app.py"
echo ""
echo "Make sure Ollama is running: ollama serve"
echo ""
