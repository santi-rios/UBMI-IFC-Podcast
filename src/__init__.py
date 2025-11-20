"""
UBMI-IFC-Podcast: Automated Scientific Podcast Generator

This package provides tools to scrape scientific publications from 
IFC-UNAM, analyze them using embeddings, find relevant PubMed articles,
and generate engaging podcast scripts and audio content.

The refactored modular structure includes:
- pdf_acquisition: Download research papers
- publication_management: Handle BibTeX and database operations  
- text_extraction: Extract text from PDF files
- affiliation_mining: Mine institutional affiliations from papers
- pubmed: Search and retrieve PubMed articles
- data_quality: Keyword extraction and publication classification
- pipeline: Main workflow orchestration
"""

# Import main pipeline class for easy access
from .pipeline import DatabaseExpansionPipeline

__version__ = "0.1.0"
__all__ = ['DatabaseExpansionPipeline']

__version__ = "0.2.0"
__author__ = "Santiago G.-Rios"
__email__ = "santiago_gr@ciencias.unam.mx"

from .utils.config import load_config
from .utils.logger import setup_logger
