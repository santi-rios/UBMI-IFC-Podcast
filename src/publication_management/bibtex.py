"""BibTeX management for publication databases."""

import os
import re
from typing import List, Dict, Any

import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase


class BibTexManager:
    """Manages BibTeX file creation and manipulation."""
    
    def __init__(self):
        """Initialize the BibTeX manager."""
        self.writer = BibTexWriter()
    
    def format_authors_for_bibtex(self, author_string: str) -> str:
        """
        Convert author string to proper BibTeX format.
        
        Args:
            author_string: Raw author string from publication data
            
        Returns:
            str: Formatted author string for BibTeX
        """
        if not author_string:
            return "Unknown"
        
        # Split by commas and clean each author
        authors = [author.strip() for author in author_string.split(',')]
        
        # Group authors (assuming they come in pairs: LastName, FirstName)
        formatted_authors = []
        i = 0
        while i < len(authors):
            if i + 1 < len(authors):
                # Check if next item looks like a first name (short, no hyphens typically)
                next_item = authors[i + 1].strip()
                if (len(next_item) <= 3 or 
                    (len(next_item.split()) == 1 and '.' in next_item) or
                    re.match(r'^[A-Z]\.?$', next_item)):
                    # This is likely a first name/initial
                    last_name = authors[i].strip()
                    first_name = next_item
                    formatted_authors.append(f"{last_name}, {first_name}")
                    i += 2
                else:
                    # This is likely a full name or last name only
                    formatted_authors.append(authors[i].strip())
                    i += 1
            else:
                # Last author, no pair
                formatted_authors.append(authors[i].strip())
                i += 1
        
        # Join with " and " for BibTeX format
        return " and ".join(formatted_authors)
    
    def create_citation_key(self, pub: Dict[str, Any], index: int) -> str:
        """
        Create a unique citation key for a publication.
        
        Args:
            pub: Publication dictionary
            index: Index for uniqueness
            
        Returns:
            str: Citation key
        """
        first_author = pub['authors'].split(',')[0].strip() if pub['authors'] else 'Unknown'
        first_author_clean = re.sub(r'[^a-zA-Z]', '', first_author)
        citation_key = f"{first_author_clean}{pub['year']}_ifc_{index}"
        return citation_key
    
    def publication_to_bibtex_entry(self, pub: Dict[str, Any], index: int) -> Dict[str, Any]:
        """
        Convert a publication dictionary to BibTeX entry format.
        
        Args:
            pub: Publication dictionary
            index: Index for citation key uniqueness
            
        Returns:
            dict: BibTeX entry dictionary
        """
        citation_key = self.create_citation_key(pub, index)
        formatted_authors = self.format_authors_for_bibtex(pub['authors'])
        
        entry = {
            'ENTRYTYPE': 'article',
            'ID': citation_key,
            'title': pub['title'],
            'author': formatted_authors,
            'journal': pub['journal'],
            'year': str(pub['year']),
            'abstract': pub.get('abstract', ''),
            'url': pub.get('ifc_url', ''),
            'note': 'Instituto de Fisiología Celular, UNAM'
        }
        
        if pub.get('doi'):
            entry['doi'] = pub['doi']
            
        if pub.get('pubmed_id'):
            entry['pmid'] = pub['pubmed_id']
            
        return entry
    
    def create_bibtex_from_publications(
        self, 
        publications: List[Dict[str, Any]], 
        output_file: str = '../data/processed/ifc_publications.bib'
    ) -> str:
        """
        Convert JSON publications to BibTeX format.
        
        Args:
            publications: List of publication dictionaries
            output_file: Output file path for BibTeX
            
        Returns:
            str: Path to created BibTeX file
        """
        db = BibDatabase()
        entries = []
        
        for i, pub in enumerate(publications):
            entry = self.publication_to_bibtex_entry(pub, i)
            entries.append(entry)
        
        db.entries = entries
        
        # Write to file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(self.writer.write(db))
        
        print(f"📚 Created BibTeX file with {len(entries)} entries: {output_file}")
        print("Import this file into Zotero to download PDFs automatically")
        
        # Show sample formatted authors for verification
        print("\n🔍 Sample author formatting:")
        for i, entry in enumerate(entries[:3]):
            print(f"{i+1}. Original: {publications[i]['authors']}")
            print(f"   BibTeX:   {entry['author']}")
        
        return output_file
    
    def load_bibtex_file(self, bibtex_path: str) -> List[Dict[str, Any]]:
        """
        Load and parse a BibTeX file.
        
        Args:
            bibtex_path: Path to BibTeX file
            
        Returns:
            list: List of parsed BibTeX entries
        """
        with open(bibtex_path, 'r', encoding='utf-8') as f:
            bib_database = bibtexparser.load(f)
        
        return bib_database.entries