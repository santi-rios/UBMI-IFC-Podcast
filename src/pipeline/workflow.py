"""Main pipeline orchestration for database expansion workflow."""

import os
import json
import time
from typing import List, Dict, Any, Optional

# Use absolute imports that work when imported into notebooks
try:
    from pdf_acquisition import PyPaperBotWrapper
    from publication_management import BibTexManager, PublicationDatabase
    from text_extraction import PDFTextExtractor
    from affiliation_mining import EnhancedAffiliationMiner, AffiliationClustering
    from pubmed import EnhancedPubmedSearcher
    from data_quality import KeywordExtractor, PublicationClassifier
except ImportError:
    # Fallback to relative imports for package installation
    from ..pdf_acquisition import PyPaperBotWrapper
    from ..publication_management import BibTexManager, PublicationDatabase
    from ..text_extraction import PDFTextExtractor
    from ..affiliation_mining import EnhancedAffiliationMiner, AffiliationClustering
    from ..pubmed import EnhancedPubmedSearcher
    from ..data_quality import KeywordExtractor, PublicationClassifier


class DatabaseExpansionPipeline:
    """Main pipeline for expanding publication databases."""
    
    def __init__(self):
        """Initialize the database expansion pipeline."""
        self.pdf_downloader = PyPaperBotWrapper()
        self.bibtex_manager = BibTexManager()
        self.database = PublicationDatabase()
        self.pdf_extractor = PDFTextExtractor()
        self.affiliation_miner = EnhancedAffiliationMiner()
        self.clustering = AffiliationClustering()
        self.pubmed_searcher = EnhancedPubmedSearcher()
        self.keyword_extractor = KeywordExtractor()
        self.classifier = PublicationClassifier()
    
    def mine_affiliations_from_pdfs(
        self, 
        pdf_dir: str, 
        output_json: Optional[str] = None, 
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract affiliations from PDFs and return structured data.
        
        Args:
            pdf_dir: Directory containing PDFs to process
            output_json: Optional path to save results as JSON
            limit: Maximum number of PDFs to process
            
        Returns:
            dict: Dictionary with affiliation data
        """
        print("🔍 Initializing affiliation miner...")
        
        # Extract text from PDFs
        print("\n📄 Extracting text from PDFs...")
        pdf_texts = self.pdf_extractor.batch_process_pdfs(pdf_dir, limit)
        
        try:
            # Mine affiliations from each PDF
            print("\n🏢 Mining affiliations from extracted text...")
            all_affiliations = set()
            pdf_affiliations = {}
            
            for filename, text in pdf_texts.items():
                try:
                    # Process only the first few pages where affiliations typically appear
                    first_pages_text = text[:20000]
                    affiliations = self.affiliation_miner.extract_affiliations_advanced_nlp(first_pages_text)
                    
                    if affiliations:
                        pdf_affiliations[filename] = list(affiliations)
                        all_affiliations.update(affiliations)
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
                    continue
            
            # Cluster similar affiliations
            print(f"\n🧩 Clustering {len(all_affiliations)} discovered affiliations...")
            clusters = self.clustering.analyze_affiliations_with_clustering(list(all_affiliations))
            
            # Generate PubMed search variations
            print("\n🔎 Generating PubMed search variations...")
            pubmed_variations = self.clustering.generate_pubmed_search_variations(clusters)
            
            # Compile results
            results = {
                'total_pdfs_processed': len(pdf_texts),
                'total_affiliations_found': len(all_affiliations),
                'affiliation_clusters': [
                    {'representative': cluster[0], 'variations': cluster} 
                    for cluster in clusters
                ],
                'pubmed_search_variations': pubmed_variations,
                'pdf_affiliations': pdf_affiliations
            }
            
            # Save results if requested
            if output_json:
                os.makedirs(os.path.dirname(output_json), exist_ok=True)
                with open(output_json, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"\n✅ Results saved to {output_json}")
            
            return results

        except Exception as e:
            print(f"❌ Error in affiliation mining process: {e}")
            if output_json:
                # Save what we have so far as backup
                with open(output_json + '.partial', 'w', encoding='utf-8') as f:
                    json.dump({
                        'error': str(e),
                        'partial_results': pdf_affiliations if 'pdf_affiliations' in locals() else {}
                    }, f, indent=2, ensure_ascii=False)
            return {
                'total_pdfs_processed': 0, 
                'total_affiliations_found': 0, 
                'affiliation_clusters': [], 
                'pubmed_search_variations': [], 
                'pdf_affiliations': {}, 
                'error': str(e)
            }
    
    def analyze_pdfs_and_search_pubmed_with_review(
        self, 
        pdf_dir: str, 
        output_dir: str = '../data/processed/affiliations', 
        limit_pdfs: Optional[int] = None, 
        max_results_per_query: int = 20
    ) -> Dict[str, Any]:
        """
        Complete pipeline with manual review: Extract affiliations, review them, then search PubMed.
        
        Args:
            pdf_dir: Directory containing PDFs to process
            output_dir: Directory for saving outputs
            limit_pdfs: Maximum number of PDFs to process (None for all)
            max_results_per_query: Maximum results per PubMed query
            
        Returns:
            dict: Results dictionary
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Step 1: Mine affiliations from PDFs
        print("🔎 Step 1: Mining affiliations from PDFs...")
        affiliations_output = os.path.join(output_dir, "discovered_affiliations.json")
        affiliation_results = self.mine_affiliations_from_pdfs(
            pdf_dir=pdf_dir,
            output_json=affiliations_output,
            limit=limit_pdfs
        )
        
        clusters = affiliation_results.get('affiliation_clusters', [])
        
        # Step 2: Manual review of affiliations
        print("\n🔍 Step 2: Reviewing discovered affiliations...")
        if not clusters:
            print("⚠️ No affiliation clusters found.")
            approved_variations = []
        else:
            # Extract clusters from results
            raw_clusters = [cluster['variations'] for cluster in clusters]
            approved_variations = self.clustering.review_and_select_affiliations(raw_clusters)
        
        # Step 3: Format approved variations for PubMed search
        if not approved_variations:
            print("⚠️ No affiliations approved. Using default affiliations for PubMed search.")
            pubmed_variations = None  # Will use defaults in PubmedSearcher
        else:
            import re
            pubmed_variations = []
            for variation in approved_variations:
                # Clean and format for PubMed
                clean_aff = re.sub(r'[,.:]', '', variation)
                clean_aff = re.sub(r'\s+', ' ', clean_aff).strip()
                pubmed_variation = f"{clean_aff}[Affiliation]"
                pubmed_variations.append(pubmed_variation)
        
            print(f"🔍 Generated {len(pubmed_variations)} PubMed search variations")
            print("\nSample variations:")
            for i, var in enumerate(pubmed_variations[:5]):
                print(f"   {i+1}. {var}")
        
        # Step 4: Search PubMed with approved affiliations
        print("\n🔍 Step 4: Searching PubMed with approved affiliations...")
        articles = self.pubmed_searcher.comprehensive_search(
            affiliation_variations=pubmed_variations,
            max_per_query=max_results_per_query
        )
        
        # Step 5: Save PubMed results
        print(f"\n📊 Found {len(articles)} articles from PubMed")
        pubmed_output = os.path.join(output_dir, "pubmed_results.json")
        with open(pubmed_output, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        print(f"✅ PubMed results saved to {pubmed_output}")
        
        # Step 6: Summary
        print("\n📋 Pipeline Summary:")
        print(f"   PDFs processed: {affiliation_results['total_pdfs_processed']}")
        print(f"   Unique affiliations found: {affiliation_results['total_affiliations_found']}")
        print(f"   Affiliation clusters reviewed: {len(clusters)}")
        print(f"   Approved variations: {len(approved_variations)}")
        print(f"   PubMed articles found: {len(articles)}")
        
        return {
            'affiliation_results': affiliation_results,
            'approved_variations': approved_variations,
            'pubmed_articles': articles
        }
    
    def run_complete_pipeline_with_review(
        self, 
        initial_json_path: str, 
        pdf_dir: str, 
        output_dir: str = '../data/processed'
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Complete automated pipeline with affiliation review step.
        
        Args:
            initial_json_path: Path to existing publications JSON
            pdf_dir: Directory containing PDFs for affiliation mining
            output_dir: Output directory for results
            
        Returns:
            tuple: (final_database, pipeline_report)
        """
        print("🚀 Starting complete publication database expansion pipeline\n")
        
        # Step 1: Load existing data
        print("📂 Step 1: Loading existing publications")
        existing_pubs = self.database.load_publications(initial_json_path)
        print(f"   Loaded {len(existing_pubs)} existing publications")
        
        # Step 2: Mine affiliations from PDFs and review
        print("\n🔍 Step 2: Mining and reviewing affiliations from PDFs")
        review_results = self.analyze_pdfs_and_search_pubmed_with_review(
            pdf_dir=pdf_dir,
            output_dir=os.path.join(output_dir, 'affiliations'),
            max_results_per_query=30
        )
        
        new_articles = review_results.get('pubmed_articles', [])
        print(f"   Found {len(new_articles)} potential new articles")
        
        # Step 3: Merge databases
        print("\n🔄 Step 3: Merging and deduplicating databases")
        expanded_json_path = os.path.join(output_dir, 'expanded_ifc_publications.json')
        final_db = self.database.merge_publication_databases(existing_pubs, new_articles, expanded_json_path)

        # Step 4: Create final BibTeX
        print("\n📚 Step 4: Creating final BibTeX file")
        final_bibtex_path = os.path.join(output_dir, 'final_ifc_publications.bib')
        self.bibtex_manager.create_bibtex_from_publications(final_db, final_bibtex_path)
        
        # Step 5: Generate summary report
        print("\n📊 Step 5: Generating summary report")
        report = self.database.generate_summary_report(
            len(existing_pubs), final_db, new_articles, output_dir
        )
        
        print(f"\n✅ Pipeline complete! Summary:")
        print(f"   📊 Original: {report['original_count']} publications")
        print(f"   🆕 Added: {report['new_additions']} new publications")
        print(f"   📈 Final: {report['final_count']} total publications")
        
        return final_db, report
    
    def extract_and_store_full_text(
        self, 
        publications_with_dois: List[Dict[str, Any]], 
        pdf_dir: str
    ) -> List[Dict[str, Any]]:
        """
        Extract full text from PDFs and store it with publications data.
        
        Args:
            publications_with_dois: Publications with DOI information
            pdf_dir: Directory containing PDF files
            
        Returns:
            list: Publications with added full text where available
        """
        return self.pdf_extractor.extract_and_store_full_text(publications_with_dois, pdf_dir)
    
    def generate_quality_report(self, publications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive quality report for publications.
        
        Args:
            publications: List of publication dictionaries
            
        Returns:
            dict: Quality report
        """
        return self.classifier.generate_quality_report(publications)