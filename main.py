#!/usr/bin/env python3
"""
Main entry point for the UBMI-IFC-Podcast pipeline

Usage:
    python main.py --full                    # Run complete pipeline
    python main.py --step-by-step           # Run step by step with pauses
    python main.py --test-components        # Test individual components
    python main.py --config CONFIG_PATH     # Use custom config file
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.pipeline import PodcastPipeline
from src.utils.logger import setup_logger, get_logger


async def test_components():
    """Test individual pipeline components"""
    print("🧪 Testing Pipeline Components")
    print("=" * 50)
    
    # Test IFC Scraper
    print("\n1. Testing IFC Scraper...")
    try:
        from src.scrapers.ifc_scraper import IFCPublicationScraper
        scraper = IFCPublicationScraper()
        print("   ✅ IFC Scraper initialized successfully")
    except Exception as e:
        print(f"   ❌ IFC Scraper failed: {e}")
    
    # Test PubMed Searcher
    print("\n2. Testing PubMed Searcher...")
    try:
        from src.pubmed.searcher import PubMedSearcher
        searcher = PubMedSearcher()
        print("   ✅ PubMed Searcher initialized successfully")
    except Exception as e:
        print(f"   ❌ PubMed Searcher failed: {e}")
    
    # Test Embeddings Manager
    print("\n3. Testing Embeddings Manager...")
    try:
        from src.embeddings.manager import EmbeddingsManager
        embeddings = EmbeddingsManager()
        print("   ✅ Embeddings Manager initialized successfully")
    except Exception as e:
        print(f"   ❌ Embeddings Manager failed: {e}")
    
    # Test LLM Script Generator
    print("\n4. Testing LLM Script Generator...")
    try:
        from src.llm.script_generator import PodcastScriptGenerator
        generator = PodcastScriptGenerator()
        print("   ✅ LLM Script Generator initialized successfully")
    except Exception as e:
        print(f"   ❌ LLM Script Generator failed: {e}")
    
    # Test Audio Generator
    print("\n5. Testing Audio Generator...")
    try:
        from src.audio.generator import AudioGenerator
        audio_gen = AudioGenerator()
        print("   ✅ Audio Generator initialized successfully")
    except Exception as e:
        print(f"   ❌ Audio Generator failed: {e}")
    
    print("\n" + "=" * 50)
    print("Component testing completed!")
    print("\n📝 Next steps:")
    print("   1. Fix any failed components")
    print("   2. Install missing dependencies with: pip install -r requirements.txt")
    print("   3. Configure API keys in .env file")
    print("   4. Test individual components with the notebooks in ./notebooks/")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="UBMI-IFC-Podcast Pipeline")
    parser.add_argument("--full", action="store_true", 
                       help="Run the complete pipeline")
    parser.add_argument("--step-by-step", action="store_true",
                       help="Run pipeline step by step with pauses")
    parser.add_argument("--test-components", action="store_true",
                       help="Test individual components")
    parser.add_argument("--config", type=str, default=None,
                       help="Path to custom config file")
    parser.add_argument("--force-refresh", action="store_true",
                       help="Force re-scraping of IFC articles")
    
    args = parser.parse_args()
    
    # Setup basic logging
    setup_logger(level="INFO")
    logger = get_logger(__name__)
    
    if args.test_components:
        await test_components()
        return
    
    if not any([args.full, args.step_by_step]):
        print("🎙️  UBMI-IFC-Podcast Pipeline")
        print("=" * 40)
        print("Please specify an action:")
        print("  --full              Run complete pipeline")
        print("  --step-by-step     Run with pauses between steps")
        print("  --test-components  Test individual components")
        print("  --help             Show all options")
        return
    
    # Initialize pipeline
    try:
        pipeline = PodcastPipeline(args.config)
        logger.info("Pipeline initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
        print("\n💡 Suggestions:")
        print("  1. Run --test-components to check individual components")
        print("  2. Check your configuration in config/config.yaml")
        print("  3. Ensure all dependencies are installed")
        return
    
    # Run pipeline
    try:
        if args.step_by_step:
            logger.info("Running pipeline step by step")
            await pipeline.run_step_by_step()
        else:
            logger.info("Running full pipeline")
            results = await pipeline.run_full_pipeline(args.force_refresh)
            
            print("\n🎉 Pipeline completed successfully!")
            print(f"📄 Episode: {results['metadata']['title']}")
            print(f"🎵 Audio: {results['audio_path']}")
            print(f"📝 Script: {results['script_path']}")
            
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        print("\n⏹️  Pipeline stopped by user")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        print(f"\n❌ Pipeline failed: {e}")
        print("\n💡 Troubleshooting:")
        print("  1. Check the logs for detailed error information")
        print("  2. Verify your API keys are correctly configured")
        print("  3. Test individual components with notebooks")


if __name__ == "__main__":
    asyncio.run(main())
