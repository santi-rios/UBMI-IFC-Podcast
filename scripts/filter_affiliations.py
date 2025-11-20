#!/usr/bin/env python3
"""
Interactive Affiliation Filter

This script provides an easy-to-use interface for filtering affiliation clusters
and customizing the filtering parameters based on your needs.
"""

import json
import sys
import os

# Add src to path if needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from affiliation_mining.affiliation_filter import AffiliationFilter


def interactive_filter():
    """Interactive interface for filtering affiliations."""
    
    print("=" * 60)
    print("🔍 INTERACTIVE AFFILIATION FILTER")
    print("=" * 60)
    
    # Input files
    input_file = '/home/santi/Projects/UBMI-IFC-Podcast/data/processed/all_affiliations.json'
    
    if not os.path.exists(input_file):
        print(f"❌ Error: Input file not found: {input_file}")
        return
    
    print(f"📁 Input file: {input_file}")
    
    # Load data
    print("\n📊 Loading affiliation data...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_clusters = len(data.get('affiliation_clusters', []))
    print(f"✅ Loaded {total_clusters} clusters")
    
    # Initialize filter
    filter_tool = AffiliationFilter()
    
    # Get user preferences
    print("\n⚙️  FILTERING OPTIONS:")
    print("1. Conservative (high relevance only, score ≥ 10.0)")
    print("2. Moderate (good balance, score ≥ 5.0)")  
    print("3. Liberal (include more possibilities, score ≥ 2.0)")
    print("4. Custom (set your own parameters)")
    
    while True:
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            min_score = 10.0
            max_results = 20
            break
        elif choice == "2":
            min_score = 5.0
            max_results = 50
            break
        elif choice == "3":
            min_score = 2.0
            max_results = 100
            break
        elif choice == "4":
            try:
                min_score = float(input("Minimum score threshold (e.g., 5.0): "))
                max_results_input = input("Maximum results (press Enter for no limit): ").strip()
                max_results = int(max_results_input) if max_results_input else None
                break
            except ValueError:
                print("❌ Invalid input. Please try again.")
        else:
            print("❌ Invalid choice. Please select 1-4.")
    
    # Apply filter
    print(f"\n🔄 Filtering with score ≥ {min_score}, max results: {max_results or 'unlimited'}...")
    
    filtered_data = filter_tool.filter_affiliations(
        data, 
        min_score=min_score,
        max_results=max_results
    )
    
    # Show results
    print("\n" + "=" * 60)
    print("📋 FILTERING RESULTS")
    print("=" * 60)
    
    filtered_count = len(filtered_data['relevant_affiliation_clusters'])
    print(f"📊 Reduced from {total_clusters} to {filtered_count} clusters ({filtered_count/total_clusters*100:.1f}%)")
    
    # Show top matches
    filter_tool.print_top_matches(filtered_data, top_n=min(10, filtered_count))
    
    # Save results
    output_file = '/home/santi/Projects/UBMI-IFC-Podcast/data/processed/filtered_affiliations.json'
    
    save_choice = input(f"\n💾 Save results to {output_file}? (y/n): ").strip().lower()
    
    if save_choice == 'y':
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Results saved to {output_file}")
        
        # Also create a simple list for easy copying
        simple_output = '/home/santi/Projects/UBMI-IFC-Podcast/data/processed/relevant_affiliations_simple.txt'
        with open(simple_output, 'w', encoding='utf-8') as f:
            f.write("RELEVANT AFFILIATION CLUSTERS\n")
            f.write("=" * 50 + "\n\n")
            
            for i, cluster in enumerate(filtered_data['relevant_affiliation_clusters'], 1):
                f.write(f"{i}. {cluster['representative']}\n")
                f.write(f"   Score: {cluster['relevance_score']:.2f}\n")
                f.write(f"   Variations: {len(cluster['variations'])}\n")
                f.write(f"   Sample variations:\n")
                
                for var in cluster['variations'][:5]:  # Show first 5 variations
                    f.write(f"     - {var}\n")
                
                if len(cluster['variations']) > 5:
                    f.write(f"     ... and {len(cluster['variations']) - 5} more\n")
                
                f.write("\n")
        
        print(f"📄 Simple text summary saved to {simple_output}")
    
    print("\n🎉 Filtering complete!")
    
    return filtered_data


def quick_filter(min_score=5.0, max_results=50):
    """Quick filter with default parameters."""
    
    input_file = '/home/santi/Projects/UBMI-IFC-Podcast/data/processed/all_affiliations.json'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    filter_tool = AffiliationFilter()
    filtered_data = filter_tool.filter_affiliations(data, min_score, max_results)
    
    output_file = '/home/santi/Projects/UBMI-IFC-Podcast/data/processed/filtered_affiliations.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=2)
    
    return filtered_data


def show_usage():
    """Show usage instructions."""
    print("""
🔍 AFFILIATION FILTER USAGE

This tool helps you automatically identify relevant affiliation clusters 
from your large dataset instead of manually reviewing all 357 clusters.

QUICK START:
  python filter_affiliations.py

EXAMPLES:

1. Conservative filtering (high relevance only):
   python filter_affiliations.py --score 10.0 --limit 20

2. Liberal filtering (include more possibilities):
   python filter_affiliations.py --score 2.0 --limit 100

3. Custom filtering:
   python filter_affiliations.py --score 7.5 --limit 30

The filter uses multiple criteria:
- Pattern matching for "Instituto de Fisiología Celular", "Institute of Cellular Physiology"
- Keyword matching for UNAM, cellular physiology, related departments
- Text similarity to known good examples
- Negative filtering to remove obviously unrelated institutions

OUTPUT FILES:
- filtered_affiliations.json: Full filtered data with scores and reasons
- relevant_affiliations_simple.txt: Easy-to-read summary

INTEGRATION:
You can then use the filtered results in your search workflow instead of 
the full 357 clusters, making it much more manageable!
""")


def main():
    """Main function."""
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            show_usage()
            return
        
        # Parse command line arguments
        min_score = 5.0
        max_results = 50
        
        try:
            if '--score' in sys.argv:
                idx = sys.argv.index('--score')
                min_score = float(sys.argv[idx + 1])
            
            if '--limit' in sys.argv:
                idx = sys.argv.index('--limit')
                max_results = int(sys.argv[idx + 1])
            
            print(f"🔄 Quick filtering with score ≥ {min_score}, limit: {max_results}")
            filtered_data = quick_filter(min_score, max_results)
            
            print(f"✅ Found {len(filtered_data['relevant_affiliation_clusters'])} relevant clusters")
            print("📁 Results saved to data/processed/filtered_affiliations.json")
            
        except (IndexError, ValueError) as e:
            print(f"❌ Error parsing arguments: {e}")
            show_usage()
    else:
        # Interactive mode
        interactive_filter()


if __name__ == "__main__":
    main()