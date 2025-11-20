"""
Affiliation Filter Utility

This module provides functionality to automatically filter affiliation clusters
to identify only those relevant to specific target institutions, avoiding the
need to manually review hundreds of clusters.
"""

import json
import re
from typing import Dict, List, Any, Tuple, Set, Optional
from difflib import SequenceMatcher
from collections import defaultdict


class AffiliationFilter:
    """Filter affiliation clusters based on relevance to target institutions."""
    
    def __init__(self):
        """Initialize the affiliation filter with target keywords and patterns."""
        
        # Primary target institutions and departments
        self.target_keywords = {
            # Instituto de Fisiología Celular variations
            'ifc_spanish': [
                'instituto de fisiología celular',
                'instituto de fisiologia celular',
                'fisiología celular',
                'fisiologia celular',
                'ifc'
            ],
            
            # English versions
            'ifc_english': [
                'institute of cellular physiology',
                'institute for cellular physiology',
                'cellular physiology',
                'cell physiology'
            ],
            
            # Universidad Nacional Autónoma de México
            'unam': [
                'unam',
                'universidad nacional autónoma de méxico',
                'universidad nacional autonoma de mexico',
                'national autonomous university of mexico'
            ],
            
            # Related departments and fields
            'related_departments': [
                'molecular genetics',
                'biochemistry',
                'structural biology',
                'cell biology',
                'development',
                'neurociencias',
                'neurosciences',
                'biología celular',
                'biologia celular'
            ],
            
            # Physiology-related terms
            'physiology_terms': [
                'physiology',
                'fisiología',
                'fisiologia',
                'electrophysiology',
                'neurophysiology',
                'molecular physiology'
            ]
        }
        
        # Institution patterns (regex)
        self.institution_patterns = [
            r'instituto\s+de\s+fisiolog[íi]a\s+celular',
            r'institute\s+(?:of|for)\s+cellular\s+physiology',
            r'fisiolog[íi]a\s+celular',
            r'cellular\s+physiology',
            r'unam',
            r'universidad\s+nacional\s+autónoma\s+de\s+méxico'
        ]
        
        # Compile regex patterns
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.institution_patterns]
        
        # Negative keywords to filter out obviously irrelevant institutions
        self.negative_keywords = [
            'harvard', 'mit', 'stanford', 'yale', 'oxford', 'cambridge university',
            'university of california', 'university of michigan', 'university of washington',
            'johns hopkins', 'mayo clinic', 'cleveland clinic', 'nih',
            'university of toronto', 'mcgill', 'university of british columbia'
        ]
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text for comparison."""
        if not text:
            return ""
        
        # Remove special characters and normalize whitespace
        cleaned = re.sub(r'[^\w\s\-]', ' ', text)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip().lower()
        
        # Remove common noise words
        noise_words = ['the', 'and', 'of', 'at', 'in', 'for', 'to', 'from']
        words = cleaned.split()
        words = [w for w in words if w not in noise_words or len(w) > 2]
        
        return ' '.join(words)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        clean1 = self.clean_text(text1)
        clean2 = self.clean_text(text2)
        
        if not clean1 or not clean2:
            return 0.0
        
        return SequenceMatcher(None, clean1, clean2).ratio()
    
    def score_cluster_relevance(self, cluster: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Score a cluster's relevance to target institutions.
        
        Returns:
            Tuple of (score, matching_reasons)
        """
        representative = cluster.get('representative', '')
        variations = cluster.get('variations', [])
        
        all_text = [representative] + variations
        score = 0.0
        reasons = []
        
        # Check for negative keywords first (strong negative score)
        for text in all_text:
            clean_text = self.clean_text(text)
            for neg_keyword in self.negative_keywords:
                if neg_keyword.lower() in clean_text:
                    # Strong penalty for clearly unrelated institutions
                    score -= 10.0
                    reasons.append(f"Contains negative keyword: {neg_keyword}")
        
        # Pattern matching (highest score)
        pattern_matches = 0
        for text in all_text:
            for pattern in self.compiled_patterns:
                if pattern.search(text):
                    score += 15.0
                    pattern_matches += 1
                    reasons.append(f"Pattern match: {pattern.pattern} in '{text[:50]}'")
        
        # Keyword matching by category
        for category, keywords in self.target_keywords.items():
            category_matches = 0
            for text in all_text:
                clean_text = self.clean_text(text)
                for keyword in keywords:
                    if keyword.lower() in clean_text:
                        if category in ['ifc_spanish', 'ifc_english']:
                            score += 10.0  # High score for primary institution
                        elif category == 'unam':
                            score += 8.0   # High score for university
                        elif category == 'related_departments':
                            score += 5.0   # Medium score for departments
                        else:
                            score += 3.0   # Lower score for general terms
                        
                        category_matches += 1
                        reasons.append(f"Keyword match ({category}): '{keyword}' in '{text[:50]}'")
            
            # Bonus for multiple matches in same category
            if category_matches > 1:
                score += category_matches * 2.0
                reasons.append(f"Multiple matches in {category}: {category_matches}")
        
        # Text similarity to known good examples
        known_good_examples = [
            'Instituto de Fisiología Celular',
            'Institute of Cellular Physiology',
            'Instituto de Fisiología Celular UNAM',
            'Department of Cellular Physiology'
        ]
        
        max_similarity = 0.0
        best_match = ""
        for text in all_text:
            for example in known_good_examples:
                similarity = self.calculate_similarity(text, example)
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match = example
        
        if max_similarity > 0.7:
            score += max_similarity * 10.0
            reasons.append(f"High similarity ({max_similarity:.2f}) to '{best_match}'")
        elif max_similarity > 0.5:
            score += max_similarity * 5.0
            reasons.append(f"Moderate similarity ({max_similarity:.2f}) to '{best_match}'")
        
        # Penalize very generic or short names
        if len(representative) < 10:
            score -= 2.0
            reasons.append("Penalty: Very short representative name")
        
        # Bonus for variation count (more variations often mean more relevant)
        variation_count = len(variations)
        if variation_count > 5:
            score += min(variation_count * 0.5, 5.0)
            reasons.append(f"Bonus: {variation_count} variations")
        
        return score, reasons
    
    def filter_affiliations(self, affiliations_data: Dict[str, Any], 
                          min_score: float = 5.0, 
                          max_results: Optional[int] = None) -> Dict[str, Any]:
        """
        Filter affiliation clusters based on relevance scores.
        
        Args:
            affiliations_data: The loaded affiliations JSON data
            min_score: Minimum relevance score to include
            max_results: Maximum number of results to return
            
        Returns:
            Filtered affiliations data with scores
        """
        clusters = affiliations_data.get('affiliation_clusters', [])
        scored_clusters = []
        
        print(f"Scoring {len(clusters)} clusters...")
        
        for i, cluster in enumerate(clusters):
            score, reasons = self.score_cluster_relevance(cluster)
            
            if score >= min_score:
                scored_clusters.append({
                    'cluster': cluster,
                    'relevance_score': score,
                    'reasons': reasons,
                    'original_index': i
                })
            
            if (i + 1) % 50 == 0:
                print(f"Processed {i + 1}/{len(clusters)} clusters...")
        
        # Sort by relevance score (descending)
        scored_clusters.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Limit results if specified
        if max_results:
            scored_clusters = scored_clusters[:max_results]
        
        print(f"\nFound {len(scored_clusters)} relevant clusters (score >= {min_score})")
        
        # Create filtered data structure
        filtered_data = {
            'filtering_metadata': {
                'original_total_clusters': len(clusters),
                'filtered_clusters_count': len(scored_clusters),
                'min_score_threshold': min_score,
                'max_results_limit': max_results,
                'filter_date': affiliations_data.get('processing_date', 'unknown')
            },
            'total_pdfs_processed': affiliations_data.get('total_pdfs_processed', 0),
            'total_affiliations_found': affiliations_data.get('total_affiliations_found', 0),
            'relevant_affiliation_clusters': [
                {
                    'representative': item['cluster']['representative'],
                    'variations': item['cluster']['variations'],
                    'relevance_score': item['relevance_score'],
                    'matching_reasons': item['reasons'],
                    'original_cluster_index': item['original_index']
                }
                for item in scored_clusters
            ]
        }
        
        return filtered_data
    
    def print_top_matches(self, filtered_data: Dict[str, Any], top_n: int = 10):
        """Print the top N matches with their scores and reasons."""
        clusters = filtered_data.get('relevant_affiliation_clusters', [])
        
        print(f"\n=== TOP {min(top_n, len(clusters))} RELEVANT CLUSTERS ===\n")
        
        for i, cluster in enumerate(clusters[:top_n], 1):
            print(f"{i}. Representative: \"{cluster['representative']}\"")
            print(f"   Score: {cluster['relevance_score']:.2f}")
            print(f"   Variations: {len(cluster['variations'])}")
            print(f"   Reasons: {', '.join(cluster['matching_reasons'][:3])}{'...' if len(cluster['matching_reasons']) > 3 else ''}")
            print()


def main():
    """Main function to demonstrate the affiliation filtering."""
    
    # Load the affiliations data
    input_file = '/home/santi/Projects/UBMI-IFC-Podcast/data/processed/all_affiliations.json'
    
    print("Loading affiliations data...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Initialize filter
    filter_tool = AffiliationFilter()
    
    # Filter affiliations
    print("\nFiltering affiliations...")
    filtered_data = filter_tool.filter_affiliations(
        data, 
        min_score=5.0,  # Minimum relevance score
        max_results=50  # Top 50 results
    )
    
    # Print top matches
    filter_tool.print_top_matches(filtered_data, top_n=15)
    
    # Save filtered results
    output_file = '/home/santi/Projects/UBMI-IFC-Podcast/data/processed/filtered_affiliations.json'
    print(f"\nSaving filtered results to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Filtering complete! Reduced from {data.get('affiliation_clusters', [])} clusters to {len(filtered_data['relevant_affiliation_clusters'])} relevant clusters.")
    
    return filtered_data


if __name__ == "__main__":
    main()