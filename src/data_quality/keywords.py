"""Keyword extraction utilities for publications."""

import re
from typing import List, Dict, Any
from collections import Counter


class KeywordExtractor:
    """Extracts keywords from publication text for better search and embeddings."""
    
    def __init__(self):
        """Initialize the keyword extractor."""
        # Common words to filter out
        self.common_words = {
            'the', 'and', 'was', 'were', 'with', 'for', 'this', 'that',
            'from', 'are', 'been', 'have', 'has', 'had', 'will', 'would',
            'could', 'should', 'can', 'may', 'might', 'must', 'shall',
            'did', 'does', 'done', 'into', 'onto', 'upon', 'over', 'under',
            'above', 'below', 'between', 'among', 'through', 'during',
            'before', 'after', 'while', 'since', 'until', 'although',
            'though', 'because', 'unless', 'whether', 'where', 'when',
            'what', 'which', 'who', 'whom', 'whose', 'why', 'how'
        }
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract key terms from text for better embedding search.
        
        Args:
            text: Text to extract keywords from
            max_keywords: Maximum number of keywords to return
            
        Returns:
            list: List of extracted keywords
        """
        if not text:
            return []
            
        try:
            # Simple frequency-based extraction
            words = re.findall(r'\b[a-zA-Z]{3,15}\b', text.lower())
            word_freq = Counter(words)
            
            # Filter out common words
            for word in self.common_words:
                if word in word_freq:
                    del word_freq[word]
                    
            # Return top keywords
            return [word for word, _ in word_freq.most_common(max_keywords)]
        except Exception:
            return []
    
    def extract_scientific_keywords(self, text: str, max_keywords: int = 15) -> List[str]:
        """
        Extract scientific keywords with domain-specific filtering.
        
        Args:
            text: Text to extract keywords from
            max_keywords: Maximum number of keywords to return
            
        Returns:
            list: List of scientific keywords
        """
        if not text:
            return []
        
        # Scientific terms patterns
        scientific_patterns = [
            r'\b[A-Z][a-z]*(?:-[a-z]+)*\b',  # Capitalized terms
            r'\b\d+[a-zA-Z]+\b',             # Alphanumeric terms
            r'\b[a-zA-Z]+-\d+\b',            # Terms with numbers
            r'\b[a-z]+ase\b',                # Enzyme names
            r'\b[a-z]+ine\b',                # Chemical suffixes
            r'\b[a-z]+osis\b',               # Medical conditions
            r'\b[a-z]+tion\b',               # Process terms
        ]
        
        keywords = set()
        
        # Extract using patterns
        for pattern in scientific_patterns:
            matches = re.findall(pattern, text)
            keywords.update(match.lower() for match in matches)
        
        # Also use frequency-based extraction
        frequency_keywords = self.extract_keywords(text, max_keywords * 2)
        keywords.update(frequency_keywords)
        
        # Filter and sort by relevance (length as proxy)
        filtered_keywords = [
            kw for kw in keywords 
            if len(kw) >= 4 and kw not in self.common_words
        ]
        
        # Sort by length (longer terms often more specific)
        filtered_keywords.sort(key=len, reverse=True)
        
        return filtered_keywords[:max_keywords]
    
    def check_data_quality(self, publications: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Check database quality before embedding.
        
        Args:
            publications: List of publication dictionaries
            
        Returns:
            dict: Dictionary of quality issues and counts
        """
        issues = {
            'missing_title': 0,
            'missing_abstract': 0,
            'missing_year': 0,
            'missing_authors': 0,
            'short_text': 0
        }
        
        for pub in publications:
            if not pub.get('title'):
                issues['missing_title'] += 1
            if not pub.get('abstract'):
                issues['missing_abstract'] += 1
            if not pub.get('year'):
                issues['missing_year'] += 1
            if not pub.get('authors'):
                issues['missing_authors'] += 1
            
            # Check if there's enough text to create meaningful embeddings
            text_len = len((pub.get('title', '') + " " + pub.get('abstract', '')).split())
            if text_len < 30:  # Arbitrary threshold
                issues['short_text'] += 1
        
        return issues


# Global function for backward compatibility
def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Global function to extract keywords (for backward compatibility).
    
    Args:
        text: Text to extract keywords from
        max_keywords: Maximum number of keywords to return
        
    Returns:
        list: List of extracted keywords
    """
    extractor = KeywordExtractor()
    return extractor.extract_keywords(text, max_keywords)