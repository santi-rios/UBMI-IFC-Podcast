# Utility Scripts for UBMI-IFC-Podcast

This directory contains utility scripts for common tasks.

## Scripts

### Quick Setup
```bash
# Run initial setup
python setup.py

# Test all components
python main.py --test-components
```

### Development Helpers
```bash
# Format code
python -m black src/ --line-length 88

# Lint code
python -m flake8 src/ --max-line-length 88

# Run tests
pytest tests/ -v
```

### Data Management
```bash
# Clear cache data
rm -rf data/processed/ifc_articles_cache.json
rm -rf data/embeddings/*

# Clear outputs
rm -rf outputs/scripts/*
rm -rf outputs/podcasts/*
```

### Pipeline Operations
```bash
# Quick test run (last 10 articles)
python -c "
import asyncio
from src.pipeline import PodcastPipeline
pipeline = PodcastPipeline()
pipeline.config['pubmed']['max_articles_per_week'] = 10
pipeline.config['pubmed']['top_relevant_articles'] = 3
asyncio.run(pipeline.run_full_pipeline())
"

# Force refresh IFC data
python main.py --full --force-refresh

# Run specific pipeline step
python -c "
import asyncio
from src.pipeline import PodcastPipeline
pipeline = PodcastPipeline()
asyncio.run(pipeline._step_1_get_ifc_articles())
"
```

### Debugging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py --full

# Check configuration
python -c "from src.utils.config import load_config; import yaml; print(yaml.dump(load_config(), default_flow_style=False))"

# Test embeddings model
python -c "
from src.embeddings.manager import EmbeddingsManager
em = EmbeddingsManager()
em.load_model()
print('Model loaded successfully')
"
```

### Performance Monitoring
```bash
# Monitor memory usage during pipeline
python -c "
import psutil
import asyncio
from src.pipeline import PodcastPipeline

async def run_with_monitoring():
    process = psutil.Process()
    pipeline = PodcastPipeline()
    
    print(f'Initial memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
    
    results = await pipeline.run_full_pipeline()
    
    print(f'Final memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
    return results

asyncio.run(run_with_monitoring())
"
```

### API Testing
```bash
# Test OpenAI connection
python -c "
import os
from openai import OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
response = client.chat.completions.create(
    model='gpt-3.5-turbo',
    messages=[{'role': 'user', 'content': 'Hello, test'}],
    max_tokens=10
)
print('OpenAI connection OK:', response.choices[0].message.content)
"

# Test ElevenLabs connection
python -c "
import os
from elevenlabs import set_api_key, generate, voices
set_api_key(os.getenv('ELEVENLABS_API_KEY'))
voice_list = voices()
print(f'ElevenLabs connection OK, {len(voice_list)} voices available')
"
```

### Backup and Restore
```bash
# Backup generated content
tar -czf backup_$(date +%Y%m%d).tar.gz outputs/ data/processed/ data/embeddings/

# Restore from backup
tar -xzf backup_YYYYMMDD.tar.gz
```
