# 🚀 QUICK START GUIDE - UBMI IFC Podcast Testing

## 📋 Current Project Status
Your project automatically generates science podcasts by:
1. **Scraping** articles from IFC-UNAM 
2. **Embedding** articles to find keywords
3. **Searching** PubMed for related articles
4. **Using LLM** to generate podcast scripts
5. **Converting** text to audio

## 🗺️ Notebooks Overview

| Notebook | Purpose | Status | Next Action |
|----------|---------|--------|-------------|
| **`00_TESTING_ROADMAP.ipynb`** ⭐ | **MAIN TESTING GUIDE** | ✅ Ready | **START HERE** |
| `01_test_ifc_scraper.ipynb` | Test IFC scraping only | Partial | Use for debugging scraper |
| `02_test_pubmed_search.ipynb` | Test PubMed API only | Partial | Use for debugging PubMed |
| `03_guided_workflow.ipynb` | Demo with mock data | ✅ Working | Reference implementation |

## 🎯 **RECOMMENDED TESTING SEQUENCE**

### Phase 1: Foundation Testing (Start Here!)
```
1. Open: 00_TESTING_ROADMAP.ipynb
2. Run: Section 1 (Setup & Configuration)
3. Verify: All components load correctly
```

### Phase 2: Component Testing
```
4. Test: IFC scraper (small dataset)
5. Test: PubMed search (small dataset) 
6. Test: Embeddings generation
7. Test: Vector similarity search
```

### Phase 3: Integration Testing
```
8. Test: Article selection pipeline
9. Test: LLM script generation (dry-run)
10. Test: Audio generation (dry-run)
11. Test: End-to-end workflow
```

## ⚡ IMMEDIATE ACTIONS

1. **Right now**: Open `00_TESTING_ROADMAP.ipynb`
2. **First 10 minutes**: Run Setup section to verify everything works
3. **Next 30 minutes**: Test individual components
4. **Next hour**: Run end-to-end pipeline

## 🔧 Configuration Checklist

Make sure you have:
- ✅ Email set in `config/config.yaml` for PubMed
- ⚠️ OpenAI API key (for LLM - optional for testing)
- ⚠️ ElevenLabs API key (for audio - optional for testing)

## 🆘 If You Get Stuck

1. **Component fails**: Use individual test notebooks (01, 02)
2. **API issues**: Check the "Error Handling" section in roadmap
3. **Need help**: Check the troubleshooting sections in each notebook

## 📊 Expected Results

After running the roadmap, you'll have:
- ✅ Working data collection pipeline
- ✅ Functional similarity search
- ✅ Generated podcast script (sample)
- ✅ Audio file (if API keys configured)
- ✅ Performance metrics and optimization suggestions

---
**🏁 Start with `00_TESTING_ROADMAP.ipynb` - it's your single source of truth!**
