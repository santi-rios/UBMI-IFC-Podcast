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
        """Parse the publications listing page based on actual website structure"""
        soup = BeautifulSoup(html, 'html.parser')
        publications = []
        
        # Based on analysis: publications are in <a> tags with classes 'opensans400' and 'd-flexy'
        publication_links = soup.find_all('a', class_=['opensans400', 'd-flexy'])
        
        self.logger.info(f"Found {len(publication_links)} potential publication links")
        
        for i, link in enumerate(publication_links):
            try:
                # Get the full text of the publication entry
                pub_text = link.get_text().strip()
                
                # Skip if this doesn't look like a publication (too short or no DOI pattern)
                if len(pub_text) < 50 or '10.' not in pub_text:
                    continue
                
                # Extract publication details using regex patterns
                import re
                
                # Extract DOI
                doi_match = re.search(r'10\.\d+/[^\s<>"]+', pub_text)
                doi = doi_match.group() if doi_match else ""
                
                # Extract year (typically in parentheses)
                year_match = re.search(r'\((\d{4})\)', pub_text)
                pub_year = int(year_match.group(1)) if year_match else year
                
                # Extract title (usually after year and before journal)
                # Pattern: (...year...). Title. Journal
                title_match = re.search(r'\(\d{4}\)\.\s*([^.]+\.)', pub_text)
                title = title_match.group(1).strip().rstrip('.') if title_match else pub_text[:100]
                
                # Extract authors (before the year)
                author_match = re.search(r'^([^(]+)\s*\(', pub_text)
                authors = author_match.group(1).strip() if author_match else ""
                
                # Extract journal (try different patterns)
                if title and title in pub_text:
                    remaining_text = pub_text.split(title, 1)[1] if title in pub_text else pub_text
                    journal_match = re.search(r'^\s*\.?\s*([^.]+)', remaining_text)
                    journal = journal_match.group(1).strip() if journal_match else ""
                else:
                    journal = ""
                
                # Get the href for more details
                detail_url = link.get('href')
                if detail_url and not detail_url.startswith('http'):
                    detail_url = f"https://www.ifc.unam.mx/{detail_url}"
                
                publication = Publication(
                    title=title,
                    authors=authors,
                    journal=journal,
                    year=pub_year,
                    doi=doi,
                    pubmed_id="",  # Will be filled later if available
                    ifc_url=detail_url or "",
                    abstract=""  # Will be filled when scraping details
                )
                
                publications.append(publication)
                
            except Exception as e:
                self.logger.error(f"Error parsing publication {i+1}: {str(e)}")
                continue
        
        self.logger.info(f"Successfully parsed {len(publications)} publications")
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

    async def scrape_all_available_publications(self):
        """Scrape publications from all available years (2020-2025)"""
        print("🚀 Starting comprehensive scraping of IFC publications...")

        scraper = self
        all_publications = []
        years_to_scrape = range(2020, 2025)  # Adjust range as needed

        for year in years_to_scrape:
            print(f"\n📅 Scraping year {year}...")
            try:
                publications = await scraper.scrape_publications_by_year(year)
                if publications:
                    all_publications.extend(publications)
                    print(f"   ✅ Found {len(publications)} publications for {year}")
                else:
                    print(f"   ⚠️ No publications found for {year}")
                    
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Error scraping {year}: {e}")
                continue

        print(f"\n🎉 Total publications collected: {len(all_publications)}")
        
        # Save raw data
        output_dir = Path("../data/raw")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        scraper.save_publications(all_publications, output_dir / "all_ifc_publications.json")
        
        # Create summary DataFrame
        df = pd.DataFrame([{
            'title': pub.title,
            'authors': pub.authors,
            'journal': pub.journal,
            'year': pub.year,
            'doi': pub.doi,
            'abstract': pub.abstract[:200] if pub.abstract else 'No abstract',
            'has_doi': bool(pub.doi),
            'has_abstract': bool(pub.abstract)
        } for pub in all_publications])
        
        print("\n📊 Data Summary:")
        print(f"   Publications by year:")
        print(df['year'].value_counts().sort_index())
        print(f"\n   Publications with DOI: {df['has_doi'].sum()}/{len(df)}")
        print(f"   Publications with abstract: {df['has_abstract'].sum()}/{len(df)}")
        
        return all_publications, df

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
