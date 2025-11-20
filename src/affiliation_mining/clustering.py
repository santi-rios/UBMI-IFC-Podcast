"""Affiliation clustering using similarity matching."""

from typing import List, Dict, Any
from difflib import SequenceMatcher


class AffiliationClustering:
    """Handles clustering of similar affiliations."""
    
    def __init__(self, similarity_threshold: float = 0.7):
        """
        Initialize the affiliation clustering system.
        
        Args:
            similarity_threshold: Minimum similarity score to group affiliations
        """
        self.similarity_threshold = similarity_threshold
    
    def similarity(self, a: str, b: str) -> float:
        """
        Calculate similarity between two affiliation strings.
        
        Args:
            a: First affiliation string
            b: Second affiliation string
            
        Returns:
            float: Similarity score between 0 and 1
        """
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def analyze_affiliations_with_clustering(self, affiliations_list: List[str]) -> List[List[str]]:
        """
        Advanced analysis with similarity clustering.
        
        Args:
            affiliations_list: List of affiliation strings to cluster
            
        Returns:
            list: List of clusters, each containing similar affiliations
        """
        # Group similar affiliations
        clusters = []
        processed = set()
        
        for affiliation in affiliations_list:
            if affiliation in processed:
                continue
                
            # Find similar affiliations
            cluster = [affiliation]
            processed.add(affiliation)
            
            for other in affiliations_list:
                if other not in processed and self.similarity(affiliation, other) > self.similarity_threshold:
                    cluster.append(other)
                    processed.add(other)
            
            if len(cluster) >= 1:
                clusters.append(cluster)
        
        return clusters
    
    def generate_pubmed_search_variations(self, affiliation_clusters: List[List[str]]) -> List[str]:
        """
        Generate PubMed search variations from affiliation clusters.
        
        Args:
            affiliation_clusters: List of affiliation clusters
            
        Returns:
            list: List of PubMed search variations
        """
        import re
        
        search_variations = []
        
        # Process each cluster
        for cluster in affiliation_clusters:
            # Use the first (representative) affiliation from each cluster
            if cluster:
                rep_affiliation = cluster[0]
                
                # Clean and format for PubMed
                # Remove common punctuation and normalize spaces
                clean_aff = re.sub(r'[,.:]', '', rep_affiliation)
                clean_aff = re.sub(r'\s+', ' ', clean_aff).strip()
                
                # Add [Affiliation] tag for PubMed
                pubmed_variation = f"{clean_aff}[Affiliation]"
                search_variations.append(pubmed_variation)
        
        return search_variations
    
    def review_and_select_affiliations(self, affiliation_clusters: List[List[str]]) -> List[str]:
        """
        Interactive review of discovered affiliation clusters before PubMed search.
        
        Args:
            affiliation_clusters: List of affiliation clusters discovered from PDFs
            
        Returns:
            list: List of approved affiliation variations for PubMed search
        """
        print("\n📋 AFFILIATION REVIEW\n")
        print("Review the following affiliation clusters discovered from PDFs:")
        print("Select which clusters to include in PubMed search\n")
        
        approved_clusters = []
        approved_variations = []
        
        for i, cluster in enumerate(affiliation_clusters):
            if not cluster:
                continue
                
            representative = cluster[0]
            print(f"\nCluster {i+1}: {representative}")
            
            if len(cluster) > 1:
                print("  Variations:")
                for j, variation in enumerate(cluster[1:]):
                    print(f"    {j+1}. {variation}")
            
            # Ask for approval
            while True:
                choice = input(f"\nInclude cluster {i+1} in PubMed search? (y/n): ").lower()
                if choice in ('y', 'yes', 'n', 'no'):
                    break
                print("Please answer 'y' or 'n'")
            
            if choice in ('y', 'yes'):
                approved_clusters.append(cluster)
                approved_variations.extend(cluster)
                print(f"✅ Cluster {i+1} approved")
            else:
                print(f"❌ Cluster {i+1} excluded")
        
        print(f"\n📊 Summary: Approved {len(approved_clusters)}/{len(affiliation_clusters)} clusters")
        print(f"Total of {len(approved_variations)} affiliation variations will be used for PubMed search")
        
        return approved_variations