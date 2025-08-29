"""
LLM integration for podcast script generation
"""

import asyncio
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
import json

from ..utils.logger import get_logger
from ..utils.config import load_config


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response from LLM"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self.logger = get_logger(__name__)
        
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI API"""
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.api_key)
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 4000)
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            raise


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider"""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key
        self.model = model
        self.logger = get_logger(__name__)
        
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using Anthropic API"""
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            response = await client.messages.create(
                model=self.model,
                max_tokens=kwargs.get('max_tokens', 4000),
                temperature=kwargs.get('temperature', 0.7),
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            self.logger.error(f"Anthropic API error: {str(e)}")
            raise


class PodcastScriptGenerator:
    """Generate podcast scripts from research articles"""
    
    def __init__(self, config: Dict = None):
        self.config = config or load_config()
        self.logger = get_logger(__name__)
        self.llm_provider = self._setup_llm_provider()
        
    def _setup_llm_provider(self) -> LLMProvider:
        """Setup LLM provider based on configuration"""
        provider_name = self.config['llm']['provider']
        
        if provider_name == 'openai':
            api_key = self.config['api_keys']['openai']
            if not api_key:
                raise ValueError("OpenAI API key not found in configuration")
            return OpenAIProvider(api_key, self.config['llm']['model'])
            
        elif provider_name == 'anthropic':
            api_key = self.config['api_keys']['anthropic']
            if not api_key:
                raise ValueError("Anthropic API key not found in configuration")
            return AnthropicProvider(api_key, self.config['llm']['model'])
            
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")
    
    async def generate_podcast_script(self, articles: List[Dict]) -> str:
        """
        Generate podcast script from selected articles
        
        Args:
            articles: List of article dictionaries with similarity scores
            
        Returns:
            Generated podcast script
        """
        self.logger.info(f"Generating podcast script from {len(articles)} articles")
        
        # Prepare articles summary for prompt
        articles_summary = self._prepare_articles_summary(articles)
        
        # Build prompt
        prompt = self._build_podcast_prompt(articles_summary)
        
        # Generate script
        script = await self.llm_provider.generate_response(
            prompt,
            temperature=self.config['llm']['temperature'],
            max_tokens=self.config['llm']['max_tokens']
        )
        
        self.logger.info("Podcast script generated successfully")
        return script
    
    def _prepare_articles_summary(self, articles: List[Dict]) -> str:
        """Prepare a summary of articles for the prompt"""
        summaries = []
        
        for i, article in enumerate(articles[:10], 1):  # Limit to top 10
            summary = f"""
Article {i}:
Title: {article.get('title', 'N/A')}
Authors: {', '.join(article.get('authors', [])) if article.get('authors') else 'N/A'}
Journal: {article.get('journal', 'N/A')}
Publication Date: {article.get('publication_date', 'N/A')}
Similarity Score: {article.get('combined_score', 0):.3f}

Abstract: {article.get('abstract', 'N/A')[:500]}{'...' if len(article.get('abstract', '')) > 500 else ''}

Key Findings: {self._extract_key_findings(article)}
"""
            summaries.append(summary)
        
        return "\n".join(summaries)
    
    def _extract_key_findings(self, article: Dict) -> str:
        """Extract key findings from article (simplified version)"""
        abstract = article.get('abstract', '')
        
        # Simple heuristic: look for conclusion-like sentences
        sentences = abstract.split('.')
        key_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in 
                   ['found', 'showed', 'demonstrated', 'revealed', 'concluded', 'results indicate']):
                key_sentences.append(sentence)
        
        return '. '.join(key_sentences[:2]) if key_sentences else "Key findings not extracted."
    
    def _build_podcast_prompt(self, articles_summary: str) -> str:
        """Build the prompt for podcast script generation"""
        
        base_prompt = self.config['llm']['podcast_prompt_template']
        
        enhanced_prompt = f"""
{base_prompt.format(articles=articles_summary)}

