"""PyPaperBot wrapper for automated paper downloading."""

import os
import sys
import time
import subprocess
from typing import List, Optional


class PyPaperBotWrapper:
    """Wrapper for PyPaperBot command-line tool."""
    
    def __init__(self):
        """Initialize the PyPaperBot wrapper."""
        self.base_command = ["python", "-m", "PyPaperBot"]
    
    def check_dependencies(self) -> bool:
        """Check if PyPaperBot and its dependencies are installed."""
        try:
            import importlib.util
            if importlib.util.find_spec("undetected_chromedriver") is None:
                print("Installing missing dependency: undetected-chromedriver")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "undetected-chromedriver"])
                print("Dependency installed successfully")
            return True
        except Exception as e:
            print(f"Warning: Could not verify/install dependencies: {e}")
            return False
    
    def check_chrome_installed(self) -> bool:
        """Check if Chrome/Chromium is installed on the system."""
        chrome_paths = [
            "google-chrome",
            "chromium-browser",
            "chromium",
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser"
        ]
        
        for path in chrome_paths:
            try:
                result = subprocess.run(["which", path], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ Chrome/Chromium found at: {result.stdout.strip()}")
                    return True
            except Exception:
                continue
        
        print("❌ Chrome/Chromium not found. Please install it for PyPaperBot to work properly.")
        print("   On Ubuntu/Debian: sudo apt install chromium-browser")
        print("   On Fedora: sudo dnf install chromium")
        return False
    
    def download_papers(
        self, 
        dois: Optional[List[str]] = None, 
        output_dir: str = '../papers/downloaded', 
        min_year: Optional[int] = None, 
        mode: int = 2,
        use_doi_filename: bool = True
    ) -> bool:
        """
        Download papers using PyPaperBot.
        
        Args:
            dois: List of DOIs to download (None for query-based search)
            output_dir: Directory to save outputs
            min_year: Minimum publication year
            mode: 0=BibTeX only, 1=PDF only, 2=both
            use_doi_filename: Use DOI as filename instead of paper title
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check dependencies
        if not self.check_dependencies() or not self.check_chrome_installed():
            print("❌ Dependencies not satisfied")
            return False
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Build command
        cmd = self.base_command.copy()
        
        if dois:
            # For multiple DOIs, create a temporary DOI file
            doi_file = os.path.join(output_dir, "temp_dois.txt")
            with open(doi_file, 'w') as f:
                f.write('\n'.join(dois))
            cmd.extend(["--doi-file", doi_file])
        
        # Add output directory
        cmd.extend(["--dwn-dir", output_dir])
        
        # Add optional parameters
        if min_year:
            cmd.extend(["--min-year", str(min_year)])
        
        # Add mode (restrict parameter)
        cmd.extend(["--restrict", str(mode)])
        
        # Use DOI as filename if requested
        if use_doi_filename:
            cmd.append("--use-doi-as-filename")
        
        # Execute command
        print(f"Executing command: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Print output
            print("\nOutput:")
            print(result.stdout)
            
            if result.stderr:
                print("\nErrors:")
                print(result.stderr)
                
            return result.returncode == 0
        except Exception as e:
            print(f"Error executing PyPaperBot: {e}")
            return False
    
    def bulk_download(
        self, 
        all_dois: List[str], 
        output_dir: str, 
        chunk_size: int = 50
    ) -> bool:
        """
        Download papers in chunks to avoid overwhelming the system.
        
        Args:
            all_dois: List of all DOIs to download
            output_dir: Directory to save outputs
            chunk_size: Number of DOIs per chunk
            
        Returns:
            bool: True if all chunks successful, False otherwise
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Process in chunks
        success_count = 0
        total_chunks = (len(all_dois) + chunk_size - 1) // chunk_size
        
        for i in range(0, len(all_dois), chunk_size):
            chunk = all_dois[i:i+chunk_size]
            chunk_num = (i // chunk_size) + 1
            
            print(f"\nProcessing chunk {chunk_num}/{total_chunks} ({len(chunk)} DOIs)")
            chunk_dir = os.path.join(output_dir, f"batch_{chunk_num}")
            
            if self.download_papers(chunk, output_dir=chunk_dir, mode=1):
                success_count += 1
                
            # Add delay between chunks
            if chunk_num < total_chunks:
                print("Waiting before next batch...")
                time.sleep(30)  # 30 second delay between batches
        
        success = success_count == total_chunks
        print(f"\nCompleted {success_count}/{total_chunks} batches successfully")
        return success