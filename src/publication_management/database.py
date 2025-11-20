"""Database management for publications."""

import os
import json
import time
from typing import List, Dict, Any, Set, Tuple
from collections import Counter


class PublicationDatabase:
    """Manages publication database operations."""
    
    def __init__(self):
        """Initialize the publication database manager."""
        pass
    
    def build_publication_indexes(self, publications: List[Dict[str, Any]]) -> Dict[str, Dict]:
        """
        Create index structures for faster lookup.
        
        Args:
            publications: List of publication dictionaries
            
        Returns:
            dict: Index structures
        """
        indexes = {
            'doi': {},
            'pmid': {},
            'title_lower': {},
            'year': {},
            'journal': {}
        }
        
        for i, pub in enumerate(publications):
            if pub.get('doi'):
                indexes['doi'][pub['doi']] = i
            if pub.get('pubmed_id'):
                indexes['pmid'][pub['pubmed_id']] = i
            if pub.get('title'):
                indexes['title_lower'][pub['title'].lower().strip()] = i
            if pub.get('year'):
                year = pub['year']
                if year not in indexes['year']:
                    indexes['year'][year] = []
                indexes['year'][year].append(i)
            if pub.get('journal'):
                journal = pub['journal']
                if journal not in indexes['journal']:
                    indexes['journal'][journal] = []
                indexes['journal'][journal].append(i)
        
        return indexes
    
    def create_lookup_sets(self, existing_pubs: List[Dict[str, Any]]) -> Tuple[Set[str], Set[str], Set[str]]:
        """
        Create lookup sets for deduplication.
        
        Args:
            existing_pubs: List of existing publications
            
        Returns:
            tuple: (DOIs, PMIDs, titles) as sets
        """
        existing_dois = {pub.get('doi') for pub in existing_pubs if pub.get('doi')}
        existing_pmids = {pub.get('pubmed_id') for pub in existing_pubs if pub.get('pubmed_id')}
        existing_titles = {pub.get('title', '').lower().strip() for pub in existing_pubs if pub.get('title')}
        
        return existing_dois, existing_pmids, existing_titles
    
    def convert_pubmed_to_publication_format(self, pubmed_pub: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert PubMed format to internal publication format.
        
        Args:
            pubmed_pub: PubMed publication dictionary
            
        Returns:
            dict: Converted publication dictionary
        """
        # Import here to avoid circular imports
        try:
            from data_quality.keywords import extract_keywords
        except ImportError:
            from ..data_quality.keywords import extract_keywords
        
        converted_pub = {
            'title': pubmed_pub.get('title', ''),
            'authors': pubmed_pub.get('authors', ''),
            'journal': pubmed_pub.get('journal', ''),
            'year': pubmed_pub.get('year'),
            'doi': pubmed_pub.get('doi'),
            'pubmed_id': pubmed_pub.get('pmid'),
            'ifc_url': None,  # Not available from PubMed
            'abstract': pubmed_pub.get('abstract', ''),
            'keywords': None,
            'embedding_text': pubmed_pub.get('abstract', '') + " " + pubmed_pub.get('title', ''),
            'keywords_extracted': extract_keywords(pubmed_pub.get('abstract', '') + " " + pubmed_pub.get('title', '')),
            'metadata': {
                'source': 'PubMed_search',
                'has_full_text': False,
                'affiliation_matched': pubmed_pub.get('affiliation_matched', 'Unknown')
            }
        }
        
        return converted_pub
    
    def merge_publication_databases(
        self, 
        existing_pubs: List[Dict[str, Any]], 
        new_pubs: List[Dict[str, Any]], 
        output_file: str = '../data/processed/expanded_ifc_publications.json'
    ) -> List[Dict[str, Any]]:
        """
        Merge existing publications with newly found ones, removing duplicates.
        
        Args:
            existing_pubs: List of existing publications
            new_pubs: List of new publications to merge
            output_file: Path to save merged database
            
        Returns:
            list: Merged publication list
        """
        # Create lookup sets for deduplication
        existing_dois, existing_pmids, existing_titles = self.create_lookup_sets(existing_pubs)
        
        merged_pubs = existing_pubs.copy()
        new_count = 0
        
        print(f"Processing {len(new_pubs)} potential new publications...")
        
        for pub in new_pubs:
            is_duplicate = False
            
            # Check for duplicates
            if pub.get('doi') and pub['doi'] in existing_dois:
                is_duplicate = True
            elif pub.get('pmid') and pub['pmid'] in existing_pmids:
                is_duplicate = True
            elif pub.get('title', '').lower().strip() in existing_titles:
                is_duplicate = True
                
            if not is_duplicate:
                # Convert PubMed format to internal format
                converted_pub = self.convert_pubmed_to_publication_format(pub)
                merged_pubs.append(converted_pub)
                new_count += 1
                
                # Update tracking sets
                if pub.get('doi'):
                    existing_dois.add(pub['doi'])
                if pub.get('pmid'):
                    existing_pmids.add(pub['pmid'])
                existing_titles.add(pub.get('title', '').lower().strip())
        
        # Save expanded database
        self.save_publications(merged_pubs, output_file)
        
        print(f"\n📊 Database expansion complete:")
        print(f"   Original publications: {len(existing_pubs)}")
        print(f"   New publications added: {new_count}")
        print(f"   Total publications: {len(merged_pubs)}")
        print(f"   Saved to: {output_file}")
        
        return merged_pubs
    
    def save_publications(self, publications: List[Dict[str, Any]], output_file: str):
        """
        Save publications to JSON file.
        
        Args:
            publications: List of publication dictionaries
            output_file: Output file path
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(publications, f, indent=2, ensure_ascii=False)
    
    def load_publications(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load publications from JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            list: List of publication dictionaries
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            publications = json.load(f)
        return publications
    
    def test_merge_effectiveness(
        self, 
        existing_pubs: List[Dict[str, Any]], 
        new_pubs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Test merge to evaluate method effectiveness without saving.
        
        Args:
            existing_pubs: Existing publications
            new_pubs: New publications to test
            
        Returns:
            dict: Analysis results
        """
        print("   Building lookup tables for faster matching...")
        existing_dois, existing_pmids, existing_titles = self.create_lookup_sets(existing_pubs)
        
        # Analyze new publications
        new_count = 0
        duplicate_by_doi = 0
        duplicate_by_pmid = 0
        duplicate_by_title = 0
        truly_new = []
        
        # Process with progress indicator
        print("\n   Processing publications:")
        total_new = len(new_pubs)
        update_interval = max(1, min(100, total_new // 10))
        
        for i, pub in enumerate(new_pubs):
            # Show progress periodically
            if i % update_interval == 0 or i == total_new - 1:
                progress = (i + 1) / total_new * 100
                print(f"   Progress: {i+1}/{total_new} ({progress:.1f}%)", end="\r")
            
            is_duplicate = False
            duplicate_reason = ""
            
            # Check for duplicates with detailed tracking
            if pub.get('doi') and pub['doi'] in existing_dois:
                is_duplicate = True
                duplicate_reason = "DOI match"
                duplicate_by_doi += 1
            elif pub.get('pmid') and pub['pmid'] in existing_pmids:
                is_duplicate = True
                duplicate_reason = "PMID match"
                duplicate_by_pmid += 1
            elif pub.get('title'):
                title_lower = pub.get('title', '').lower().strip()
                if title_lower in existing_titles:
                    is_duplicate = True
                    duplicate_reason = "Title match"
                    duplicate_by_title += 1
                
            if not is_duplicate:
                # This is a new publication
                truly_new.append({
                    'title': pub.get('title', ''),
                    'authors': pub.get('authors', ''),
                    'journal': pub.get('journal', ''),
                    'year': pub.get('year'),
                    'doi': pub.get('doi'),
                    'pubmed_id': pub.get('pmid'),
                    'abstract': pub.get('abstract', ''),
                    'source': 'PubMed_search'
                })
                new_count += 1
        
        print("\n   Processing complete!                           ")  # Clear progress line
        
        return {
            'total_found': len(new_pubs),
            'truly_new': new_count,
            'truly_new_articles': truly_new,
            'duplicates': {
                'by_doi': duplicate_by_doi,
                'by_pmid': duplicate_by_pmid,
                'by_title': duplicate_by_title,
                'total': len(new_pubs) - new_count
            }
        }
    
    def generate_summary_report(
        self, 
        original_count: int, 
        final_publications: List[Dict[str, Any]], 
        new_articles: List[Dict[str, Any]], 
        output_dir: str
    ) -> Dict[str, Any]:
        """
        Generate a summary report of the database expansion.
        
        Args:
            original_count: Original number of publications
            final_publications: Final merged publications
            new_articles: New articles found
            output_dir: Output directory for report
            
        Returns:
            dict: Summary report
        """
        report = {
            'pipeline_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'original_count': original_count,
            'pubmed_found': len(new_articles),
            'final_count': len(final_publications),
            'new_additions': len(final_publications) - original_count,
            'year_distribution': {},
            'top_journals': {}
        }
        
        # Analyze year distribution
        years = [pub.get('year') for pub in final_publications if pub.get('year')]
        year_counts = Counter(years)
        report['year_distribution'] = dict(year_counts.most_common(10))
        
        # Analyze top journals
        journals = [pub.get('journal') for pub in final_publications if pub.get('journal')]
        journal_counts = Counter(journals)
        report['top_journals'] = dict(journal_counts.most_common(10))
        
        # Save report
        report_path = os.path.join(output_dir, 'pipeline_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report