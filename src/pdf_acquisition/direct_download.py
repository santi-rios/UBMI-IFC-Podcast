"""Direct DOI download module using Sci-Hub mirrors."""

import os
import time
import requests
from typing import List, Tuple


class DirectDownloader:
    """Direct PDF downloader from DOI using Sci-Hub mirrors."""
    
    def __init__(self):
        """Initialize the direct downloader with default configuration."""
        # List of Sci-Hub mirrors to try
        self.mirrors = [
            "https://sci-hub.se/",
            "https://sci-hub.st/",
            "https://sci-hub.ru/",
        ]
        
        # Session configuration
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_doi(self, doi: str, output_dir: str) -> bool:
        """
        Download a single paper by DOI.
        
        Args:
            doi: The DOI to download
            output_dir: Directory to save the PDF
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"Downloading DOI: {doi}")
        
        for mirror in self.mirrors:
            try:
                url = f"{mirror}{doi}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    # Check if response is PDF
                    if 'application/pdf' in response.headers.get('content-type', ''):
                        # Save PDF
                        filename = f"{doi.replace('/', '_')}.pdf"
                        filepath = os.path.join(output_dir, filename)
                        
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                            
                        print(f"✅ Downloaded to {filepath}")
                        return True
                    else:
                        # Handle HTML response (Sci-Hub page)
                        # You'd need a more sophisticated parser to extract the PDF link from the HTML
                        continue
                        
            except Exception as e:
                print(f"Failed with {mirror}: {e}")
                continue
                
        print(f"❌ Failed to download {doi}")
        return False
    
    def bulk_download(self, dois: List[str], output_dir: str = '../papers/downloaded/direct') -> int:
        """
        Download multiple papers from DOIs.
        
        Args:
            dois: List of DOIs to download
            output_dir: Directory to save PDFs
            
        Returns:
            int: Number of successfully downloaded papers
        """
        os.makedirs(output_dir, exist_ok=True)
        success_count = 0
        
        for doi in dois:
            if self.download_doi(doi, output_dir):
                success_count += 1
            time.sleep(2)  # Be respectful to servers
        
        print(f"\nDownload summary: {success_count}/{len(dois)} papers downloaded")
        return success_count