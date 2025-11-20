"""
Example: How to use filtered affiliations in your research workflow

This example shows how to integrate the filtered affiliations into your existing
publication search and analysis pipeline.
"""

import json
import sys
import os

def load_filtered_affiliations():
    """Load the filtered affiliation clusters."""
    
    filtered_file = '/home/santi/Projects/UBMI-IFC-Podcast/data/processed/filtered_affiliations.json'
    
    with open(filtered_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data['relevant_affiliation_clusters']

def get_search_terms_from_affiliations(min_score=10.0):
    """
    Extract clean search terms from filtered affiliations for PubMed searches.
    
    Args:
        min_score: Minimum relevance score to include
        
    Returns:
        List of clean search terms
    """
    
    clusters = load_filtered_affiliations()
    search_terms = set()
    
    print(f"Extracting search terms from clusters with score >= {min_score}")
    
    for cluster in clusters:
        if cluster['relevance_score'] >= min_score:
            
            # Add the representative term
            representative = cluster['representative'].strip()
            if len(representative) > 5:  # Skip very short terms
                search_terms.add(clean_affiliation_term(representative))
            
            # Add high-quality variations
            for variation in cluster['variations'][:10]:  # Limit to top 10 variations
                cleaned = clean_affiliation_term(variation)
                if len(cleaned) > 10:  # Only substantial terms
                    search_terms.add(cleaned)
    
    return sorted(list(search_terms))

def clean_affiliation_term(term):
    """Clean an affiliation term for search use."""
    import re
    
    # Remove common noise
    cleaned = re.sub(r'[^\w\s\-]', ' ', term)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'^[•\d]+\s*', '', cleaned)  # Remove bullets and numbers
    cleaned = cleaned.strip()
    
    # Remove very generic words at start
    generic_prefixes = ['the ', 'a ', 'an ', 'of ']
    for prefix in generic_prefixes:
        if cleaned.lower().startswith(prefix):
            cleaned = cleaned[len(prefix):]
    
    return cleaned

def generate_pubmed_search_queries():
    """Generate PubMed search queries using filtered affiliations."""
    
    search_terms = get_search_terms_from_affiliations(min_score=15.0)  # High quality only
    
    # Group by type
    ifc_terms = [term for term in search_terms if 'fisiolog' in term.lower() or 'cellular physiology' in term.lower()]
    unam_terms = [term for term in search_terms if 'unam' in term.lower() or 'nacional autónoma' in term.lower()]
    department_terms = [term for term in search_terms if any(dept in term.lower() for dept in ['department', 'departamento'])]
    
    queries = []
    
    # Primary IFC search
    if ifc_terms:
        primary_query = ' OR '.join([f'"{term}"[Affiliation]' for term in ifc_terms[:5]])
        queries.append(f"({primary_query})")
    
    # UNAM search
    if unam_terms:
        unam_query = ' OR '.join([f'"{term}"[Affiliation]' for term in unam_terms[:3]])
        queries.append(f"({unam_query})")
    
    return queries

def demonstrate_usage():
    """Demonstrate how to use the filtered affiliations."""
    
    print("=" * 70)
    print("🔍 FILTERED AFFILIATIONS USAGE EXAMPLE")
    print("=" * 70)
    
    # Load filtered data
    clusters = load_filtered_affiliations()
    
    print(f"\n📊 Loaded {len(clusters)} filtered clusters")
    print("\n🏆 TOP 5 CLUSTERS:")
    
    for i, cluster in enumerate(clusters[:5], 1):
        print(f"\n{i}. {cluster['representative']}")
        print(f"   Score: {cluster['relevance_score']:.1f}")
        print(f"   Variations: {len(cluster['variations'])}")
        print(f"   Sample: {cluster['variations'][0] if cluster['variations'] else 'N/A'}")
    
    # Show search terms
    print("\n" + "=" * 70)
    print("🔍 EXTRACTED SEARCH TERMS (Score >= 15.0)")
    print("=" * 70)
    
    search_terms = get_search_terms_from_affiliations(min_score=15.0)
    
    for i, term in enumerate(search_terms[:10], 1):
        print(f"{i:2d}. {term}")
    
    if len(search_terms) > 10:
        print(f"    ... and {len(search_terms) - 10} more terms")
    
    # Show PubMed queries
    print("\n" + "=" * 70)
    print("🔍 GENERATED PUBMED SEARCH QUERIES")
    print("=" * 70)
    
    queries = generate_pubmed_search_queries()
    
    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}:")
        print(f"{query}")
    
    # Integration example
    print("\n" + "=" * 70)
    print("⚙️  INTEGRATION EXAMPLE")
    print("=" * 70)
    
    print("""
# Example: Use in your existing PubMed search workflow

from your_pubmed_module import PubmedSearcher

# Load filtered affiliations
clusters = load_filtered_affiliations()

# Use only high-scoring clusters for search
high_relevance_clusters = [
    cluster for cluster in clusters 
    if cluster['relevance_score'] >= 15.0
]

searcher = PubmedSearcher()

for cluster in high_relevance_clusters:
    print(f"Searching for: {cluster['representative']}")
    
    # Use representative term
    results = searcher.search_by_affiliation(cluster['representative'])
    
    # Or use all variations
    all_terms = [cluster['representative']] + cluster['variations']
    for term in all_terms[:5]:  # Limit to top 5
        results.extend(searcher.search_by_affiliation(term))
    
    print(f"Found {len(results)} publications")
""")

def save_for_manual_review():
    """Save a manual review file with the most relevant clusters."""
    
    clusters = load_filtered_affiliations()
    
    # Select top clusters for manual review
    top_clusters = [c for c in clusters if c['relevance_score'] >= 10.0]
    
    output_file = '/home/santi/Projects/UBMI-IFC-Podcast/data/processed/manual_review_affiliations.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("AFFILIATION CLUSTERS FOR MANUAL REVIEW\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated from top {len(top_clusters)} clusters (score >= 10.0)\n\n")
        
        for i, cluster in enumerate(top_clusters, 1):
            f.write(f"{i:2d}. REPRESENTATIVE: {cluster['representative']}\n")
            f.write(f"    SCORE: {cluster['relevance_score']:.1f}\n")
            f.write(f"    VARIATIONS ({len(cluster['variations'])}):\n")
            
            for j, variation in enumerate(cluster['variations'], 1):
                f.write(f"    {j:2d}) {variation}\n")
            
            f.write(f"\n    REASONS: {', '.join(cluster['matching_reasons'][:2])}...\n")
            f.write("\n" + "-" * 50 + "\n\n")
    
    print(f"✅ Manual review file saved: {output_file}")
    print(f"📊 Contains {len(top_clusters)} high-relevance clusters for final review")

if __name__ == "__main__":
    demonstrate_usage()
    print("\n" + "=" * 70)
    
    save_choice = input("💾 Save manual review file? (y/n): ").strip().lower()
    if save_choice == 'y':
        save_for_manual_review()
    
    print("\n🎉 Example complete!")
    print("\nNext steps:")
    print("1. Review the filtered results")
    print("2. Integrate the search terms into your PubMed workflow")
    print("3. Use the high-scoring clusters for your publication searches")
    print("4. Customize the filtering parameters if needed")