Additional Instructions:
- Focus on the most impactful and interconnected findings
- Create smooth transitions between different topics
- Include brief explanations of complex scientific terms
- Maintain an engaging, conversational tone
- Structure: Opening hook (30 seconds), Main content (4 minutes), Closing (30 seconds)
- Target audience: Educated general public with interest in science
- Mention that this is generated from recent research relevant to IFC-UNAM's research areas

Please generate a complete podcast script with clear sections and timing cues.
"""
        
        return enhanced_prompt
    
    async def generate_episode_metadata(self, script: str, articles: List[Dict]) -> Dict:
        """
        Generate metadata for the podcast episode
        
        Args:
            script: Generated podcast script
            articles: Source articles
            
        Returns:
            Dictionary with episode metadata
        """
        # Extract title from script or generate one
        title_prompt = f"""
Based on this podcast script, generate a compelling episode title (max 60 characters):

{script[:1000]}...

Title should be:
- Engaging and informative
- Suitable for a scientific podcast
- Focused on the main themes
- Professional but accessible

Respond with only the title, no additional text.
"""
        
        title = await self.llm_provider.generate_response(
            title_prompt,
            temperature=0.5,
            max_tokens=100
        )
        
        # Generate description
        description_prompt = f"""
Write a brief podcast episode description (100-150 words) based on this script:

{script[:1500]}...

Description should:
- Summarize key topics covered
- Mention it's based on recent research
- Be engaging for potential listeners
- Include relevant scientific areas

Respond with only the description text.
"""
        
        description = await self.llm_provider.generate_response(
            description_prompt,
            temperature=0.6,
            max_tokens=200
        )
        
        # Extract keywords from articles
        keywords = set()
        for article in articles:
            if article.get('mesh_terms'):
                keywords.update(article['mesh_terms'][:3])  # Top 3 MeSH terms per article
            if article.get('keywords'):
                keywords.update(article['keywords'][:3])
        
        metadata = {
            'title': title.strip(),
            'description': description.strip(),
            'keywords': list(keywords)[:10],  # Limit to 10 keywords
            'source_articles_count': len(articles),
            'top_journals': list(set([article.get('journal', '') for article in articles[:5]])),
            'generation_date': str(pd.Timestamp.now().date()) if 'pd' in globals() else None
        }
        
        return metadata
    
    def save_script(self, script: str, metadata: Dict = None, output_path: str = None) -> str:
        """Save podcast script to file"""
        if not output_path:
            from ..utils.config import get_output_dir
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = get_output_dir() / "scripts" / f"podcast_script_{timestamp}.md"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create formatted script with metadata
        full_content = []
        
        if metadata:
            full_content.append("# Podcast Episode")
            full_content.append(f"## {metadata.get('title', 'Untitled Episode')}")
            full_content.append("")
            full_content.append("### Metadata")
            full_content.append(f"- **Generated**: {metadata.get('generation_date', 'Unknown')}")
            full_content.append(f"- **Source Articles**: {metadata.get('source_articles_count', 0)}")
            full_content.append(f"- **Keywords**: {', '.join(metadata.get('keywords', []))}")
            full_content.append("")
            full_content.append("### Description")
            full_content.append(metadata.get('description', ''))
            full_content.append("")
            full_content.append("---")
            full_content.append("")
        
        full_content.append("## Script")
        full_content.append("")
        full_content.append(script)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(full_content))
        
        self.logger.info(f"Saved podcast script to {output_path}")
        return str(output_path)


async def main():
    """Test function"""
    generator = PodcastScriptGenerator()
    
    # Mock articles for testing
    sample_articles = [
        {
            'title': 'Neural mechanisms of learning and memory',
            'abstract': 'We investigated the cellular mechanisms underlying learning and memory formation in the hippocampus. Our results showed that specific neural pathways are activated during memory consolidation.',
            'authors': ['Smith, J.', 'Johnson, M.'],
            'journal': 'Nature Neuroscience',
            'publication_date': '2024-01-15',
            'combined_score': 0.95
        }
    ]
    
    try:
        script = await generator.generate_podcast_script(sample_articles)
        metadata = await generator.generate_episode_metadata(script, sample_articles)
        
        print("Generated script preview:")
        print(script[:500] + "...")
        print(f"\nTitle: {metadata['title']}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
