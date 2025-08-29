"""
UBMI-IFC-Podcast: Automated Scientific Podcast Generator

This package provides tools to scrape scientific publications from 
IFC-UNAM, analyze them using embeddings, find relevant PubMed articles,
and generate podcast scripts using LLMs.
"""

__version__ = "0.1.0"
__author__ = "Santiago Rios"
__email__ = "your-email@example.com"

from .utils.config import load_config
from .utils.logger import setup_logger
