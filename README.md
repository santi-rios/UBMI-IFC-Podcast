# Automated Scientific Podcast Generator

This project is an automated pipeline that transforms scientific publications from the Instituto de Fisiología Celular (IFC-UNAM) into engaging podcasts. It scrapes publication data, analyzes research trends, finds related articles, and uses AI to generate and voice podcast scripts.

## Features

- **Web Scraping**: Gathers publication data from the IFC-UNAM website.
- **AI-Powered Analysis**: Uses embeddings and language models to identify research themes and generate content.
- **Podcast Production**: Automatically generates podcast scripts and converts them to audio.
- **Interactive Showcase**: An interactive `index.html` file, generated from `index.qmd`, demonstrates the project's capabilities.

## Getting Started

### Prerequisites

- Python 3.8+
- An environment manager (like `venv` or `conda`)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/santi-rios/UBMI-IFC-Podcast.git
    cd UBMI-IFC-Podcast
    ```

2.  **Set up a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure API Keys:**
    - Copy the configuration template:
      ```bash
      cp config/config.template.yaml config/config.yaml
      ```
    - Add your API keys to `config/config.yaml`. **This file is ignored by Git to protect your keys.**

### Running the Project

The core of this project is showcased in the `final_pipeline.ipynb` notebook. This notebook provides a step-by-step walkthrough of the entire process, from data scraping to podcast generation.

For an interactive overview of the project's functionalities, open the `index.html` file in your web browser.

## Project Structure

- `final_pipeline.ipynb`: The main notebook demonstrating the entire workflow.
- `index.qmd` & `index.html`: An interactive presentation of the project.
- `src/`: Contains the Python source code for the pipeline.
- `config/`: Holds configuration files. `config.template.yaml` is a template for your own `config.yaml`.
- `requirements.txt`: A list of all necessary Python packages.
- `notebooks/`: Contains additional notebooks for specific tasks and experiments.
- `.gitignore`: Specifies which files and directories to exclude from version control.
- `LICENSE`: The project's license.
- `README.md`: This file.

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