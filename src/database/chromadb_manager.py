"""
ChromaDB Manager for IFC Publications
Simple interface for managing publication embeddings
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
import uuid

from ..utils.logger import get_logger
from ..utils.config import load_config, get_data_dir
from ..scrapers.ifc_scraper import Publication

class ChromaDBManager:
    """Simple ChromaDB manager for publication embeddings"""
    
    def __init__(self, config_path: str = None):
        self.logger = get_logger(__name__)
        self.config = load_config(config_path)
        
        # Setup paths
        data_dir = get_data_dir()
        self.persist_directory = data_dir / "chromadb"
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding model
        model_name = 'all-MiniLM-L6-v2'
        self.logger.info(f"Loading embedding model: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)
        
        # Initialize ChromaDB client
        self.logger.info(f"Initializing ChromaDB at: {self.persist_directory}")
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.collection_name = "ifc_publications"
        self.collection = None
        
    def create_collection(self, reset: bool = False) -> None:
        """Create or get the publications collection"""
        try:
            if reset:
                try:
                    self.client.delete_collection(self.collection_name)
                    self.logger.info(f"Deleted existing collection: {self.collection_name}")
                except Exception:
                    pass  # Collection might not exist
            
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description": "IFC-UNAM Publications Embeddings",
                    "embedding_model": 'all-MiniLM-L6-v2',
                    "created_with": "UBMI-IFC-Podcast"
                }
            )
            
            self.logger.info(f"Collection '{self.collection_name}' ready")
            
        except Exception as e:
            self.logger.error(f"Error creating collection: {e}")
            raise
    
    def add_publications(self, publications: List[Publication], batch_size: int = 100) -> None:
        """Add publications to the database"""
        if not self.collection:
            self.create_collection()
        
        self.logger.info(f"Adding {len(publications)} publications to ChromaDB...")
        
        # Prepare data
        texts, metadatas, ids = self._prepare_publication_data(publications)
        
        # Generate embeddings
        self.logger.info("Generating embeddings...")
        embeddings = self.embedding_model.encode(
            texts, 
            show_progress_bar=True,
            batch_size=32
        )
        
        # Add to collection in batches
        total_added = 0
        for i in range(0, len(publications), batch_size):
            end_idx = min(i + batch_size, len(publications))
            
            batch_ids = ids[i:end_idx]
            batch_embeddings = embeddings[i:end_idx].tolist()
            batch_texts = texts[i:end_idx]
            batch_metadatas = metadatas[i:end_idx]
            
            try:
                self.collection.add(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    documents=batch_texts,
                    metadatas=batch_metadatas
                )
                total_added += len(batch_ids)
                self.logger.info(f"Added batch {i//batch_size + 1}, total: {total_added}/{len(publications)}")
                
            except Exception as e:
                self.logger.error(f"Error adding batch {i//batch_size + 1}: {e}")
                continue
        
        self.logger.info(f"✅ Successfully added {total_added} publications to ChromaDB")
    
    def _prepare_publication_data(self, publications: List[Publication]) -> Tuple[List[str], List[Dict], List[str]]:
        """Prepare publication data for ChromaDB"""
        texts = []
        metadatas = []
        ids = []
        
        for i, pub in enumerate(publications):
            # Create rich text for embedding
            text_parts = []
            
            if pub.title:
                text_parts.append(f"Title: {pub.title}")
            
            if pub.abstract:
                text_parts.append(f"Abstract: {pub.abstract}")
            else:
                # If no abstract, use title + authors + journal
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
            
            # Metadata (must be JSON-serializable)
            metadata = {
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
            metadatas.append(metadata)
        
        return texts, metadatas, ids
    
    def search_similar(self, query: str, n_results: int = 10) -> Dict:
        """Search for similar publications"""
        if not self.collection:
            raise ValueError("Collection not initialized. Call create_collection() first.")
        
        self.logger.info(f"Searching for: '{query}' (top {n_results} results)")
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return {
            'query': query,
            'results': results,
            'count': len(results['documents'][0]) if results['documents'] else 0
        }
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        if not self.collection:
            return {'error': 'Collection not initialized'}
        
        count = self.collection.count()
        
        if count > 0:
            sample = self.collection.peek(limit=min(100, count))
            
            # Analyze years
            years = [meta.get('year', 0) for meta in sample['metadatas']]
            
            # Analyze journals
            journals = [meta.get('journal', '') for meta in sample['metadatas']]
            unique_journals = len(set([j for j in journals if j]))
            
            # Analyze abstracts
            has_abstracts = sum(1 for meta in sample['metadatas'] if meta.get('has_abstract', False))
            
            stats = {
                'total_publications': count,
                'year_range': f"{min(years)}-{max(years)}" if years else "Unknown",
                'unique_journals_sample': unique_journals,
                'publications_with_abstracts_sample': f"{has_abstracts}/{len(sample['metadatas'])}",
                'collection_name': self.collection_name,
                'embedding_model': 'all-MiniLM-L6-v2'
            }
        else:
            stats = {
                'total_publications': 0,
                'collection_name': self.collection_name,
                'status': 'Empty collection'
            }
        
        return stats
    
    def export_embeddings(self, output_path: str = None) -> str:
        """Export embeddings and metadata to files"""
        if not self.collection:
            raise ValueError("Collection not initialized")
        
        if not output_path:
            output_path = get_data_dir() / "processed"
        
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Get all data
        count = self.collection.count()
        all_data = self.collection.get(include=['embeddings', 'documents', 'metadatas'])
        
        # Save embeddings
        embeddings = np.array(all_data['embeddings'])
        np.save(output_path / "embeddings.npy", embeddings)
        
        # Save metadata as CSV
        df = pd.DataFrame(all_data['metadatas'])
        df['document'] = all_data['documents']
        df['id'] = all_data['ids']
        df.to_csv(output_path / "publications_metadata.csv", index=False)
        
        self.logger.info(f"Exported {count} embeddings and metadata to {output_path}")
        return str(output_path)


def load_publications_from_json(file_path: str) -> List[Publication]:
    """Helper function to load publications from JSON file"""
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


# Example usage
if __name__ == "__main__":
    # Simple test
    db_manager = ChromaDBManager()
    
    # Load some publications
    publications = load_publications_from_json("../data/raw/all_ifc_publications.json")
    
    # Create collection and add publications
    db_manager.create_collection(reset=True)
    db_manager.add_publications(publications)
    
    # Test search
    results = db_manager.search_similar("neural mechanisms memory", n_results=5)
    print(f"Found {results['count']} similar publications")
    
    # Show stats
    stats = db_manager.get_collection_stats()
    print("Collection stats:", stats)