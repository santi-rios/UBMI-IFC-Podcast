# Kokoro TTS Setup Guide

This guide documents the migration from Google TTS API to Kokoro TTS (local, no API key needed).

## 🎯 Summary of Changes

### Python Version Update
- **Old:** Python 3.13.11
- **New:** Python 3.12.0 (via pyenv)
- **Reason:** Kokoro requires Python 3.9-3.12

### TTS System Update
- **Old:** Google TTS API (cloud-based, requires API key)
- **New:** Kokoro TTS (local, no API key needed)
- **Language:** Changed from Spanish to English (Kokoro v1.0 doesn't support Spanish yet)

## 📋 Prerequisites

### 1. System Dependencies
```bash
# Install espeak-ng (required for Kokoro)
sudo apt-get update
sudo apt-get install espeak-ng
```

### 2. Python Version Management (pyenv)
```bash
# Install pyenv (if not already installed)
curl https://pyenv.run | bash

# Add to your ~/.bashrc or ~/.zshrc
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# Reload shell
source ~/.bashrc  # or source ~/.zshrc
```

## 🚀 Installation Steps

### 1. Install Python 3.12.0
```bash
cd /home/santi/projects/UBMI-IFC-Podcast
pyenv install 3.12.0
pyenv local 3.12.0
```

### 2. Create Virtual Environment
```bash
# Remove old venv (if exists)
rm -rf .venv

# Create new venv with Python 3.12
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Python Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install all requirements (including kokoro-tts)
pip install -r requirements.txt
```

### 4. Download Kokoro Model Files
```bash
# Download model (~310 MB)
wget https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx

# Download voices (~25 MB)
wget https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin
```

These files should be in your project root directory.

## 🧪 Testing Installation

Run the test script:
```bash
source .venv/bin/activate
python test_kokoro.py
```

Or test manually:
```bash
echo "Welcome to the Institute’s Daily Brief. I’m your host, and today we’re evaluating our new synthesis engine, Kokoro, using recent metadata from PubMed.

This is a rigorous stress test for natural language processing. For instance, how does the model handle complex nomenclature like 'Phosphatidylinositol 3-kinase' or the nuances of in vivo versus in vitro studies?

We are specifically looking for a balanced prosody—one that avoids a robotic drone while maintaining the professional gravitas required for high-impact research. Let’s dive into today’s breakthroughs in molecular biology and clinical therapeutics. We hope you enjoy the insights!" > test.txt
kokoro-tts test.txt output_long.wav --lang en-us --voice af_sarah
rm test.txt output.wav
```

## 📖 Kokoro TTS Usage

### Command Line
```bash
kokoro-tts input.txt output.wav --lang en-us --voice af_sarah --speed 1.0
```

### Available Options

**Languages:**
- `en-us` - English (US)
- `en-gb` - English (UK)
- `fr-fr` - French
- `it` - Italian
- `ja` - Japanese
- `cmn` - Chinese (Mandarin)

**Voices:**
- Female: `af_sarah`, `af_nicole`, `af_bella`, `af_nova`, etc.
- Male: `am_adam`, `am_michael`, etc.

View all voices:
```bash
kokoro-tts --help-voices
```

**Voice Blending:**
```bash
# Mix two voices (60% sarah, 40% adam)
kokoro-tts input.txt output.wav --voice "af_sarah:60,am_adam:40"
```

## 📝 Notebook Changes

### Modified Cells
1. **Setup cell** - Updated documentation
2. **TTS import cell** - Changed from Google TTS to Kokoro
3. **Audio generation cell** - Complete rewrite for Kokoro
4. **Script generation cell** - Changed from Spanish to English

### Key Code Changes

**Before (Google TTS):**
```python
from google.cloud import texttospeech
client = texttospeech.TextToSpeechClient()
# Required API key configuration
```

**After (Kokoro):**
```python
import subprocess
# No API key needed - local processing
cmd = ["kokoro-tts", input_file, output_file, "--lang", "en-us", "--voice", "af_sarah"]
subprocess.run(cmd)
```

## 🔧 Troubleshooting

### Python Version Issues
```bash
# Verify Python version
python --version  # Should show 3.12.0

# If wrong version
pyenv local 3.12.0
```

### Missing Model Files
```bash
# Check if files exist
ls -lh kokoro-v1.0.onnx voices-v1.0.bin

# Re-download if missing
wget https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx
wget https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin
```

### espeak-ng Not Found
```bash
sudo apt-get update
sudo apt-get install espeak-ng
```

### Virtual Environment Issues
```bash
# Deactivate current venv
deactivate

# Remove and recreate
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 📊 Comparison: Google TTS vs Kokoro

| Feature | Google TTS | Kokoro TTS |
|---------|-----------|------------|
| Cost | Paid (API usage) | Free |
| Location | Cloud-based | Local |
| API Key | Required | Not required |
| Spanish Support | ✅ Yes | ❌ No (v1.0) |
| English Support | ✅ Yes | ✅ Yes |
| Voice Quality | High | High |
| Offline Usage | ❌ No | ✅ Yes |
| Speed | Network dependent | Fast (local) |
| Privacy | Data sent to Google | 100% private |

## 🎤 Voice Recommendations

For professional podcasts:
- **Female voice:** `af_sarah` or `af_nicole` (clear, professional)
- **Male voice:** `am_adam` (warm, engaging)
- **Speed:** 1.0 (natural), 1.1 (slightly faster), 0.9 (slower, clearer)

## 📚 Additional Resources

- [Kokoro TTS GitHub](https://github.com/nazdridoy/kokoro-tts)
- [Kokoro Documentation](https://github.com/nazdridoy/kokoro-tts/blob/main/README.md)
- [espeak-ng Documentation](https://github.com/espeak-ng/espeak-ng)

## ✅ Quick Checklist

- [ ] Python 3.12.0 installed via pyenv
- [ ] Virtual environment created and activated
- [ ] espeak-ng installed
- [ ] kokoro-tts installed (`pip list | grep kokoro`)
- [ ] Model files downloaded (kokoro-v1.0.onnx, voices-v1.0.bin)
- [ ] Test successful (`python test_kokoro.py`)
- [ ] Notebook cells updated

## 🔄 Workflow

1. **Generate script** (in English via Gemini)
2. **Clean script** (remove stage directions)
3. **Generate audio** (Kokoro TTS)
4. **Listen and adjust** (change voice/speed if needed)

---

**Last updated:** January 27, 2026
**Python Version:** 3.12.0
**Kokoro Version:** 1.0.0
