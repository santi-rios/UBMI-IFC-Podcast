"""Enhanced PubMed searcher with comprehensive search capabilities."""

import time
import requests
from typing import List, Dict, Any, Optional
from .xml_parser import PubmedXMLParser


class EnhancedPubmedSearcher:
    """Enhanced PubMed searcher with comprehensive query building and XML parsing."""
    
    def __init__(self):
        """Initialize the enhanced PubMed searcher."""
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.xml_parser = PubmedXMLParser()
        
    def build_search_queries(self, affiliation_variations: Optional[List[str]] = None) -> List[str]:
        """
        Build comprehensive search queries for different affiliation variations.
        
        Args:
            affiliation_variations: List of affiliation variations to search
            
        Returns:
            list: List of search queries
        """
        if affiliation_variations is None:
            # Default variations based on the institute
            affiliation_variations = [
                "Instituto de Fisiologia Celular[Affiliation]",
                "Institute of Cellular Physiology[Affiliation]",
                "IFC UNAM[Affiliation]",
                "Departamento de Neurobiologia UNAM[Affiliation]",
                "Universidad Nacional Autonoma Mexico Fisiologia[Affiliation]",
                "National Autonomous University Mexico Cellular Physiology[Affiliation]"
            ]
        
        # Filter out variations that are too generic or too long
        filtered_variations = []
        for var in affiliation_variations:
            # Remove the [Affiliation] suffix if present for checking
            check_var = var.replace("[Affiliation]", "").strip().lower()
            
            # Skip variations that are too short (likely noise) 
            # or don't contain key terms related to the institute
            if len(check_var) < 10:
                continue
            
            # Skip variations without key identifiers
            if not any(term in check_var for term in ["fisiol", "physiol", "mexico", "unam", "ifc", "cellular"]):
                continue
                
            filtered_variations.append(var)
        
        queries = []
        
        # Individual affiliation searches
        for aff in filtered_variations[:10]:  # Limit to top 10 to avoid excessive queries
            queries.append(aff)
            
        # Combined searches with time ranges
        if filtered_variations:
            recent_query = f"({' OR '.join(filtered_variations[:3])}) AND (2020:2024[pdat])"
            historical_query = f"({' OR '.join(filtered_variations[:3])}) AND (2010:2019[pdat])"
            
            queries.extend([recent_query, historical_query])
        
        return queries
    
    def search_pubmed(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Search PubMed with a given query.
        
        Args:
            query: Search query
            max_results: Maximum number of results to retrieve
            
        Returns:
            list: List of article dictionaries
        """
        # Step 1: Search
        search_url = f"{self.base_url}esearch.fcgi"
        search_params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'json'
        }
        
        try:
            response = requests.get(search_url, params=search_params)
            search_data = response.json()
            
            pmids = search_data['esearchresult']['idlist']
            total_count = int(search_data['esearchresult']['count'])
            
            print(f"Found {total_count} results for query: {query[:50]}...")
            
            if not pmids:
                return []
            
            # Step 2: Fetch details
            time.sleep(0.5)  # Rate limiting
            
            fetch_url = f"{self.base_url}efetch.fcgi"
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(pmids),
                'retmode': 'xml'
            }
            
            fetch_response = requests.get(fetch_url, params=fetch_params)
            
            # Parse XML using our parser
            articles = self.xml_parser.parse_pubmed_xml(fetch_response.text)
            
            return articles
            
        except Exception as e:
            print(f"Error searching PubMed: {e}")
            return []
    
    def comprehensive_search(
        self, 
        affiliation_variations: Optional[List[str]] = None, 
        max_per_query: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Run comprehensive search with all query variations.
        
        Args:
            affiliation_variations: Optional list of affiliation variations to use
            max_per_query: Maximum results per query
        
        Returns:
            list: List of articles found
        """
        queries = self.build_search_queries(affiliation_variations)
        all_articles = []
        seen_pmids = set()
        
        for i, query in enumerate(queries):
            print(f"\n🔍 Running search {i+1}/{len(queries)}")
            articles = self.search_pubmed(query, max_per_query)
            
            # Deduplicate
            new_articles = []
            for article in articles:
                if article['pmid'] not in seen_pmids:
                    seen_pmids.add(article['pmid'])
                    new_articles.append(article)
            
            all_articles.extend(new_articles)
            print(f"Added {len(new_articles)} new articles (total: {len(all_articles)})")
            
            time.sleep(1)  # Be respectful to NCBI
            
        return all_articles