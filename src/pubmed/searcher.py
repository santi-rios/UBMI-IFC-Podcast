"""
PubMed search and article retrieval
"""

import asyncio
import aiohttp
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from xml.etree import ElementTree as ET
from urllib.parse import urlencode
import pandas as pd

# Handle both relative and absolute imports for notebook compatibility
try:
    from ..utils.logger import get_logger
    from ..utils.config import load_config
except ImportError:
    # Fallback for notebook/standalone usage
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.logger import get_logger
    from utils.config import load_config


@dataclass
class PubMedArticle:
    """Data class for PubMed article information"""
    pmid: str
    title: str
    abstract: str
    authors: List[str]
    journal: str
    publication_date: str
    doi: Optional[str] = None
    keywords: Optional[List[str]] = None
    mesh_terms: Optional[List[str]] = None
    similarity_score: Optional[float] = None


class PubMedSearcher:
    """Search and retrieve articles from PubMed"""
    
    def __init__(self, config: Dict = None):
        self.config = config or load_config()
        self.logger = get_logger(__name__)
        self.base_url = self.config['pubmed']['base_url']
        self.email = self.config['pubmed']['email']
        self.api_key = self.config['pubmed']['api_key']
        self.rate_limit_delay = self.config['pubmed']['rate_limit_delay']
        
    async def search_recent_articles(self, 
                                   query_terms: List[str] = None,
                                   days_back: int = 7,
                                   max_results: int = 1000) -> List[str]:
        """
        Search for recent articles in PubMed
        
        Args:
            query_terms: List of search terms. If None, uses broad search
            days_back: How many days back to search
            max_results: Maximum number of PMIDs to return
            
        Returns:
            List of PubMed IDs
        """
        # Build search query
        if query_terms:
            query = " OR ".join([f'"{term}"[Abstract]' for term in query_terms])
        else:
            # Broad search for recent biomedical articles
            query = "(humans[MeSH Terms]) AND (english[Language])"
        
        # For now, skip date filtering to get basic functionality working
        # TODO: Fix date filter format
        # Add date filter for recent articles (simpler format)
        # Use last N days format which is more reliable
        # if days_back <= 365:
        #     # For recent searches, use "last N days" format
        #     query += f' AND "last {days_back} days"[Publication Date]'
        # else:
        #     # For longer periods, use date range
        #     from datetime import datetime, timedelta
        #     end_date = datetime.now()
        #     start_date = end_date - timedelta(days=days_back)
        #     
        #     # PubMed date format: YYYY/MM/DD
        #     start_date_str = start_date.strftime("%Y/%m/%d")
        #     end_date_str = end_date.strftime("%Y/%m/%d")
        #     
        #     query += f' AND ("{start_date_str}"[Publication Date]:"{end_date_str}"[Publication Date])'
        
        self.logger.info(f"Searching PubMed with query: {query}")
        
        # Parameters for search
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'xml',
            'tool': 'ubmi-ifc-podcast',
            'email': self.email,
            'sort': 'relevance'
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        url = f"{self.base_url}esearch.fcgi?" + urlencode(params)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        xml_content = await response.text()
                        pmids = self._parse_search_results(xml_content)
                        self.logger.info(f"Found {len(pmids)} articles")
                        return pmids[:max_results]
                    else:
                        self.logger.error(f"PubMed search failed with status {response.status}")
                        return []
            except Exception as e:
                self.logger.error(f"Error searching PubMed: {str(e)}")
                return []
    
    def _parse_search_results(self, xml_content: str) -> List[str]:
        """Parse XML search results to extract PMIDs"""
        try:
            root = ET.fromstring(xml_content)
            pmids = []
            
            for id_elem in root.findall('.//Id'):
                pmid = id_elem.text
                if pmid:
                    pmids.append(pmid)
                    
            return pmids
        except ET.ParseError as e:
            self.logger.error(f"Error parsing search results XML: {str(e)}")
            return []
    
    async def fetch_article_details(self, pmids: List[str]) -> List[PubMedArticle]:
        """
        Fetch detailed information for a list of PMIDs
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            List of PubMedArticle objects
        """
        articles = []
        
        # Process PMIDs in batches to respect rate limits
        batch_size = 200  # PubMed allows up to 200 IDs per request
        
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]
            batch_articles = await self._fetch_batch_details(batch)
            articles.extend(batch_articles)
            
            # Rate limiting
            if i + batch_size < len(pmids):
                await asyncio.sleep(self.rate_limit_delay)
        
        self.logger.info(f"Retrieved details for {len(articles)} articles")
        return articles
    
    async def _fetch_batch_details(self, pmids: List[str]) -> List[PubMedArticle]:
        """Fetch details for a batch of PMIDs"""
        if not pmids:
            return []
        
        # Parameters for efetch
        params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml',
            'tool': 'ubmi-ifc-podcast',
            'email': self.email
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        url = f"{self.base_url}efetch.fcgi?" + urlencode(params)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        xml_content = await response.text()
                        return self._parse_article_details(xml_content)
                    else:
                        self.logger.error(f"Failed to fetch details for batch, status: {response.status}")
                        return []
            except Exception as e:
                self.logger.error(f"Error fetching article details: {str(e)}")
                return []
    
    def _parse_article_details(self, xml_content: str) -> List[PubMedArticle]:
        """Parse XML response to extract article details"""
        articles = []
        
        try:
            root = ET.fromstring(xml_content)
            
            for article_elem in root.findall('.//PubmedArticle'):
                try:
                    article = self._parse_single_article(article_elem)
                    if article:
                        articles.append(article)
                except Exception as e:
                    self.logger.warning(f"Error parsing individual article: {str(e)}")
                    continue
                    
        except ET.ParseError as e:
            self.logger.error(f"Error parsing article details XML: {str(e)}")
        
        return articles
    
    def _parse_single_article(self, article_elem) -> Optional[PubMedArticle]:
        """Parse a single article from XML"""
        # Extract PMID
        pmid_elem = article_elem.find('.//PMID')
        if pmid_elem is None:
            return None
        pmid = pmid_elem.text
        
        # Extract title
        title_elem = article_elem.find('.//ArticleTitle')
        title = title_elem.text if title_elem is not None else ""
        
        # Extract abstract
        abstract_texts = []
        for abstract_elem in article_elem.findall('.//AbstractText'):
            if abstract_elem.text:
                abstract_texts.append(abstract_elem.text)
        abstract = " ".join(abstract_texts)
        
        # Extract authors
        authors = []
        for author_elem in article_elem.findall('.//Author'):
            last_name_elem = author_elem.find('.//LastName')
            first_name_elem = author_elem.find('.//ForeName')
            if last_name_elem is not None:
                author_name = last_name_elem.text
                if first_name_elem is not None:
                    author_name = f"{first_name_elem.text} {author_name}"
                authors.append(author_name)
        
        # Extract journal
        journal_elem = article_elem.find('.//Journal/Title')
        journal = journal_elem.text if journal_elem is not None else ""
        
        # Extract publication date
        pub_date_elem = article_elem.find('.//PubDate')
        pub_date = ""
        if pub_date_elem is not None:
            year_elem = pub_date_elem.find('Year')
            month_elem = pub_date_elem.find('Month')
            day_elem = pub_date_elem.find('Day')
            
            parts = []
            if year_elem is not None:
                parts.append(year_elem.text)
            if month_elem is not None:
                parts.append(month_elem.text)
            if day_elem is not None:
                parts.append(day_elem.text)
            pub_date = "-".join(parts)
        
        # Extract DOI
        doi = None
        for article_id_elem in article_elem.findall('.//ArticleId'):
            id_type = article_id_elem.get('IdType')
            if id_type == 'doi':
                doi = article_id_elem.text
                break
        
        # Extract MeSH terms
        mesh_terms = []
        for mesh_elem in article_elem.findall('.//MeshHeading/DescriptorName'):
            if mesh_elem.text:
                mesh_terms.append(mesh_elem.text)
        
        return PubMedArticle(
            pmid=pmid,
            title=title,
            abstract=abstract,
            authors=authors,
            journal=journal,
            publication_date=pub_date,
            doi=doi,
            mesh_terms=mesh_terms
        )
    
    def save_articles(self, articles: List[PubMedArticle], 
                     output_path: str = None) -> None:
        """Save articles to file"""
        if not output_path:
            from ..utils.config import get_data_dir
            output_path = get_data_dir() / "raw" / "pubmed_articles.json"
        
        # Convert to DataFrame
        data = []
        for article in articles:
            data.append({
                'pmid': article.pmid,
                'title': article.title,
                'abstract': article.abstract,
                'authors': article.authors,
                'journal': article.journal,
                'publication_date': article.publication_date,
                'doi': article.doi,
                'keywords': article.keywords,
                'mesh_terms': article.mesh_terms,
                'similarity_score': article.similarity_score
            })
        
        df = pd.DataFrame(data)
        df.to_json(output_path, orient='records', indent=2)
        
        self.logger.info(f"Saved {len(articles)} articles to {output_path}")


async def main():
    """Test function"""
    searcher = PubMedSearcher()
    
    # Search for recent articles
    pmids = await searcher.search_recent_articles(
        query_terms=["neuroscience", "physiology"],
        days_back=7,
        max_results=10
    )
    
    # Fetch details
    articles = await searcher.fetch_article_details(pmids)
    searcher.save_articles(articles)
    
    print(f"Found {len(articles)} articles")
    for article in articles[:3]:
        print(f"- {article.title}")


if __name__ == "__main__":
    asyncio.run(main())
