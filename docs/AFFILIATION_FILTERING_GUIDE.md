# Automated Affiliation Filtering Solution

## Problem Solved

Instead of manually reviewing **357 affiliation clusters** to find relevant ones for your Instituto de Fisiología Celular (IFC) research, this automated system identifies the most relevant clusters using intelligent scoring algorithms.

## Quick Results

✅ **Reduced from 357 clusters to 50 highly relevant ones** (86% reduction!)

The top matches found include:
1. **Instituto de Fisiología Celular** (Score: 1767.0) - 39 variations
2. **Universidad Nacional Autónoma de México** (Score: 708.0) - 53 variations  
3. **Institute for Cellular Physiology** (Score: 544.0) - 10 variations
4. **Department of Biochemistry and Structural Biology, Institute of Cellular Physiology** (Score: 363.0)
5. **Cellular Physiology** (Score: 96.9) - 5 variations

## How It Works

The filtering system uses multiple intelligent criteria:

### 🎯 **Pattern Matching** (Highest Priority)
- `Instituto de Fisiología Celular` and variations
- `Institute of/for Cellular Physiology` 
- `UNAM` references
- `Fisiología Celular` / `Cellular Physiology`

### 🔍 **Keyword Categories** (Medium Priority)
- **Spanish IFC terms**: "instituto de fisiología celular", "fisiologia celular"
- **English IFC terms**: "institute of cellular physiology", "cellular physiology"
- **University**: "UNAM", "Universidad Nacional Autónoma de México"
- **Related departments**: "molecular genetics", "biochemistry", "neurociencias"
- **Physiology terms**: "physiology", "electrophysiology", "neurophysiology"

### 📊 **Similarity Scoring** (Supporting)
- Text similarity to known good examples
- Bonus for multiple variations (indicates relevance)
- Penalty for very generic names
- Strong negative filtering for obviously unrelated institutions

## Usage Options

### Option 1: Use Pre-Filtered Results
The filtered results are already saved in:
- `data/processed/filtered_affiliations.json` - Complete data with scores
- `data/processed/relevant_affiliations_simple.txt` - Easy-to-read summary

### Option 2: Interactive Filtering
```bash
cd /home/santi/Projects/UBMI-IFC-Podcast
python3 scripts/filter_affiliations.py
```

Choose from:
- **Conservative**: Score ≥ 10.0, top 20 results (highest quality)
- **Moderate**: Score ≥ 5.0, top 50 results (good balance) ← **Recommended**
- **Liberal**: Score ≥ 2.0, top 100 results (includes more possibilities)
- **Custom**: Set your own parameters

### Option 3: Command Line
```bash
# Conservative filtering
python3 scripts/filter_affiliations.py --score 10.0 --limit 20

# Liberal filtering  
python3 scripts/filter_affiliations.py --score 2.0 --limit 100

# Custom parameters
python3 scripts/filter_affiliations.py --score 7.5 --limit 30
```

## Integration with Your Workflow

Instead of manually selecting from 357 clusters, you can now:

1. **Use the filtered list directly** - The 50 relevant clusters cover all major IFC-related affiliations
2. **Customize the filtering** - Adjust thresholds based on your specific needs  
3. **Add to your search workflow** - Use these clusters for PubMed searches, affiliation matching, etc.

## Quality Assurance

The system correctly identified your target examples:

✅ **"Instituto de Fisiología Celular"** - Top result (Score: 1767.0)
- All 39 variations captured, including:
  - "Instituto de Fisiología Celular UNAM"
  - "Instituto de Fisiología Celular-Neurociencias" 
  - "Department of Biochemistry and Structural Biology, Instituto de Fisiología Celular"

✅ **"Institute for Cellular Physiology"** - 3rd result (Score: 544.0)
- All English variations captured including:
  - "Institute of Cellular Physiology at UNAM"
  - "the Institute for Cellular Physiology"

✅ **"Cellular Physiology"** - Found as separate cluster (Score: 96.9)

## Customization

You can easily modify the filtering by editing `src/affiliation_mining/affiliation_filter.py`:

- **Add new keywords** to `self.target_keywords`
- **Add new patterns** to `self.institution_patterns` 
- **Adjust scoring weights** in `score_cluster_relevance()`
- **Add negative keywords** to filter out irrelevant institutions

## Files Created

- `src/affiliation_mining/affiliation_filter.py` - Main filtering algorithm
- `scripts/filter_affiliations.py` - Interactive interface
- `data/processed/filtered_affiliations.json` - Filtered results with scores
- `data/processed/relevant_affiliations_simple.txt` - Human-readable summary

## Next Steps

1. **Review the filtered results** to ensure they meet your needs
2. **Integrate with your publication search workflow** 
3. **Customize filtering parameters** if needed for different projects
4. **Use the relevant clusters** instead of manually reviewing all 357

This solution saves you hours of manual review while ensuring you don't miss any relevant affiliations! 🎉