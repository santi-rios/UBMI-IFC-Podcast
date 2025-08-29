"""
Main pipeline orchestrator for the podcast generation system
"""

import asyncio
from typing import Dict, List, Optional
from pathlib import Path
import json
from datetime import datetime

from .utils.logger import setup_logger, get_logger
from .utils.config import load_config, get_output_dir
from .scrapers.ifc_scraper import IFCPublicationScraper
from .pubmed.searcher import PubMedSearcher
from .embeddings.manager import EmbeddingsManager
from .llm.script_generator import PodcastScriptGenerator
from .audio.generator import AudioGenerator


class PodcastPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize the podcast pipeline
        
        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        
        # Setup logging
        setup_logger(
            level=self.config.get('logging', {}).get('level', 'INFO'),
            log_file=self.config.get('logging', {}).get('file')
        )
        
        self.logger = get_logger(__name__)
        self.logger.info("Initializing Podcast Pipeline")
        
        # Initialize components
        self.ifc_scraper = IFCPublicationScraper(self.config)
        self.pubmed_searcher = PubMedSearcher(self.config)
        self.embeddings_manager = EmbeddingsManager(self.config)
        self.script_generator = PodcastScriptGenerator(self.config)
        self.audio_generator = AudioGenerator(self.config)
        
        # Pipeline state
        self.ifc_articles = []
        self.pubmed_articles = []
        self.selected_articles = []
        self.podcast_script = ""
        self.audio_path = ""
    
    async def run_full_pipeline(self, force_refresh: bool = False) -> Dict:
        """
        Run the complete podcast generation pipeline
        
        Args:
            force_refresh: Force re-scraping of IFC articles
            
        Returns:
            Dictionary with pipeline results
        """
        self.logger.info("Starting full podcast generation pipeline")
        
        try:
            # Step 1: Get IFC articles (scrape or load from cache)
            await self._step_1_get_ifc_articles(force_refresh)
            
            # Step 2: Analyze research themes
            theme_analysis = await self._step_2_analyze_themes()
            
            # Step 3: Search PubMed for relevant articles
            await self._step_3_search_pubmed(theme_analysis)
            
            # Step 4: Find most similar articles
            await self._step_4_find_similar_articles()
            
            # Step 5: Generate podcast script
            await self._step_5_generate_script()
            
            # Step 6: Generate audio
            await self._step_6_generate_audio()
            
            # Step 7: Save results
            results = await self._step_7_save_results()
            
            self.logger.info("Pipeline completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            raise
    
    async def _step_1_get_ifc_articles(self, force_refresh: bool = False) -> None:
        """Step 1: Get IFC articles"""
        self.logger.info("Step 1: Getting IFC articles")
        
        # Check if we have cached articles
        cache_path = Path("data/processed/ifc_articles_cache.json")
        
        if not force_refresh and cache_path.exists():
            self.logger.info("Loading IFC articles from cache")
            with open(cache_path, 'r', encoding='utf-8') as f:
                self.ifc_articles = json.load(f)
        else:
            self.logger.info("Scraping IFC articles")
            articles = await self.ifc_scraper.scrape_all_years()
            
            # Convert to dict format and save
            self.ifc_articles = []
            for article in articles:
                self.ifc_articles.append({
                    'title': article.title,
                    'authors': article.authors,
                    'journal': article.journal,
                    'year': article.year,
                    'doi': article.doi,
                    'pubmed_id': article.pubmed_id,
                    'ifc_url': article.ifc_url,
                    'abstract': article.abstract,
                    'keywords': article.keywords
                })
            
            # Cache the results
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.ifc_articles, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Loaded {len(self.ifc_articles)} IFC articles")
    
    async def _step_2_analyze_themes(self) -> Dict:
        """Step 2: Analyze research themes"""
        self.logger.info("Step 2: Analyzing research themes")
        
        # Process IFC articles for embeddings
        self.embeddings_manager.process_ifc_articles(self.ifc_articles)
        
        # Analyze themes
        theme_analysis = self.embeddings_manager.analyze_research_themes()
        
        # Save embeddings for future use
        self.embeddings_manager.save_embeddings()
        
        self.logger.info(f"Identified {len(theme_analysis['clusters'])} research themes")
        return theme_analysis
    
    async def _step_3_search_pubmed(self, theme_analysis: Dict) -> None:
        """Step 3: Search PubMed for relevant articles"""
        self.logger.info("Step 3: Searching PubMed for relevant articles")
        
        # Extract keywords for search
        keywords = self.embeddings_manager.extract_research_keywords(theme_analysis)
        
        # Search PubMed
        max_results = self.config['pubmed']['max_articles_per_week']
        pmids = await self.pubmed_searcher.search_recent_articles(
            query_terms=keywords[:10],  # Use top 10 keywords
            days_back=7,
            max_results=max_results
        )
        
        # Fetch article details
        articles = await self.pubmed_searcher.fetch_article_details(pmids)
        
        # Convert to dict format
        self.pubmed_articles = []
        for article in articles:
            self.pubmed_articles.append({
                'pmid': article.pmid,
                'title': article.title,
                'abstract': article.abstract,
                'authors': article.authors,
                'journal': article.journal,
                'publication_date': article.publication_date,
                'doi': article.doi,
                'keywords': article.keywords,
                'mesh_terms': article.mesh_terms
            })
        
        self.logger.info(f"Found {len(self.pubmed_articles)} PubMed articles")
    
    async def _step_4_find_similar_articles(self) -> None:
        """Step 4: Find most similar articles"""
        self.logger.info("Step 4: Finding most similar articles")
        
        top_k = self.config['pubmed']['top_relevant_articles']
        self.selected_articles = self.embeddings_manager.find_similar_articles(
            self.pubmed_articles, 
            top_k=top_k
        )
        
        self.logger.info(f"Selected {len(self.selected_articles)} most relevant articles")
    
    async def _step_5_generate_script(self) -> None:
        """Step 5: Generate podcast script"""
        self.logger.info("Step 5: Generating podcast script")
        
        self.podcast_script = await self.script_generator.generate_podcast_script(
            self.selected_articles
        )
        
        # Generate metadata
        self.script_metadata = await self.script_generator.generate_episode_metadata(
            self.podcast_script, 
            self.selected_articles
        )
        
        self.logger.info("Podcast script generated")
    
    async def _step_6_generate_audio(self) -> None:
        """Step 6: Generate audio"""
        self.logger.info("Step 6: Generating audio")
        
        # Generate main podcast audio
        self.audio_path = await self.audio_generator.generate_audio(
            self.podcast_script
        )
        
        # Enhance audio quality
        enhanced_path = await self.audio_generator.enhance_audio(self.audio_path)
        self.audio_path = enhanced_path
        
        self.logger.info(f"Audio generated: {self.audio_path}")
    
    async def _step_7_save_results(self) -> Dict:
        """Step 7: Save all results"""
        self.logger.info("Step 7: Saving results")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = get_output_dir()
        
        # Save script
        script_path = self.script_generator.save_script(
            self.podcast_script,
            self.script_metadata,
            output_dir / "scripts" / f"podcast_script_{timestamp}.md"
        )
        
        # Save episode metadata
        episode_data = {
            'timestamp': timestamp,
            'metadata': self.script_metadata,
            'ifc_articles_count': len(self.ifc_articles),
            'pubmed_articles_count': len(self.pubmed_articles),
            'selected_articles_count': len(self.selected_articles),
            'selected_articles': self.selected_articles,
            'script_path': script_path,
            'audio_path': self.audio_path,
            'audio_info': self.audio_generator.get_audio_info(self.audio_path)
        }
        
        episode_path = output_dir / f"episode_data_{timestamp}.json"
        with open(episode_path, 'w', encoding='utf-8') as f:
            json.dump(episode_data, f, indent=2, ensure_ascii=False, default=str)
        
        results = {
            'success': True,
            'timestamp': timestamp,
            'episode_data_path': str(episode_path),
            'script_path': script_path,
            'audio_path': self.audio_path,
            'metadata': self.script_metadata
        }
        
        self.logger.info(f"Results saved to {episode_path}")
        return results
    
    async def run_step_by_step(self) -> None:
        """Run pipeline step by step for testing"""
        steps = [
            ("Get IFC Articles", self._step_1_get_ifc_articles),
            ("Analyze Themes", self._step_2_analyze_themes),
            ("Search PubMed", lambda: self._step_3_search_pubmed({})),
            ("Find Similar Articles", self._step_4_find_similar_articles),
            ("Generate Script", self._step_5_generate_script),
            ("Generate Audio", self._step_6_generate_audio),
            ("Save Results", self._step_7_save_results)
        ]
        
        for step_name, step_func in steps:
            try:
                self.logger.info(f"Running: {step_name}")
                await step_func()
                self.logger.info(f"Completed: {step_name}")
                
                # Pause for review
                input(f"Press Enter to continue to next step...")
                
            except Exception as e:
                self.logger.error(f"Failed at {step_name}: {str(e)}")
                break
    
    def get_status(self) -> Dict:
        """Get current pipeline status"""
        return {
            'ifc_articles_loaded': len(self.ifc_articles),
            'pubmed_articles_found': len(self.pubmed_articles),
            'selected_articles': len(self.selected_articles),
            'script_generated': bool(self.podcast_script),
            'audio_generated': bool(self.audio_path)
        }


async def main():
    """Main entry point"""
    pipeline = PodcastPipeline()
    
    # Run full pipeline
    try:
        results = await pipeline.run_full_pipeline()
        print("Pipeline completed successfully!")
        print(f"Episode title: {results['metadata']['title']}")
        print(f"Audio file: {results['audio_path']}")
        
    except Exception as e:
        print(f"Pipeline failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
