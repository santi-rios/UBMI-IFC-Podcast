"""
Configuration management for the podcast pipeline
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file and environment variables
    
    Args:
        config_path: Path to config file. If None, uses default config/config.yaml
        
    Returns:
        Dictionary containing configuration settings
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
    
    # Load environment variables
    load_dotenv()
    
    # Load YAML config
    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    
    # Override with environment variables where applicable
    config['pubmed']['email'] = os.getenv('PUBMED_EMAIL', config['pubmed']['email'])
    config['pubmed']['api_key'] = os.getenv('PUBMED_API_KEY', config['pubmed']['api_key'])
    
    # Add API keys from environment
    config['api_keys'] = {
        'openai': os.getenv('OPENAI_API_KEY'),
        'anthropic': os.getenv('ANTHROPIC_API_KEY'),
        'elevenlabs': os.getenv('ELEVENLABS_API_KEY')
    }
    
    return config


def get_data_dir() -> Path:
    """Get the data directory path"""
    return Path(__file__).parent.parent.parent / "data"


def get_output_dir() -> Path:
    """Get the output directory path"""
    return Path(__file__).parent.parent.parent / "outputs"
