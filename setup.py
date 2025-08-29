#!/usr/bin/env python3
"""
Setup script for UBMI-IFC-Podcast project
Helps with initial configuration and dependency verification
"""

import os
import sys
import subprocess
from pathlib import Path
import yaml


def print_banner():
    """Print setup banner"""
    print("🎙️  UBMI-IFC-Podcast Setup")
    print("=" * 40)
    print("Automated Scientific Podcast Generator")
    print("Instituto de Fisiología Celular, UNAM")
    print("=" * 40)


def check_python_version():
    """Check Python version"""
    print("\n📋 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        print(f"   Current version: {sys.version}")
        return False
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        return True


def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def setup_directories():
    """Create necessary directories"""
    print("\n📁 Setting up directories...")
    
    directories = [
        "data/raw",
        "data/processed", 
        "data/embeddings",
        "outputs/scripts",
        "outputs/podcasts",
        "logs"
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")
    
    return True


def setup_env_file():
    """Setup environment file"""
    print("\n🔐 Setting up environment configuration...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("   ℹ️  .env file already exists")
        response = input("   Do you want to overwrite it? (y/N): ").lower()
        if response != 'y':
            print("   ⏭️  Skipping .env setup")
            return True
    
    if env_example.exists():
        # Copy example to .env
        import shutil
        shutil.copy(env_example, env_file)
        print("   ✅ Created .env from template")
        
        print("\n   📝 Please edit .env file with your API keys:")
        print("   - OPENAI_API_KEY (for script generation)")
        print("   - ANTHROPIC_API_KEY (alternative to OpenAI)")
        print("   - ELEVENLABS_API_KEY (for audio generation)")
        print("   - PUBMED_EMAIL (required by NCBI)")
        
    else:
        print("   ❌ .env.example not found")
        return False
    
    return True


def setup_config():
    """Setup configuration file"""
    print("\n⚙️  Checking configuration...")
    
    config_file = Path("config/config.yaml")
    
    if config_file.exists():
        print("   ✅ Configuration file exists")
        
        # Validate email in config
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            email = config.get('pubmed', {}).get('email', '')
            if email == 'your-email@example.com':
                print("   ⚠️  Please update your email in config/config.yaml")
                print("   NCBI requires a valid email for PubMed access")
        except Exception as e:
            print(f"   ⚠️  Could not validate config: {e}")
    else:
        print("   ❌ Configuration file not found")
        return False
    
    return True


def test_imports():
    """Test if key dependencies can be imported"""
    print("\n🧪 Testing key imports...")
    
    test_imports = [
        ("requests", "Web scraping"),
        ("beautifulsoup4", "HTML parsing"),
        ("pandas", "Data processing"),
        ("numpy", "Numerical computing"),
        ("yaml", "Configuration parsing"),
    ]
    
    optional_imports = [
        ("aiohttp", "Async HTTP requests"),
        ("sklearn", "Machine learning"),
        ("sentence_transformers", "Text embeddings"),
        ("openai", "OpenAI API"),
        ("anthropic", "Anthropic API"),
        ("elevenlabs", "ElevenLabs TTS"),
    ]
    
    all_success = True
    
    for package, description in test_imports:
        try:
            __import__(package.replace("-", "_"))
            print(f"   ✅ {package:<20} ({description})")
        except ImportError:
            print(f"   ❌ {package:<20} ({description})")
            all_success = False
    
    print("\n   Optional dependencies:")
    for package, description in optional_imports:
        try:
            __import__(package.replace("-", "_"))
            print(f"   ✅ {package:<20} ({description})")
        except ImportError:
            print(f"   ⚠️  {package:<20} ({description}) - install if needed")
    
    return all_success


def run_component_test():
    """Run basic component test"""
    print("\n🔍 Testing pipeline components...")
    
    try:
        # Test basic imports
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from src.utils.config import load_config
        from src.utils.logger import setup_logger
        
        config = load_config()
        setup_logger(level="ERROR")  # Quiet logging for test
        
        print("   ✅ Configuration loading")
        print("   ✅ Logger setup")
        
        # Test component initialization (without API calls)
        components_tested = 0
        
        try:
            from src.scrapers.ifc_scraper import IFCPublicationScraper
            IFCPublicationScraper(config)
            print("   ✅ IFC Scraper")
            components_tested += 1
        except Exception as e:
            print(f"   ⚠️  IFC Scraper: {e}")
        
        try:
            from src.pubmed.searcher import PubMedSearcher
            PubMedSearcher(config)
            print("   ✅ PubMed Searcher")
            components_tested += 1
        except Exception as e:
            print(f"   ⚠️  PubMed Searcher: {e}")
        
        print(f"\n   📊 {components_tested}/2 core components working")
        return components_tested >= 1
        
    except Exception as e:
        print(f"   ❌ Component test failed: {e}")
        return False


def print_next_steps():
    """Print next steps for user"""
    print("\n🚀 Next Steps:")
    print("=" * 20)
    
    print("\n1. Configure API Keys:")
    print("   • Edit .env file with your API keys")
    print("   • Update email in config/config.yaml")
    
    print("\n2. Test Components:")
    print("   • python main.py --test-components")
    print("   • jupyter lab notebooks/")
    
    print("\n3. Run Pipeline:")
    print("   • python main.py --step-by-step  (for testing)")
    print("   • python main.py --full          (complete run)")
    
    print("\n4. Documentation:")
    print("   • README.md - Full documentation")
    print("   • notebooks/ - Interactive testing")
    
    print("\n📧 Remember: PubMed requires a valid email address!")


def main():
    """Main setup function"""
    print_banner()
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Install dependencies
    if success and not install_dependencies():
        print("   💡 Try: pip install --upgrade pip")
        print("   💡 Or: pip install -r requirements.txt --user")
        success = False
    
    # Setup directories
    if success:
        setup_directories()
    
    # Setup environment
    if success:
        setup_env_file()
    
    # Setup config
    if success:
        setup_config()
    
    # Test imports
    if success:
        if not test_imports():
            print("   💡 Some dependencies missing - install with pip")
    
    # Test components
    if success:
        run_component_test()
    
    # Print results
    if success:
        print("\n🎉 Setup completed successfully!")
    else:
        print("\n⚠️  Setup completed with warnings")
        print("   Some components may not work until issues are resolved")
    
    print_next_steps()


if __name__ == "__main__":
    main()
