"""PubMed XML parsing utilities."""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional


class PubmedXMLParser:
    """Handles parsing of PubMed XML responses."""
    
    def __init__(self):
        """Initialize the XML parser."""
        pass
    
    def parse_pubmed_xml(self, xml_content: str) -> List[Dict[str, Any]]:
        """
        Parse PubMed XML response and extract article information.
        
        Args:
            xml_content: Raw XML content from PubMed API
            
        Returns:
            list: List of parsed article dictionaries
        """
        articles = []
        
        try:
            root = ET.fromstring(xml_content)
            
            for article in root.findall('.//PubmedArticle'):
                try:
                    parsed_article = self.parse_single_article(article)
                    if parsed_article:
                        articles.append(parsed_article)
                        
                except Exception as e:
                    print(f"Error parsing article: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error parsing XML: {e}")
            
        return articles
    
    def parse_single_article(self, article_elem) -> Optional[Dict[str, Any]]:
        """
        Parse a single PubmedArticle XML element.
        
        Args:
            article_elem: XML element representing a single article
            
        Returns:
            dict: Parsed article data or None if parsing fails
        """
        try:
            # Extract basic info
            pmid = self.get_text_or_none(article_elem.find('.//PMID'))
            if not pmid:
                return None
            
            title_elem = article_elem.find('.//ArticleTitle')
            title = title_elem.text if title_elem is not None else "No title"
            
            # Authors
            authors = self.extract_authors(article_elem)
            
            # Journal and year
            journal_elem = article_elem.find('.//Journal/Title')
            journal = journal_elem.text if journal_elem is not None else "Unknown"
            
            year_elem = article_elem.find('.//PubDate/Year')
            year = int(year_elem.text) if year_elem is not None else None
            
            # Abstract
            abstract_elem = article_elem.find('.//Abstract/AbstractText')
            abstract = abstract_elem.text if abstract_elem is not None else ""
            
            # DOI
            doi_elem = article_elem.find('.//ELocationID[@EIdType="doi"]')
            doi = doi_elem.text if doi_elem is not None else None
            
            article_data = {
                'pmid': pmid,
                'title': title,
                'authors': '; '.join(authors),
                'journal': journal,
                'year': year,
                'abstract': abstract,
                'doi': doi
            }
            
            return article_data
            
        except Exception as e:
            print(f"Error parsing single article: {e}")
            return None
    
    def get_text_or_none(self, elem) -> Optional[str]:
        """
        Safely extract text from XML element.
        
        Args:
            elem: XML element
            
        Returns:
            str or None: Element text or None if element is None
        """
        return elem.text if elem is not None else None
    
    def extract_authors(self, article_elem) -> List[str]:
        """
        Extract author list from article XML element.
        
        Args:
            article_elem: XML element representing the article
            
        Returns:
            list: List of author names
        """
        authors = []
        
        for author in article_elem.findall('.//Author'):
            lastname = author.find('.//LastName')
            firstname = author.find('.//ForeName')
            
            if lastname is not None:
                author_name = lastname.text
                if firstname is not None:
                    author_name += f", {firstname.text}"
                authors.append(author_name)
        
        return authors
    
    def extract_mesh_terms(self, article_elem) -> List[str]:
        """
        Extract MeSH terms from article XML element.
        
        Args:
            article_elem: XML element representing the article
            
        Returns:
            list: List of MeSH terms
        """
        mesh_terms = []
        
        for mesh_heading in article_elem.findall('.//MeshHeading'):
            descriptor = mesh_heading.find('.//DescriptorName')
            if descriptor is not None:
                mesh_terms.append(descriptor.text)
        
        return mesh_terms
    
    def extract_keywords(self, article_elem) -> List[str]:
        """
        Extract keywords from article XML element.
        
        Args:
            article_elem: XML element representing the article
            
        Returns:
            list: List of keywords
        """
        keywords = []
        
        for keyword in article_elem.findall('.//Keyword'):
            if keyword.text:
                keywords.append(keyword.text)
        
        return keywords