"""Enhanced affiliation mining using spaCy NLP and custom patterns."""

import re
from collections import Counter, defaultdict
from typing import Set, List, Dict, Optional

try:
    import spacy
    from spacy.matcher import Matcher
    from spacy.tokens import Span
except ImportError:
    print("spaCy not found. Install with: pip install spacy")
    spacy = None

try:
    import langdetect
    from langdetect import detect
except ImportError:
    print("langdetect not found. Install with: pip install langdetect")
    langdetect = None


class EnhancedAffiliationMiner:
    """Advanced affiliation mining using spaCy NLP and custom pattern matching."""
    
    def __init__(self):
        """Initialize with advanced spaCy features."""
        if spacy is None:
            raise ImportError("spaCy is required for affiliation mining. Install with: pip install spacy")
        
        self.nlp_models = {}
        self.matchers = {}
        self.load_nlp_models()
        self.setup_custom_matchers()
        
    def load_nlp_models(self):
        """Load spaCy models with error handling."""
        models_to_load = {
            'en': 'en_core_web_sm',
            'es': 'es_core_news_sm'
        }
        
        for lang, model_name in models_to_load.items():
            try:
                nlp = spacy.load(model_name)
                # Add custom pipeline components
                if not nlp.has_pipe('merge_entities'):
                    nlp.add_pipe('merge_entities')
                
                self.nlp_models[lang] = nlp
                print(f"✅ Loaded {model_name}")
                
                # Setup matcher for this language
                self.matchers[lang] = Matcher(nlp.vocab)
                
            except OSError:
                print(f"❌ {model_name} not found. Install with:")
                print(f"   python -m spacy download {model_name}")
    
    def setup_custom_matchers(self):
        """Setup custom pattern matchers for institutional names."""
        
        # Patterns for Spanish institutions
        if 'es' in self.matchers:
            spanish_patterns = [
                # Instituto de X patterns
                [{"LOWER": "instituto"}, {"LOWER": "de"}, {"IS_TITLE": True, "OP": "+"}],
                
                # Universidad patterns
                [{"LOWER": "universidad"}, {"IS_TITLE": True, "OP": "+"}],
                [{"LOWER": "universidad"}, {"LOWER": "nacional"}, {"LOWER": "autónoma"}, {"LOWER": "de"}, {"LOWER": "méxico"}],
                
                # Departamento patterns
                [{"LOWER": "departamento"}, {"LOWER": "de"}, {"IS_TITLE": True, "OP": "+"}],
                
                # IFC patterns
                [{"TEXT": {"REGEX": r"IFC-?UNAM"}}],
            ]
            
            for i, pattern in enumerate(spanish_patterns):
                self.matchers['es'].add(f"SPANISH_INSTITUTION_{i}", [pattern])
        
        # Patterns for English institutions
        if 'en' in self.matchers:
            english_patterns = [
                # University of X patterns
                [{"LOWER": "university"}, {"LOWER": "of"}, {"IS_TITLE": True, "OP": "+"}],
                
                # Institute of X patterns
                [{"LOWER": "institute"}, {"LOWER": "of"}, {"IS_TITLE": True, "OP": "+"}],
                
                # Department of X patterns
                [{"LOWER": "department"}, {"LOWER": "of"}, {"IS_TITLE": True, "OP": "+"}],
                
                # National Autonomous University of Mexico
                [{"LOWER": "national"}, {"LOWER": "autonomous"}, {"LOWER": "university"}, 
                 {"LOWER": "of"}, {"LOWER": "mexico"}],
            ]
            
            for i, pattern in enumerate(english_patterns):
                self.matchers['en'].add(f"ENGLISH_INSTITUTION_{i}", [pattern])
    
    def detect_language_advanced(self, text: str) -> str:
        """Advanced language detection with keyword fallback."""
        if langdetect is None:
            # Simple keyword-based detection
            spanish_keywords = ['de', 'del', 'la', 'el', 'y', 'universidad', 'instituto']
            english_keywords = ['of', 'the', 'and', 'university', 'institute', 'department']
            
            text_lower = text.lower()
            spanish_count = sum(1 for kw in spanish_keywords if kw in text_lower)
            english_count = sum(1 for kw in english_keywords if kw in text_lower)
            
            return 'es' if spanish_count > english_count else 'en'
        
        try:
            # Use langdetect for primary detection
            detected = detect(text[:1000])  # Use first 1000 chars for speed
            
            # Validate with keyword analysis
            spanish_keywords = ['de', 'del', 'la', 'el', 'y', 'universidad', 'instituto']
            english_keywords = ['of', 'the', 'and', 'university', 'institute', 'department']
            
            text_lower = text.lower()
            spanish_count = sum(1 for kw in spanish_keywords if kw in text_lower)
            english_count = sum(1 for kw in english_keywords if kw in text_lower)
            
            # Override detection if keyword analysis is strong
            if spanish_count > english_count * 1.5:
                return 'es'
            elif english_count > spanish_count * 1.5:
                return 'en'
            else:
                return detected if detected in ['es', 'en'] else 'en'
                
        except:
            return 'en'  # Default to English
    
    def extract_affiliations_advanced_nlp(self, text: str) -> Set[str]:
        """Advanced NER + custom patterns for affiliation extraction."""
        language = self.detect_language_advanced(text)
        
        if language not in self.nlp_models:
            print(f"⚠️ No model available for language: {language}")
            return set()
        
        nlp = self.nlp_models[language]
        matcher = self.matchers[language]
        
        affiliations = set()
        
        # Process text in chunks to handle large documents
        max_length = 1000000
        text_chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        
        for chunk in text_chunks:
            try:
                doc = nlp(chunk)
                
                # Method 1: Standard NER for organizations
                for ent in doc.ents:
                    if ent.label_ == "ORG":
                        org_text = ent.text.strip()
                        if self.is_relevant_affiliation(org_text):
                            affiliations.add(org_text)
                
                # Method 2: Custom pattern matching
                matches = matcher(doc)
                for match_id, start, end in matches:
                    span = doc[start:end]
                    affiliation_text = span.text.strip()
                    if len(affiliation_text) > 5:
                        affiliations.add(affiliation_text)
                
                # Method 3: Context-based extraction
                # Look for sentences containing institutional indicators
                for sent in doc.sents:
                    sent_text = sent.text.strip()
                    if self.contains_institutional_indicators(sent_text, language):
                        # Extract the institutional part
                        extracted = self.extract_institutional_part(sent_text, language)
                        if extracted:
                            affiliations.add(extracted)
                            
            except Exception as e:
                print(f"⚠️ Error processing chunk: {e}")
                continue
        
        return affiliations
    
    def is_relevant_affiliation(self, org_text: str) -> bool:
        """Check if organization text is relevant to our search."""
        relevant_keywords = [
            'instituto', 'institute', 'universidad', 'university',
            'departamento', 'department', 'unam', 'ifc', 'mexico',
            'fisiolog', 'physiolog', 'celular', 'cellular', 'neurobiolog'
        ]
        
        org_lower = org_text.lower()
        return (len(org_text) > 10 and 
                any(keyword in org_lower for keyword in relevant_keywords))
    
    def contains_institutional_indicators(self, text: str, language: str) -> bool:
        """Check if text contains institutional indicators."""
        if language == 'es':
            indicators = [
                'instituto de', 'universidad', 'departamento de', 
                'centro de', 'facultad de', 'unam'
            ]
        else:
            indicators = [
                'institute of', 'university of', 'department of',
                'center of', 'faculty of', 'unam'
            ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in indicators)
    
    def extract_institutional_part(self, sentence: str, language: str) -> Optional[str]:
        """Extract the institutional part from a sentence."""
        # Use regex patterns to extract institutional names
        if language == 'es':
            patterns = [
                r'Instituto\s+de\s+[A-Za-zÁáÉéÍíÓóÚúÑñ\s,]+?(?:,|\.|\s+UNAM)',
                r'Universidad\s+[A-Za-zÁáÉéÍíÓóÚúÑñ\s,]+?(?:,|\.)',
                r'Departamento\s+de\s+[A-Za-zÁáÉéÍíÓóÚúÑñ\s,]+?(?:,|\.)'
            ]
        else:
            patterns = [
                r'Institute\s+of\s+[A-Za-z\s,]+?(?:,|\.|\s+UNAM)',
                r'University\s+of\s+[A-Za-z\s,]+?(?:,|\.)',
                r'Department\s+of\s+[A-Za-z\s,]+?(?:,|\.)'
            ]
        
        for pattern in patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return match.group().strip()
        
        return None