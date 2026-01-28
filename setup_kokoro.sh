#!/bin/bash
# Kokoro TTS Setup Script for UBMI-IFC-Podcast
# This script automates the setup process for new environments

set -e  # Exit on error

echo "🚀 Kokoro TTS Setup Script"
echo "=" | sed 's/./=/g' | head -c 50; echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in project directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Error: Must run from project root directory${NC}"
    echo "   Expected: /home/santi/projects/UBMI-IFC-Podcast"
    exit 1
fi

echo -e "${GREEN}✅ Running in project directory${NC}"

# 1. Check Python version
echo ""
echo "📍 Step 1: Checking Python version..."
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.12"

if [[ "$PYTHON_VERSION" == "$REQUIRED_VERSION"* ]]; then
    echo -e "${GREEN}✅ Python $PYTHON_VERSION detected${NC}"
else
    echo -e "${YELLOW}⚠️  Python version mismatch${NC}"
    echo "   Current: $PYTHON_VERSION"
    echo "   Required: 3.12.x"
    echo ""
    echo "   Setting Python 3.12.0 via pyenv..."
    
    # Check if pyenv is installed
    if ! command -v pyenv &> /dev/null; then
        echo -e "${RED}❌ pyenv not found. Installing...${NC}"
        curl https://pyenv.run | bash
        export PATH="$HOME/.pyenv/bin:$PATH"
        eval "$(pyenv init -)"
    fi
    
    # Install Python 3.12.0 if not present
    if ! pyenv versions | grep -q "3.12.0"; then
        echo "   Installing Python 3.12.0..."
        pyenv install 3.12.0
    fi
    
    # Set local version
    pyenv local 3.12.0
    echo -e "${GREEN}✅ Python 3.12.0 set via pyenv${NC}"
fi

# 2. Check virtual environment
echo ""
echo "📍 Step 2: Setting up virtual environment..."
if [ -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment exists${NC}"
    read -p "   Recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .venv
        python3 -m venv .venv
        echo -e "${GREEN}✅ Virtual environment recreated${NC}"
    fi
else
    python3 -m venv .venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
source .venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# 3. Install system dependencies
echo ""
echo "📍 Step 3: Checking system dependencies..."
if ! command -v espeak-ng &> /dev/null; then
    echo -e "${YELLOW}⚠️  espeak-ng not found. Installing...${NC}"
    sudo apt-get update
    sudo apt-get install -y espeak-ng
    echo -e "${GREEN}✅ espeak-ng installed${NC}"
else
    echo -e "${GREEN}✅ espeak-ng already installed${NC}"
fi

# 4. Install Python packages
echo ""
echo "📍 Step 4: Installing Python packages..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✅ Python packages installed${NC}"

# 5. Download Kokoro model files
echo ""
echo "📍 Step 5: Checking Kokoro model files..."

MODEL_FILE="kokoro-v1.0.onnx"
VOICES_FILE="voices-v1.0.bin"
BASE_URL="https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0"

if [ ! -f "$MODEL_FILE" ]; then
    echo "   Downloading $MODEL_FILE (~310 MB)..."
    wget -q --show-progress "$BASE_URL/$MODEL_FILE"
    echo -e "${GREEN}✅ Model file downloaded${NC}"
else
    echo -e "${GREEN}✅ Model file exists${NC}"
fi

if [ ! -f "$VOICES_FILE" ]; then
    echo "   Downloading $VOICES_FILE (~25 MB)..."
    wget -q --show-progress "$BASE_URL/$VOICES_FILE"
    echo -e "${GREEN}✅ Voices file downloaded${NC}"
else
    echo -e "${GREEN}✅ Voices file exists${NC}"
fi

# 6. Test installation
echo ""
echo "📍 Step 6: Testing Kokoro TTS installation..."
echo "This is a test of Kokoro TTS." > /tmp/kokoro_test.txt

if kokoro-tts /tmp/kokoro_test.txt /tmp/kokoro_test.wav --lang en-us --voice af_sarah 2>&1 | grep -q "Created"; then
    echo -e "${GREEN}✅ Kokoro TTS test successful${NC}"
    rm /tmp/kokoro_test.txt /tmp/kokoro_test.wav
else
    echo -e "${RED}❌ Kokoro TTS test failed${NC}"
    echo "   Run 'python test_kokoro.py' for detailed diagnostics"
fi

# Summary
echo ""
echo "=" | sed 's/./=/g' | head -c 50; echo ""
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Activate environment: source .venv/bin/activate"
echo "  2. Start Jupyter: jupyter notebook final_pipeline.ipynb"
echo "  3. Run all cells to generate podcast"
echo ""
echo "Available voices: kokoro-tts --help-voices"
echo "Test installation: python test_kokoro.py"
echo ""
echo "Documentation:"
echo "  - KOKORO_SETUP_GUIDE.md"
echo "  - MIGRATION_SUMMARY.md"
echo ""
