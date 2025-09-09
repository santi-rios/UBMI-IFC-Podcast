# Dependency Management Guide

## 🐍 Python Environment Options

### Option 1: Virtual Environment (Recommended)

**Create and use a virtual environment:**

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run setup
python setup.py
```

**Benefits:**
- ✅ Isolated dependencies
- ✅ No conflicts with system Python
- ✅ Easy to delete/recreate
- ✅ Reproducible environments

### Option 2: Conda Environment

```bash
# Create conda environment
conda create -n ubmi-podcast python=3.11
conda activate ubmi-podcast

# Install dependencies
pip install -r requirements.txt
# OR use conda when possible:
conda install pandas numpy scikit-learn jupyter

# Run setup
python setup.py
```

### Option 3: Global Installation (Not Recommended)

```bash
# Install globally (use with caution)
pip install -r requirements.txt

# Or install for current user only
pip install --user -r requirements.txt
```

## 🔍 Check Current Environment

```bash
# Check if in virtual environment
python -c "import sys; print('Virtual env:' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 'Global Python')"

# Check where packages are installed
python -c "import site; print('Packages location:', site.getsitepackages())"

# Check Python executable location
which python
# or
python -c "import sys; print(sys.executable)"
```

## 🛠️ Automated Setup Options

### Quick Setup with Virtual Environment

```bash
# Automated setup with venv
python setup.py

# If not in venv, it will offer to create one
# Choose option: "create-venv"
```

### Manual Virtual Environment Setup

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# 3. Upgrade pip
pip install --upgrade pip

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run setup
python setup.py
```

## 📦 Key Dependencies

### Core Dependencies (Required)
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `PyYAML` - Configuration files

### ML/AI Dependencies (Required for full functionality)
- `scikit-learn` - Machine learning
- `sentence-transformers` - Text embeddings
- `torch` - Deep learning backend

### API Dependencies (Optional, based on your choice)
- `openai` - OpenAI API
- `anthropic` - Anthropic API
- `elevenlabs` - ElevenLabs TTS

### Development Dependencies
- `jupyter` - Interactive notebooks
- `pytest` - Testing
- `black` - Code formatting

## 🚨 Common Issues

### Issue: "Module not found" errors
**Solution:** Check if you're in the right environment
```bash
which python
pip list | grep requests
```

### Issue: Permission denied during installation
**Solutions:**
```bash
# Option 1: Use virtual environment
python -m venv venv && source venv/bin/activate

# Option 2: User installation
pip install --user -r requirements.txt

# Option 3: Upgrade pip
pip install --upgrade pip
```

### Issue: Different Python versions
**Solution:** Specify Python version
```bash
# Use specific Python version
python3.11 -m venv venv
# or
/usr/bin/python3 -m venv venv
```

### Issue: Conda vs pip conflicts
**Solution:** Prefer conda for scientific packages
```bash
# Install via conda first
conda install pandas numpy scikit-learn

# Then pip for remaining packages
pip install sentence-transformers openai
```

## 🎯 Recommended Workflow

1. **Create isolated environment**
2. **Install dependencies in environment**
3. **Verify installation with setup script**
4. **Test components individually**
5. **Run full pipeline**

```bash
# Complete workflow
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python setup.py
python main.py --test-components
```

## 💡 Pro Tips

- **Use `requirements.txt`** for reproducible installations
- **Pin versions** for production: `requests==2.31.0`
- **Separate dev dependencies** in `requirements-dev.txt`
- **Document your environment** with `pip freeze > requirements-lock.txt`
- **Use `.python-version`** file for pyenv users

## 📊 Environment Verification

After setup, verify your environment:

```bash
# Check Python version and location
python --version
which python

# Check key packages
python -c "import requests, pandas, numpy; print('Core packages OK')"
python -c "import sklearn, sentence_transformers; print('ML packages OK')"

# Check package locations
python -c "import requests; print('Requests location:', requests.__file__)"
```
