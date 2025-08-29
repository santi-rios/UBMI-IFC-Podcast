"""
Web scraper for IFC-UNAM publications
"""

import asyncio
import aiohttp
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup
from urllib.parse import urljoin, parse_qs, urlparse
import pandas as pd
from pathlib import Path

from ..utils.logger import get_logger
from ..utils.config import load_config


@dataclass
class Publication:
    """Data class for publication information"""
    title: str
    authors: str
    journal: str
    year: int
    doi: Optional[str] = None
    pubmed_id: Optional[str] = None
    ifc_url: Optional[str] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None


class IFCPublicationScraper:
    """Scraper for IFC-UNAM publications"""
    
    def __init__(self, config: Dict = None):
        self.config = config or load_config()
        self.logger = get_logger(__name__)
        self.base_url = self.config['ifc']['base_url']
        self.rate_limit_delay = self.config['ifc']['rate_limit_delay']
        
    async def scrape_publications_by_year(self, year: int) -> List[Publication]:
        """
        Scrape publications for a specific year
        
        Args:
            year: Year to scrape publications for
            
        Returns:
            List of Publication objects
        """
        self.logger.info(f"Scraping publications for year {year}")
        
        url = f"{self.base_url}/publicaciones.php?year={year}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        publications = self._parse_publications_page(html, year)
                        
                        # Get detailed information for each publication
                        detailed_publications = []
                        for pub in publications:
                            if pub.ifc_url:
                                detailed_pub = await self._get_publication_details(session, pub)
                                detailed_publications.append(detailed_pub)
                                await asyncio.sleep(self.rate_limit_delay)
                        
                        return detailed_publications
                    else:
                        self.logger.error(f"Failed to fetch {url}, status: {response.status}")
                        return []
                        
            except Exception as e:
                self.logger.error(f"Error scraping year {year}: {str(e)}")
                return []
    
    def _parse_publications_page(self, html: str, year: int) -> List[Publication]:
        """Parse the publications listing page"""
        soup = BeautifulSoup(html, 'html.parser')
        publications = []
        
        # This will need to be adjusted based on the actual HTML structure
        # You'll need to inspect the page to find the correct selectors
        publication_elements = soup.find_all('div', class_='publication-item')  # Adjust selector
        
        for element in publication_elements:
            try:
                # Extract basic information from listing
                title_element = element.find('a')  # Adjust selector
                if title_element:
                    title = title_element.get_text(strip=True)
                    detail_url = title_element.get('href')
                    if detail_url:
                        detail_url = urljoin(self.base_url, detail_url)
                
                # Extract other visible information
                authors = self._extract_text_by_class(element, 'authors')  # Adjust
                journal = self._extract_text_by_class(element, 'journal')  # Adjust
                
                pub = Publication(
                    title=title,
                    authors=authors,
                    journal=journal,
                    year=year,
                    ifc_url=detail_url
                )
                publications.append(pub)
                
            except Exception as e:
                self.logger.warning(f"Error parsing publication element: {str(e)}")
                continue
        
        self.logger.info(f"Found {len(publications)} publications for year {year}")
        return publications
    
    async def _get_publication_details(self, session: aiohttp.ClientSession, 
                                     publication: Publication) -> Publication:
        """Get detailed information from publication detail page"""
        try:
            async with session.get(publication.ifc_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract abstract
                    abstract_element = soup.find('div', class_='abstract')  # Adjust selector
                    if abstract_element:
                        publication.abstract = abstract_element.get_text(strip=True)
                    
                    # Extract DOI
                    doi_element = soup.find('span', string='DOI:')  # Adjust selector
                    if doi_element and doi_element.next_sibling:
                        publication.doi = doi_element.next_sibling.strip()
                    
                    # Extract PubMed ID
                    pubmed_element = soup.find('a', href=lambda x: x and 'pubmed' in x.lower())
                    if pubmed_element:
                        href = pubmed_element.get('href')
                        if href and 'pubmed' in href.lower():
                            # Extract PubMed ID from URL
                            publication.pubmed_id = self._extract_pubmed_id(href)
                    
                    self.logger.debug(f"Got details for: {publication.title[:50]}...")
                    
        except Exception as e:
            self.logger.warning(f"Error getting details for {publication.title}: {str(e)}")
        
        return publication
    
    def _extract_text_by_class(self, element, class_name: str) -> str:
        """Helper to extract text by class name"""
        found = element.find(class_=class_name)
        return found.get_text(strip=True) if found else ""
    
    def _extract_pubmed_id(self, url: str) -> Optional[str]:
        """Extract PubMed ID from URL"""
        try:
            parsed = urlparse(url)
            if 'pubmed' in parsed.netloc.lower():
                path_parts = parsed.path.strip('/').split('/')
                if path_parts and path_parts[-1].isdigit():
                    return path_parts[-1]
            return None
        except:
            return None
    
    async def scrape_all_years(self, start_year: int = None, end_year: int = None) -> List[Publication]:
        """
        Scrape publications for all configured years
        
        Args:
            start_year: Override config start year
            end_year: Override config end year
            
        Returns:
            List of all publications
        """
        start_year = start_year or self.config['ifc']['years_range']['start']
        end_year = end_year or self.config['ifc']['years_range']['end']
        
        all_publications = []
        
        for year in range(start_year, end_year + 1):
            publications = await self.scrape_publications_by_year(year)
            all_publications.extend(publications)
            
        self.logger.info(f"Total publications scraped: {len(all_publications)}")
        return all_publications
    
    def save_publications(self, publications: List[Publication], 
                         output_path: str = None) -> None:
        """Save publications to JSON/CSV file"""
        if not output_path:
            from ..utils.config import get_data_dir
            output_path = get_data_dir() / "raw" / "ifc_publications.json"
        
        # Convert to DataFrame for easy saving
        data = []
        for pub in publications:
            data.append({
                'title': pub.title,
                'authors': pub.authors,
                'journal': pub.journal,
                'year': pub.year,
                'doi': pub.doi,
                'pubmed_id': pub.pubmed_id,
                'ifc_url': pub.ifc_url,
                'abstract': pub.abstract,
                'keywords': pub.keywords
            })
        
        df = pd.DataFrame(data)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.suffix == '.json':
            df.to_json(output_path, orient='records', indent=2)
        else:
            df.to_csv(output_path, index=False)
        
        self.logger.info(f"Saved {len(publications)} publications to {output_path}")


async def main():
    """Test function"""
    scraper = IFCPublicationScraper()
    
    # Test with one year first
    publications = await scraper.scrape_publications_by_year(2024)
    scraper.save_publications(publications)
    
    print(f"Scraped {len(publications)} publications from 2024")
    for pub in publications[:3]:  # Print first 3
        print(f"- {pub.title}")


if __name__ == "__main__":
    asyncio.run(main())
