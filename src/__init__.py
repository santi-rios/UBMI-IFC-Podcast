"""
UBMI-IFC-Podcast: Automated Scientific Podcast Generator

This package provides tools to scrape scientific publications from 
IFC-UNAM, analyze them using embeddings, find relevant PubMed articles,
and generate podcast scripts using LLMs.
"""

__version__ = "0.2.0"
__author__ = "Santiago G.-Rios"
__email__ = "santiago_gr@ciencias.unam.mx"

from .utils.config import load_config
from .utils.logger import setup_logger
