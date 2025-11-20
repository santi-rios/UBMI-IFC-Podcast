"""PDF text extraction module using PyMuPDF."""

import os
import glob
from typing import Dict, List, Optional
from tqdm import tqdm

try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDF not found. Install with: pip install pymupdf")
    fitz = None


class PDFTextExtractor:
    """Extracts text from PDF files using PyMuPDF."""
    
    def __init__(self):
        """Initialize the PDF text extractor."""
        if fitz is None:
            raise ImportError("PyMuPDF is required for PDF text extraction. Install with: pip install pymupdf")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from a single PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            str: Extracted text content
        """
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
            
            return text
        except Exception as e:
            print(f"Error extracting text from {os.path.basename(pdf_path)}: {e}")
            return ""
        finally:
            if 'doc' in locals():
                doc.close()
    
    def batch_process_pdfs(self, pdf_dir: str, limit: Optional[int] = None) -> Dict[str, str]:
        """
        Process multiple PDFs and extract text from all.
        
        Args:
            pdf_dir: Directory containing PDF files
            limit: Maximum number of PDFs to process (None for all)
            
        Returns:
            dict: Dictionary mapping filename to extracted text
        """
        pdf_files = glob.glob(os.path.join(pdf_dir, "**", "*.pdf"), recursive=True)
        
        if limit:
            pdf_files = pdf_files[:limit]
        
        print(f"Found {len(pdf_files)} PDF files to process")
        
        results = {}
        for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
            filename = os.path.basename(pdf_path)
            text = self.extract_text_from_pdf(pdf_path)
            if text:
                results[filename] = text
        
        print(f"Successfully extracted text from {len(results)} PDFs")
        return results
    
    def extract_first_pages_text(self, pdf_path: str, max_chars: int = 20000) -> str:
        """
        Extract text from the first few pages of a PDF (where affiliations typically appear).
        
        Args:
            pdf_path: Path to the PDF file
            max_chars: Maximum number of characters to extract
            
        Returns:
            str: Extracted text from first pages
        """
        full_text = self.extract_text_from_pdf(pdf_path)
        return full_text[:max_chars] if full_text else ""
    
    def extract_and_store_full_text(
        self, 
        publications_with_dois: List[Dict], 
        pdf_dir: str
    ) -> List[Dict]:
        """
        Extract full text from PDFs and store it with publications data.
        
        Args:
            publications_with_dois: List of publications with DOI information
            pdf_dir: Directory containing PDF files
            
        Returns:
            list: Publications with added full text where available
        """
        # Track which publications have full text
        has_full_text = set()
        
        # Extract text from PDFs where available
        pdf_texts = self.batch_process_pdfs(pdf_dir)
        
        # Match PDFs to publications by DOI
        for pub in publications_with_dois:
            if pub.get('doi'):
                # Look for PDF with DOI in filename (PyPaperBot naming convention)
                doi_filename = pub['doi'].replace('/', '_') + '.pdf'
                if doi_filename in pdf_texts:
                    # Store text with publication
                    pub['full_text'] = pdf_texts[doi_filename]
                    # Ensure metadata exists
                    if 'metadata' not in pub:
                        pub['metadata'] = {}
                    pub['metadata']['has_full_text'] = True
                    has_full_text.add(pub['doi'])
        
        print(f"Added full text to {len(has_full_text)} publications")
        return publications_with_dois