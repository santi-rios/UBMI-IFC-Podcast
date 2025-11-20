"""
Configuration management for the podcast pipeline
"""

import yaml
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to config file. If None, uses default config/config.yaml
        
    Returns:
        Dictionary containing configuration settings
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
    
    # Load YAML config
    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    
    # Extract API keys from the YAML file
    config['api_keys'] = {
        'openai': config.get('api_keys', {}).get('openai'),
        'anthropic': config.get('api_keys', {}).get('anthropic'),
        'elevenlabs': config.get('api_keys', {}).get('elevenlabs'),
        'google': config.get('api_keys', {}).get('google'),  # Read Gemini API key
        'google_tts': config.get('api_keys', {}).get('google_tts')
    }
    
    return config


def get_data_dir() -> Path:
    """Get the data directory path"""
    return Path(__file__).parent.parent.parent / "data"


def get_output_dir() -> Path:
    """Get the output directory path"""
    return Path(__file__).parent.parent.parent / "outputs"