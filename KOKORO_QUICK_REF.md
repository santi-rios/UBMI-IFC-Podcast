# 🎙️ Kokoro TTS Quick Reference

## One-Line Commands

### Setup (First Time)
```bash
./setup_kokoro.sh
```

### Daily Use
```bash
source .venv/bin/activate
jupyter notebook final_pipeline.ipynb
```

### Generate Test Audio
```bash
echo "Hello world" > test.txt && kokoro-tts test.txt output.wav --lang en-us --voice af_sarah && rm test.txt
```

## Common Voice Options

| Voice | Gender | Description |
|-------|--------|-------------|
| `af_sarah` | Female | Clear, professional |
| `af_nicole` | Female | Warm, friendly |
| `af_bella` | Female | Soft, gentle |
| `am_adam` | Male | Neutral, professional |
| `am_michael` | Male | Deep, authoritative |

## Language Codes
- `en-us` - English (US) ✅
- `en-gb` - English (UK)
- `fr-fr` - French
- `it` - Italian
- `ja` - Japanese
- `cmn` - Chinese

## Quick Fixes

### Wrong Python Version
```bash
pyenv local 3.12.0
rm -rf .venv && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Missing Model Files
```bash
wget https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx
wget https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin
```

### Test Installation
```bash
python test_kokoro.py
```

## Useful Commands

```bash
# List all voices
kokoro-tts --help-voices

# List languages  
kokoro-tts --help-languages

# Check Python version
python --version

# Verify packages
pip list | grep kokoro

# Check model files
ls -lh *.onnx *.bin
```

## File Locations

| File | Size | Location |
|------|------|----------|
| Model | ~310 MB | `kokoro-v1.0.onnx` |
| Voices | ~25 MB | `voices-v1.0.bin` |
| Test Script | <10 KB | `test_kokoro.py` |
| Setup Script | <5 KB | `setup_kokoro.sh` |

## Notebook Cells to Modify

| Cell | Purpose | What to Change |
|------|---------|----------------|
| 13 | Audio gen | Voice, speed |
| 12 | Script | Prompt, style |

## Common Errors

| Error | Fix |
|-------|-----|
| `Unsupported language: es-mx` | Use `en-us` instead |
| `Required model files are missing` | Run setup script or download manually |
| `Python 3.13+ is not supported` | Install Python 3.12 via pyenv |
| `espeak-ng: command not found` | `sudo apt-get install espeak-ng` |

## Performance Tips

- **Faster:** Increase speed to 1.1 or 1.2
- **Clearer:** Decrease speed to 0.9
- **More natural:** Use voice blending (e.g., `af_sarah:70,am_adam:30`)

---

**Need help?** Check `KOKORO_SETUP_GUIDE.md` or `MIGRATION_SUMMARY.md`
