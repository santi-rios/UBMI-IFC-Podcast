"""
Publication embedding system using ChromaDB and UMAP
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json
import hashlib
import uuid

# Embedding and ML libraries
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import umap
from sklearn.preprocessing import StandardScaler

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

# Handle imports for both module and notebook usage
try:
    from ..utils.logger import get_logger
    from ..utils.config import load_config, get_data_dir
    from ..scrapers.ifc_scraper import Publication
except ImportError:
    # Fallback for notebook usage
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.logger import get_logger
    from utils.config import load_config, get_data_dir
    from scrapers.ifc_scraper import Publication


class PublicationEmbeddingSystem:
    """System for creating and managing publication embeddings"""
    
    def __init__(self, config: Dict = None):
        self.config = config or load_config()
        self.logger = get_logger(__name__)
        
        # Initialize embedding model
        model_name = 'all-MiniLM-L6-v2'  # Multilingual, fast, good quality
        self.logger.info(f"Loading embedding model: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)
        
        # Initialize ChromaDB
        self.data_dir = get_data_dir()
        self.chroma_dir = self.data_dir / "chromadb"
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Initializing ChromaDB at: {self.chroma_dir}")
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.chroma_dir),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Collection for publications
        self.collection_name = "ifc_publications"
        
    def create_publication_embeddings(self, publications: List[Publication]) -> Dict:
        """
        Create embeddings for all publications
        
        Args:
            publications: List of Publication objects
            
        Returns:
            Dictionary with embeddings and metadata
        """
        self.logger.info(f"Creating embeddings for {len(publications)} publications...")
        
        # Prepare texts for embedding
        texts, metadata, ids = self._prepare_texts_and_metadata(publications)
        
        # Generate embeddings
        self.logger.info("Generating embeddings with SentenceTransformer...")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        
        # Store in ChromaDB
        self.logger.info("Storing embeddings in ChromaDB...")
        self._store_in_chromadb(ids, embeddings, texts, metadata)
        
        # Create UMAP projection
        self.logger.info("Creating UMAP projection...")
        umap_embeddings = self._create_umap_projection(embeddings)
        
        result = {
            'embeddings': embeddings,
            'umap_embeddings': umap_embeddings,
            'texts': texts,
            'metadata': metadata,
            'ids': ids,
            'publications': publications
        }
        
        # Save results
        self._save_embedding_results(result)
        
        self.logger.info("✅ Embedding creation complete!")
        return result
    
    def _prepare_texts_and_metadata(self, publications: List[Publication]) -> Tuple[List[str], List[Dict], List[str]]:
        """Prepare texts and metadata for embedding"""
        texts = []
        metadata = []
        ids = []
        
        for i, pub in enumerate(publications):
            # Create rich text for embedding
            text_parts = []
            
            if pub.title:
                text_parts.append(f"Title: {pub.title}")
            
            if pub.abstract:
                text_parts.append(f"Abstract: {pub.abstract}")
            else:
                # Fallback: use authors and journal if no abstract
                if pub.authors:
                    text_parts.append(f"Authors: {pub.authors}")
                if pub.journal:
                    text_parts.append(f"Journal: {pub.journal}")
            
            if pub.keywords:
                text_parts.append(f"Keywords: {', '.join(pub.keywords)}")
            
            combined_text = " ".join(text_parts)
            texts.append(combined_text)
            
            # Create unique ID
            pub_id = f"pub_{i}_{uuid.uuid4().hex[:8]}"
            ids.append(pub_id)
            
            # Metadata for ChromaDB (must be JSON serializable)
            meta = {
                'title': pub.title or '',
                'authors': pub.authors or '',
                'journal': pub.journal or '',
                'year': int(pub.year),
                'doi': pub.doi or '',
                'pubmed_id': pub.pubmed_id or '',
                'ifc_url': pub.ifc_url or '',
                'has_abstract': bool(pub.abstract),
                'text_length': len(combined_text),
                'index': i
            }
            metadata.append(meta)
        
        return texts, metadata, ids
    
    def _store_in_chromadb(self, ids: List[str], embeddings: np.ndarray, 
                          texts: List[str], metadata: List[Dict]):
        """Store embeddings in ChromaDB"""
        try:
            # Delete existing collection if it exists
            try:
                self.chroma_client.delete_collection(self.collection_name)
                self.logger.info(f"Deleted existing collection: {self.collection_name}")
            except Exception:
                pass  # Collection might not exist
            
            # Create new collection
            collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "IFC-UNAM Publications Embeddings"}
            )
            
            # Add documents in batches
            batch_size = 100
            total_added = 0
            
            for i in range(0, len(ids), batch_size):
                end_idx = min(i + batch_size, len(ids))
                
                batch_ids = ids[i:end_idx]
                batch_embeddings = embeddings[i:end_idx].tolist()
                batch_texts = texts[i:end_idx]
                batch_metadata = metadata[i:end_idx]
                
                collection.add(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    documents=batch_texts,
                    metadatas=batch_metadata
                )
                
                total_added += len(batch_ids)
                self.logger.info(f"Added batch {i//batch_size + 1}, total: {total_added}/{len(ids)}")
            
            self.logger.info(f"✅ Stored {len(ids)} embeddings in ChromaDB collection '{self.collection_name}'")
            
        except Exception as e:
            self.logger.error(f"Error storing in ChromaDB: {e}")
            raise
    
    def _create_umap_projection(self, embeddings: np.ndarray) -> np.ndarray:
        """Create 2D UMAP projection of embeddings"""
        if len(embeddings) < 15:
            self.logger.warning("Too few embeddings for optimal UMAP. Using smaller n_neighbors.")
            n_neighbors = max(2, len(embeddings) - 1)
        else:
            n_neighbors = 15
        
        # Standardize embeddings
        scaler = StandardScaler()
        embeddings_scaled = scaler.fit_transform(embeddings)
        
        # UMAP projection
        umap_reducer = umap.UMAP(
            n_components=2,
            n_neighbors=n_neighbors,
            min_dist=0.1,
            metric='cosine',
            random_state=42
        )
        
        umap_embeddings = umap_reducer.fit_transform(embeddings_scaled)
        
        # Save UMAP model for future use
        import pickle
        models_dir = self.data_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        
        with open(models_dir / "umap_model.pkl", 'wb') as f:
            pickle.dump(umap_reducer, f)
        
        with open(models_dir / "scaler.pkl", 'wb') as f:
            pickle.dump(scaler, f)
        
        return umap_embeddings
    
    def _save_embedding_results(self, results: Dict):
        """Save embedding results to disk"""
        output_dir = self.data_dir / "processed"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save embeddings and UMAP coordinates
        np.save(output_dir / "publication_embeddings.npy", results['embeddings'])
        np.save(output_dir / "umap_coordinates.npy", results['umap_embeddings'])
        
        # Save metadata as DataFrame with UMAP coordinates
        df = pd.DataFrame(results['metadata'])
        df['umap_x'] = results['umap_embeddings'][:, 0]
        df['umap_y'] = results['umap_embeddings'][:, 1]
        df['id'] = results['ids']
        df.to_csv(output_dir / "publications_with_coordinates.csv", index=False)
        
        self.logger.info(f"Saved embedding results to {output_dir}")
    
    def visualize_embeddings(self, results: Dict, save_plots: bool = True):
        """Create visualizations of the embeddings"""
        self.logger.info("Creating embedding visualizations...")
        
        # Prepare data for plotting
        df = pd.DataFrame(results['metadata'])
        df['umap_x'] = results['umap_embeddings'][:, 0]
        df['umap_y'] = results['umap_embeddings'][:, 1]
        
        # Create visualizations
        figs = []
        
        # 1. Basic scatter plot colored by year
        fig1 = self._plot_basic_scatter(df)
        figs.append(('basic_scatter', fig1))
        
        # 2. Interactive plot with hover information
        fig2 = self._plot_interactive(df)
        figs.append(('interactive', fig2))
        
        # 3. Journal clustering (if we have multiple journals)
        if len(df['journal'].unique()) > 1:
            fig3 = self._plot_journal_clusters(df)
            figs.append(('journal_clusters', fig3))
        
        # 4. Year evolution (if we have multiple years)
        if len(df['year'].unique()) > 1:
            fig4 = self._plot_year_evolution(df)
            figs.append(('year_evolution', fig4))
        
        if save_plots:
            self._save_plots(figs)
        
        return figs
    
    def _plot_basic_scatter(self, df: pd.DataFrame):
        """Basic scatter plot of UMAP coordinates"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        scatter = ax.scatter(
            df['umap_x'], df['umap_y'], 
            c=df['year'], 
            cmap='viridis', 
            alpha=0.7, 
            s=60
        )
        
        ax.set_xlabel('UMAP Dimension 1')
        ax.set_ylabel('UMAP Dimension 2')
        ax.set_title('IFC Publications Embedding Space (UMAP Projection)')
        ax.grid(True, alpha=0.3)
        
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Publication Year')
        
        plt.tight_layout()
        return fig
    
    def _plot_interactive(self, df: pd.DataFrame):
        """Interactive plotly visualization"""
        # Truncate long titles for hover display
        df_plot = df.copy()
        df_plot['title_short'] = df_plot['title'].apply(lambda x: x[:60] + '...' if len(x) > 60 else x)
        df_plot['authors_short'] = df_plot['authors'].apply(lambda x: x[:40] + '...' if len(x) > 40 else x)
        
        fig = px.scatter(
            df_plot, 
            x='umap_x', 
            y='umap_y',
            color='year',
            hover_data=['title_short', 'authors_short', 'journal'],
            title='Interactive IFC Publications Map',
            labels={'umap_x': 'UMAP Dimension 1', 'umap_y': 'UMAP Dimension 2'},
            color_continuous_scale='viridis'
        )
        
        fig.update_traces(marker=dict(size=8, opacity=0.7))
        fig.update_layout(width=1000, height=700)
        
        return fig
    
    def _plot_journal_clusters(self, df: pd.DataFrame):
        """Plot clustering by journal"""
        # Get top journals (limit to avoid overcrowding)
        top_journals = df['journal'].value_counts().head(10).index
        df_filtered = df[df['journal'].isin(top_journals)]
        
        fig = px.scatter(
            df_filtered,
            x='umap_x',
            y='umap_y',
            color='journal',
            title='Publications Clustered by Journal (Top 10)',
            labels={'umap_x': 'UMAP Dimension 1', 'umap_y': 'UMAP Dimension 2'}
        )
        
        fig.update_traces(marker=dict(size=10, opacity=0.8))
        fig.update_layout(width=1200, height=800)
        
        return fig
    
    def _plot_year_evolution(self, df: pd.DataFrame):
        """Plot showing evolution over years"""
        years = sorted(df['year'].unique())
        n_years = len(years)
        
        if n_years <= 4:
            cols = 2
            rows = 2
        else:
            cols = 3
            rows = (n_years + 2) // 3
        
        fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
        if rows == 1 and cols == 1:
            axes = [axes]
        elif rows == 1 or cols == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()
        
        colors = plt.cm.viridis(np.linspace(0, 1, n_years))
        
        for i, year in enumerate(years):
            if i < len(axes):
                year_data = df[df['year'] == year]
                axes[i].scatter(year_data['umap_x'], year_data['umap_y'], 
                              alpha=0.7, s=50, color=colors[i])
                axes[i].set_title(f'Publications {year} (n={len(year_data)})')
                axes[i].set_xlabel('UMAP Dimension 1')
                axes[i].set_ylabel('UMAP Dimension 2')
                axes[i].grid(True, alpha=0.3)
        
        # Hide empty subplots
        for i in range(len(years), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        return fig
    
    def _save_plots(self, figs: List[Tuple[str, any]]):
        """Save plots to disk"""
        plots_dir = self.data_dir / "plots"
        plots_dir.mkdir(parents=True, exist_ok=True)
        
        for name, fig in figs:
            try:
                if hasattr(fig, 'write_html'):  # Plotly figure
                    fig.write_html(plots_dir / f"{name}.html")
                    self.logger.info(f"Saved {name}.html")
                else:  # Matplotlib figure
                    fig.savefig(plots_dir / f"{name}.png", dpi=300, bbox_inches='tight')
                    fig.savefig(plots_dir / f"{name}.pdf", bbox_inches='tight')
                    self.logger.info(f"Saved {name}.png and {name}.pdf")
                    plt.close(fig)  # Close to free memory
            except Exception as e:
                self.logger.error(f"Error saving plot {name}: {e}")
    
    def search_similar_publications(self, query: str, n_results: int = 5) -> Dict:
        """Search for similar publications using vector similarity"""
        try:
            collection = self.chroma_client.get_collection(self.collection_name)
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results
        except Exception as e:
            self.logger.error(f"Error searching publications: {e}")
            return {'error': str(e)}


def load_publications_from_file(file_path: str) -> List[Publication]:
    """Load publications from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    publications = []
    for item in data:
        pub = Publication(
            title=item.get('title', ''),
            authors=item.get('authors', ''),
            journal=item.get('journal', ''),
            year=item.get('year', 2024),
            doi=item.get('doi'),
            pubmed_id=item.get('pubmed_id'),
            ifc_url=item.get('ifc_url'),
            abstract=item.get('abstract'),
            keywords=item.get('keywords')
        )
        publications.append(pub)
    
    return publications