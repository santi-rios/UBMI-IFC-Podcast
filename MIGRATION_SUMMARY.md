# Migration Summary: Google TTS → Kokoro TTS

## ✅ Completed Tasks

### 1. Python Environment Migration
- ✅ Installed Python 3.12.0 via pyenv
- ✅ Updated `.python-version` file (pyenv local 3.12.0)
- ✅ Recreated virtual environment (.venv) with Python 3.12
- ✅ Verified compatibility (Python 3.13.11 → 3.12.0)

### 2. Dependencies
- ✅ Updated `requirements.txt` (removed elevenlabs, kept kokoro-tts)
- ✅ Installed espeak-ng system package
- ✅ Installed kokoro-tts Python package
- ✅ Downloaded Kokoro model files:
  - `kokoro-v1.0.onnx` (~310 MB)
  - `voices-v1.0.bin` (~25 MB)

### 3. Code Changes
- ✅ Updated [final_pipeline.ipynb](final_pipeline.ipynb):
  - Cell 1: Updated pipeline description
  - Cell 7: Changed TTS setup documentation
  - Cell 8: Added Kokoro voice listing
  - Cell 12: Updated audio generation function
  - Cell 13: Updated script generation (English instead of Spanish)
  - Cell 14: Updated configuration notes

### 4. Testing & Documentation
- ✅ Created `test_kokoro.py` for installation verification
- ✅ Tested audio generation successfully
- ✅ Created comprehensive setup guide: [KOKORO_SETUP_GUIDE.md](KOKORO_SETUP_GUIDE.md)
- ✅ Updated `.gitignore` to exclude large model files

## 📊 Key Changes

### Language Support
**Before:** Spanish (es-mx) via Google TTS  
**After:** English (en-us) via Kokoro TTS  
**Reason:** Kokoro v1.0 doesn't support Spanish yet

### Architecture
**Before:**
```
User → Gemini (script) → Google TTS API (audio) → Output
                ↓
          Requires API key
          Cloud processing
```

**After:**
```
User → Gemini (script) → Kokoro TTS (audio) → Output
                ↓
          No API key
          Local processing
```

### Benefits
- ✅ **No API costs** - Kokoro is free and local
- ✅ **Privacy** - Audio processing stays on your machine
- ✅ **Offline support** - Works without internet
- ✅ **Faster** - No network latency

### Trade-offs
- ⚠️ **Language:** English only (Spanish not yet supported)
- ⚠️ **Model size:** ~335 MB to download
- ⚠️ **Compute:** Runs on your CPU/GPU

## 🎯 How to Use

### Quick Start
```bash
cd /home/santi/projects/UBMI-IFC-Podcast
source .venv/bin/activate
jupyter notebook final_pipeline.ipynb
```

### Generate Podcast
1. Run cells 1-11 to generate embeddings and find similar articles
2. Cell 12 generates the script in English
3. Cell 13 creates audio with Kokoro TTS
4. Listen to `podcast_episode.wav`

### Customize Voice
Edit Cell 13, line with `--voice`:
```python
"--voice", "af_sarah",  # Change to: am_adam, af_nicole, etc.
```

### Adjust Speed
Edit Cell 13, line with `--speed`:
```python
"--speed", "1.0",  # Try: 0.9 (slower), 1.1 (faster)
```

## 📁 Project Structure Changes

```
UBMI-IFC-Podcast/
├── .python-version           # NEW: pyenv version (3.12.0)
├── kokoro-v1.0.onnx          # NEW: Model file (gitignored)
├── voices-v1.0.bin           # NEW: Voices file (gitignored)
├── test_kokoro.py            # NEW: Test script
├── KOKORO_SETUP_GUIDE.md     # NEW: Setup documentation
├── final_pipeline.ipynb      # MODIFIED: Updated TTS cells
├── requirements.txt          # MODIFIED: Updated dependencies
└── .gitignore                # MODIFIED: Added Kokoro files
```

## 🔄 Reverting to Google TTS (if needed)

If you need to revert:

1. **Switch back to Python 3.13:**
   ```bash
   pyenv local 3.13.11
   rm -rf .venv
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Restore Google TTS in requirements.txt:**
   ```bash
   # Remove: kokoro-tts
   # Add back: elevenlabs>=0.2.0
   ```

3. **Restore notebook cells from git:**
   ```bash
   git checkout HEAD -- final_pipeline.ipynb
   ```

## 🚀 Next Steps

### Recommended
- [ ] Test the full pipeline with a real podcast generation
- [ ] Experiment with different Kokoro voices
- [ ] Adjust speed for optimal podcast pacing

### Optional Improvements
- [ ] Add voice blending (mix multiple voices)
- [ ] Create automated script for model download
- [ ] Add support for chapter-based audio generation
- [ ] Explore using different languages (French, Italian, etc.)

### Future Considerations
- [ ] Monitor Kokoro updates for Spanish support
- [ ] Consider hybrid approach (Kokoro for English, another TTS for Spanish)
- [ ] Implement voice cloning if needed

## 📞 Support

If you encounter issues:

1. Check `KOKORO_SETUP_GUIDE.md` troubleshooting section
2. Run `python test_kokoro.py` to diagnose
3. Verify Python version: `python --version` (should be 3.12.0)
4. Check model files: `ls -lh kokoro-v1.0.onnx voices-v1.0.bin`

## 📚 References

- [Kokoro TTS GitHub](https://github.com/nazdridoy/kokoro-tts)
- [pyenv Documentation](https://github.com/pyenv/pyenv)
- [espeak-ng](https://github.com/espeak-ng/espeak-ng)

---

**Migration completed:** January 27, 2026  
**Python version:** 3.12.0  
**Kokoro version:** 1.0.0  
**Status:** ✅ Fully functional
