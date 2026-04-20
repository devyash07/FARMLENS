#!/bin/bash

# Setup script for Python 3.12 virtual environment with TensorFlow support

echo "🔧 Setting up Python 3.12 virtual environment with TensorFlow..."

# Check if Python 3.12 is installed
if ! command -v /opt/homebrew/bin/python3.12 &> /dev/null; then
    echo "❌ Python 3.12 not found. Installing via Homebrew..."
    brew install python@3.12
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv312" ]; then
    echo "📦 Creating virtual environment with Python 3.12..."
    /opt/homebrew/bin/python3.12 -m venv venv312
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv312/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install TensorFlow first (large package)
echo "📥 Installing TensorFlow (this may take a while)..."
pip install --resume-retries 20 tensorflow

# Install remaining packages
echo "📥 Installing PyTorch, OpenCV, and other packages..."
pip install torch torchvision opencv-python fastapi uvicorn ollama

# Install other dependencies from requirements.txt if it exists
if [ -f "requirements.txt" ]; then
    echo "📥 Installing additional dependencies from requirements.txt..."
    pip install -r requirements.txt
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Installed packages:"
pip list | grep -E "(torch|tensorflow|opencv|fastapi|uvicorn|ollama)"
echo ""
echo "Python version: $(python --version)"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source venv312/bin/activate"
echo ""
echo "To deactivate, run:"
echo "  deactivate"
echo ""
echo "To start the backend server:"
echo "  python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001"
