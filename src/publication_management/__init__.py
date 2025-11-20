"""Publication management modules for BibTeX and database operations."""

from .bibtex import BibTexManager
from .database import PublicationDatabase

__all__ = ['BibTexManager', 'PublicationDatabase']