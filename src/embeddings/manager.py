"""
Embeddings generation and similarity search
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import pickle
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from ..utils.logger import get_logger
from ..utils.config import load_config


class EmbeddingsManager:
    """Manage embeddings for articles and similarity search"""
    
    def __init__(self, config: Dict = None):
        self.config = config or load_config()
        self.logger = get_logger(__name__)
        self.model_name = self.config['embeddings']['model_name']
        self.model = None
        self.ifc_embeddings = None
        self.ifc_articles = None
        
    def load_model(self):
        """Load the sentence transformer model"""
        if self.model is None:
            self.logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings
            
        Returns:
            Numpy array of embeddings
        """
        self.load_model()
        
        self.logger.info(f"Generating embeddings for {len(texts)} texts")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        return embeddings
    
    def process_ifc_articles(self, articles_data: List[Dict]) -> None:
        """
        Process IFC articles and generate embeddings
        
        Args:
            articles_data: List of article dictionaries
        """
        self.logger.info(f"Processing {len(articles_data)} IFC articles")
        
        # Prepare texts for embedding (title + abstract)
        texts = []
        processed_articles = []
        
        for article in articles_data:
            # Combine title and abstract for embedding
            text_parts = []
            if article.get('title'):
                text_parts.append(article['title'])
            if article.get('abstract'):
                text_parts.append(article['abstract'])
            
            if text_parts:
                combined_text = ". ".join(text_parts)
                texts.append(combined_text)
                processed_articles.append(article)
        
        # Generate embeddings
        self.ifc_embeddings = self.generate_embeddings(texts)
        self.ifc_articles = processed_articles
        
        self.logger.info(f"Generated embeddings for {len(processed_articles)} IFC articles")
    
    def analyze_research_themes(self, n_clusters: int = None) -> Dict:
        """
        Analyze research themes using clustering
        
        Args:
            n_clusters: Number of clusters. If None, uses config default
            
        Returns:
            Dictionary with cluster analysis results
        """
        if self.ifc_embeddings is None:
            raise ValueError("No IFC embeddings available. Run process_ifc_articles first.")
        
        n_clusters = n_clusters or self.config['embeddings']['clustering']['n_clusters']
        
        self.logger.info(f"Analyzing research themes with {n_clusters} clusters")
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(self.ifc_embeddings)
        
        # Analyze clusters
        clusters = {}
        for i in range(n_clusters):
            cluster_mask = cluster_labels == i
            cluster_articles = [self.ifc_articles[j] for j in range(len(self.ifc_articles)) if cluster_mask[j]]
            
            # Extract keywords/themes from cluster articles
            cluster_titles = [article.get('title', '') for article in cluster_articles]
            cluster_abstracts = [article.get('abstract', '') for article in cluster_articles]
            
            clusters[f"cluster_{i}"] = {
                'size': len(cluster_articles),
                'articles': cluster_articles,
                'sample_titles': cluster_titles[:5],  # First 5 titles as examples
                'centroid': kmeans.cluster_centers_[i]
            }
        
        # Generate theme keywords for each cluster
        theme_analysis = {
            'clusters': clusters,
            'total_articles': len(self.ifc_articles),
            'cluster_sizes': [clusters[f"cluster_{i}"]['size'] for i in range(n_clusters)]
        }
        
        self.logger.info("Research theme analysis completed")
        return theme_analysis
    
    def find_similar_articles(self, query_articles: List[Dict], 
                            top_k: int = 10) -> List[Dict]:
        """
        Find articles most similar to IFC research themes
        
        Args:
            query_articles: List of articles to score for similarity
            top_k: Number of top articles to return
            
        Returns:
            List of articles ranked by similarity
        """
        if self.ifc_embeddings is None:
            raise ValueError("No IFC embeddings available. Run process_ifc_articles first.")
        
        self.logger.info(f"Finding similar articles among {len(query_articles)} candidates")
        
        # Prepare query texts
        query_texts = []
        valid_articles = []
        
        for article in query_articles:
            text_parts = []
            if article.get('title'):
                text_parts.append(article['title'])
            if article.get('abstract'):
                text_parts.append(article['abstract'])
            
            if text_parts:
                combined_text = ". ".join(text_parts)
                query_texts.append(combined_text)
                valid_articles.append(article)
        
        if not query_texts:
            self.logger.warning("No valid query articles found")
            return []
        
        # Generate embeddings for query articles
        query_embeddings = self.generate_embeddings(query_texts)
        
        # Calculate similarity scores
        similarity_scores = []
        
        for i, query_embedding in enumerate(query_embeddings):
            # Calculate maximum similarity to any IFC article
            similarities = cosine_similarity(
                query_embedding.reshape(1, -1), 
                self.ifc_embeddings
            )[0]
            max_similarity = np.max(similarities)
            mean_similarity = np.mean(similarities)
            
            # Store article with similarity scores
            article_with_score = valid_articles[i].copy()
            article_with_score['max_similarity'] = float(max_similarity)
            article_with_score['mean_similarity'] = float(mean_similarity)
            article_with_score['combined_score'] = float(0.7 * max_similarity + 0.3 * mean_similarity)
            
            similarity_scores.append(article_with_score)
        
        # Sort by combined similarity score
        similarity_scores.sort(key=lambda x: x['combined_score'], reverse=True)
        
        self.logger.info(f"Found top {top_k} similar articles")
        return similarity_scores[:top_k]
    
    def save_embeddings(self, output_dir: str = None) -> None:
        """Save embeddings and processed articles"""
        if output_dir is None:
            from ..utils.config import get_data_dir
            output_dir = get_data_dir() / "embeddings"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.ifc_embeddings is not None:
            # Save embeddings
            embeddings_path = output_dir / "ifc_embeddings.npy"
            np.save(embeddings_path, self.ifc_embeddings)
            
            # Save articles
            articles_path = output_dir / "ifc_articles.pkl"
            with open(articles_path, 'wb') as f:
                pickle.dump(self.ifc_articles, f)
            
            self.logger.info(f"Saved embeddings to {output_dir}")
    
    def load_embeddings(self, input_dir: str = None) -> None:
        """Load saved embeddings and articles"""
        if input_dir is None:
            from ..utils.config import get_data_dir
            input_dir = get_data_dir() / "embeddings"
        
        input_dir = Path(input_dir)
        
        embeddings_path = input_dir / "ifc_embeddings.npy"
        articles_path = input_dir / "ifc_articles.pkl"
        
        if embeddings_path.exists() and articles_path.exists():
            self.ifc_embeddings = np.load(embeddings_path)
            
            with open(articles_path, 'rb') as f:
                self.ifc_articles = pickle.load(f)
            
            self.logger.info(f"Loaded embeddings from {input_dir}")
        else:
            self.logger.warning(f"Embeddings not found in {input_dir}")
    
    def extract_research_keywords(self, theme_analysis: Dict) -> List[str]:
        """
        Extract key research terms from theme analysis
        
        Args:
            theme_analysis: Results from analyze_research_themes
            
        Returns:
            List of research keywords for PubMed search
        """
        keywords = []
        
        # For now, extract from cluster sample titles
        # In a more sophisticated implementation, you might use TF-IDF or other methods
        for cluster_id, cluster_data in theme_analysis['clusters'].items():
            titles = cluster_data['sample_titles']
            
            # Simple keyword extraction from titles
            for title in titles:
                if title:
                    # Split and filter common words
                    words = title.lower().split()
                    filtered_words = [
                        word.strip('.,!?;:()[]') for word in words 
                        if len(word) > 3 and word not in ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'she', 'use', 'way', 'will', 'with']
                    ]
                    keywords.extend(filtered_words)
        
        # Get most common keywords
        from collections import Counter
        keyword_counts = Counter(keywords)
        top_keywords = [word for word, count in keyword_counts.most_common(20)]
        
        self.logger.info(f"Extracted {len(top_keywords)} research keywords")
        return top_keywords


def main():
    """Test function"""
    # This would be called with actual data
    embeddings_manager = EmbeddingsManager()
    
    # Mock data for testing
    sample_articles = [
        {
            'title': 'Neural mechanisms of memory formation',
            'abstract': 'We investigated how neurons form memories in the hippocampus...'
        },
        {
            'title': 'Cardiac physiology under stress',
            'abstract': 'Heart rate variability was measured during stress conditions...'
        }
    ]
    
    embeddings_manager.process_ifc_articles(sample_articles)
    theme_analysis = embeddings_manager.analyze_research_themes()
    
    print(f"Found {len(theme_analysis['clusters'])} research themes")


if __name__ == "__main__":
    main()
