# UBMI-IFC-Podcast

Automated Scientific Podcast Generator for Instituto de Fisiología Celular (IFC-UNAM)

## Overview

This project creates an automated pipeline that:
1. **Scrapes** scientific publications from IFC-UNAM website (2021-2025)
2. **Analyzes** research themes using embeddings and clustering
3. **Searches** PubMed for recent relevant articles
4. **Generates** podcast scripts using LLMs
5. **Creates** audio podcasts using text-to-speech

## Project Structure

```
UBMI-IFC-Podcast/
├── src/                    # Source code
│   ├── scrapers/          # Web scraping modules
│   ├── embeddings/        # Embedding analysis
│   ├── pubmed/           # PubMed integration
│   ├── llm/              # LLM script generation
│   ├── audio/            # Audio generation
│   ├── utils/            # Utility functions
│   └── pipeline.py       # Main orchestrator
├── data/                  # Data storage
│   ├── raw/              # Raw scraped data
│   ├── processed/        # Processed data
│   └── embeddings/       # Embedding vectors
├── config/               # Configuration files
├── notebooks/            # Jupyter testing notebooks
├── outputs/              # Generated content
│   ├── scripts/          # Podcast scripts
│   └── podcasts/         # Audio files
├── tests/                # Unit tests
└── main.py              # Entry point

```

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd UBMI-IFC-Podcast

# RECOMMENDED: Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# OR: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

**📚 For detailed environment setup options, see [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md)**

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

Required API keys:
- OpenAI or Anthropic (for script generation)
- ElevenLabs or Azure Speech (for audio generation)
- PubMed email (required by NCBI)

### 3. Test Components

```bash
# Test individual components
python main.py --test-components

# Use Jupyter notebooks for detailed testing
jupyter lab notebooks/
```

### 4. Run Pipeline

```bash
# Run complete pipeline
python main.py --full

# Run step-by-step (for testing)
python main.py --step-by-step
```

## Pipeline Components

### 🕷️ IFC Scraper (`src/scrapers/ifc_scraper.py`)
- Scrapes publications from IFC-UNAM website
- Extracts titles, authors, abstracts, DOIs
- Handles rate limiting and error recovery

### 🔍 PubMed Searcher (`src/pubmed/searcher.py`)
- Searches recent PubMed articles
- Retrieves detailed article information
- Respects NCBI API guidelines

### 🧠 Embeddings Manager (`src/embeddings/manager.py`)
- Generates semantic embeddings for articles
- Clusters research themes
- Finds similar articles using cosine similarity

### 📝 Script Generator (`src/llm/script_generator.py`)
- Uses LLMs to create podcast scripts
- Generates episode metadata
- Formats content for audio conversion

### 🎵 Audio Generator (`src/audio/generator.py`)
- Converts scripts to speech using TTS
- Enhances audio quality
- Creates intro/outro segments

## Testing

### Individual Component Testing

Use the provided Jupyter notebooks:

```bash
# Start Jupyter
jupyter lab

# Test components individually:
# notebooks/01_test_ifc_scraper.ipynb
# notebooks/02_test_pubmed_search.ipynb
# notebooks/03_test_embeddings.ipynb      (create as needed)
# notebooks/04_test_llm_generation.ipynb  (create as needed)
# notebooks/05_test_audio_generation.ipynb (create as needed)
```

### Full Pipeline Testing

```bash
# Test with step-by-step execution
python main.py --step-by-step

# Test complete pipeline
python main.py --full --force-refresh
```

## Configuration

### Main Config (`config/config.yaml`)

```yaml
# IFC scraping settings
ifc:
  base_url: "https://www.ifc.unam.mx"
  years_range:
    start: 2021
    end: 2025
  rate_limit_delay: 1.0

# PubMed settings
pubmed:
  email: "your-email@example.com"  # Required!
  max_articles_per_week: 1000
  top_relevant_articles: 10

# LLM settings
llm:
  provider: "openai"  # or "anthropic"
  model: "gpt-4"
  temperature: 0.7

# Audio settings
audio:
  provider: "elevenlabs"  # or "azure"
  voice_id: "default"
```

### Environment Variables (`.env`)

```bash
# API Keys
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here

# PubMed (required)
PUBMED_EMAIL=your-email@example.com
```

## Development

### Adding New Components

1. Create module in appropriate `src/` subdirectory
2. Add configuration options to `config/config.yaml`
3. Create test notebook in `notebooks/`
4. Update pipeline in `src/pipeline.py`

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_scraper.py
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Install dependencies with `pip install -r requirements.txt`
2. **API Errors**: Check API keys in `.env` file
3. **Scraping Fails**: Website structure may have changed, update selectors
4. **Rate Limiting**: Increase delays in configuration
5. **Memory Issues**: Reduce batch sizes for large datasets

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py --full
```

### Component-Specific Issues

- **IFC Scraper**: Check `notebooks/01_test_ifc_scraper.ipynb`
- **PubMed**: Verify email configuration, check API limits
- **Embeddings**: Ensure sufficient memory for model loading
- **LLM**: Verify API keys and model availability
- **Audio**: Check TTS service quotas and voice availability

## Output

Generated content is saved to:
- **Scripts**: `outputs/scripts/podcast_script_YYYYMMDD_HHMMSS.md`
- **Audio**: `outputs/podcasts/podcast_YYYYMMDD_HHMMSS.mp3`
- **Metadata**: `episode_data_YYYYMMDD_HHMMSS.json`

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit pull request

## License

[Your License Here]

## Acknowledgments

- Instituto de Fisiología Celular, UNAM
- PubMed/NCBI for article access
- OpenAI/Anthropic for LLM services
- ElevenLabs for text-to-speech