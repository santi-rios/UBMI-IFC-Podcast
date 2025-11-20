"""Publication classification and quality analysis."""

from typing import Dict, Any, List
from collections import Counter


class PublicationClassifier:
    """Classifies publications by type and analyzes quality metrics."""
    
    def __init__(self):
        """Initialize the publication classifier."""
        # Classification keywords for different publication types
        self.classification_keywords = {
            'Review': ['review', 'overview', 'survey', 'meta-analysis', 'systematic review'],
            'Clinical Trial': ['trial', 'randomized', 'placebo', 'clinical study', 'rct'],
            'Case Report': ['case report', 'patient case', 'case study', 'case series'],
            'Methodology': ['method', 'technique', 'protocol', 'approach', 'procedure'],
            'Research Article': []  # Default category
        }
    
    def classify_publication_type(self, title: str, abstract: str) -> str:
        """
        Simple rule-based classification of publication type.
        
        Args:
            title: Publication title
            abstract: Publication abstract
            
        Returns:
            str: Classified publication type
        """
        text = (title + " " + abstract).lower()
        
        # Check each category
        for pub_type, keywords in self.classification_keywords.items():
            if pub_type == 'Research Article':
                continue  # Skip default category
            
            if any(kw in text for kw in keywords):
                return pub_type
        
        # Default to Research Article
        return 'Research Article'
    
    def analyze_publication_types(self, publications: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Analyze publication type distribution in a dataset.
        
        Args:
            publications: List of publication dictionaries
            
        Returns:
            dict: Publication type counts
        """
        publication_types = Counter()
        
        for pub in publications:
            pub_type = self.classify_publication_type(
                pub.get('title', ''), 
                pub.get('abstract', '')
            )
            publication_types[pub_type] += 1
            
            # Add the classification to the publication metadata
            if 'metadata' not in pub:
                pub['metadata'] = {}
            pub['metadata']['publication_type'] = pub_type
        
        return dict(publication_types)
    
    def analyze_year_distribution(self, publications: List[Dict[str, Any]]) -> Dict[int, int]:
        """
        Analyze publication year distribution.
        
        Args:
            publications: List of publication dictionaries
            
        Returns:
            dict: Year distribution
        """
        years = [pub.get('year') for pub in publications if pub.get('year')]
        year_counts = Counter(years)
        return dict(year_counts.most_common(10))
    
    def analyze_journal_distribution(self, publications: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Analyze journal distribution.
        
        Args:
            publications: List of publication dictionaries
            
        Returns:
            dict: Journal distribution
        """
        journals = [pub.get('journal') for pub in publications if pub.get('journal')]
        journal_counts = Counter(journals)
        return dict(journal_counts.most_common(10))
    
    def generate_quality_report(self, publications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive quality report for a publication dataset.
        
        Args:
            publications: List of publication dictionaries
            
        Returns:
            dict: Comprehensive quality report
        """
        from .keywords import KeywordExtractor
        
        extractor = KeywordExtractor()
        
        report = {
            'total_publications': len(publications),
            'data_quality': extractor.check_data_quality(publications),
            'publication_types': self.analyze_publication_types(publications),
            'year_distribution': self.analyze_year_distribution(publications),
            'journal_distribution': self.analyze_journal_distribution(publications)
        }
        
        # Calculate quality percentages
        total = report['total_publications']
        if total > 0:
            quality_percentages = {}
            for issue, count in report['data_quality'].items():
                quality_percentages[f"{issue}_percentage"] = (count / total) * 100
            report['quality_percentages'] = quality_percentages
        
        return report
    
    def filter_high_quality_publications(
        self, 
        publications: List[Dict[str, Any]], 
        min_text_length: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Filter publications to include only high-quality entries.
        
        Args:
            publications: List of publication dictionaries
            min_text_length: Minimum combined title+abstract length
            
        Returns:
            list: Filtered high-quality publications
        """
        high_quality = []
        
        for pub in publications:
            # Check basic requirements
            if not pub.get('title') or not pub.get('abstract'):
                continue
            
            # Check text length
            text_len = len(pub.get('title', '') + " " + pub.get('abstract', ''))
            if text_len < min_text_length:
                continue
            
            # Check for year (optional but preferred)
            if not pub.get('year'):
                continue
            
            high_quality.append(pub)
        
        print(f"Filtered {len(publications)} publications to {len(high_quality)} high-quality entries")
        return high_quality


# Global function for backward compatibility
def classify_publication_type(title: str, abstract: str) -> str:
    """
    Global function to classify publication type (for backward compatibility).
    
    Args:
        title: Publication title
        abstract: Publication abstract
        
    Returns:
        str: Classified publication type
    """
    classifier = PublicationClassifier()
    return classifier.classify_publication_type(title, abstract)