# =============================================================================
# nlp/preprocessor.py — NLP Preprocessor
# =============================================================================
# PURPOSE: Cleans and tokenizes raw text from research paper abstracts.
# STEPS:
#   1. Text cleaning  — removes URLs, special chars, extra whitespace
#   2. Sentence splitting — splits paragraph into individual sentences
#   3. Word tokenization — splits each sentence into word tokens
#   4. Stopword removal  — removes common words ("the", "a", "is" …)
#   5. Lemmatization     — reduces words to their root form (running→run)

import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# ── Optional imports — fallback gracefully ────────────────────────────────────
try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus   import stopwords
    from nltk.stem     import WordNetLemmatizer
    _NLTK_AVAILABLE = True
except ImportError:
    _NLTK_AVAILABLE = False

try:
    import spacy
    _SPACY_AVAILABLE = False   # will be set True if the model loads
    _NLP_MODEL = None
except ImportError:
    _SPACY_AVAILABLE = False
    _NLP_MODEL = None


def _ensure_nltk_data():
    """Downloads required NLTK corpora if not already present."""
    if not _NLTK_AVAILABLE:
        return
    for resource in ["punkt", "punkt_tab", "stopwords", "wordnet", "omw-1.4"]:
        try:
            nltk.data.find(f"tokenizers/{resource}")
        except LookupError:
            try:
                nltk.download(resource, quiet=True)
            except Exception:
                pass


_ensure_nltk_data()


class Preprocessor:
    """
    Cleans and tokenises research-paper text.

    Usage:
        prep = Preprocessor()
        sentences = prep.get_sentences(abstract_text)
        tokens    = prep.tokenize(sentence)
    """

    def __init__(self):
        # Setup NLTK tools
        if _NLTK_AVAILABLE:
            try:
                self._stop_words  = set(stopwords.words("english"))
                self._lemmatizer  = WordNetLemmatizer()
                self._nltk_ready  = True
            except Exception:
                self._nltk_ready = False
        else:
            self._nltk_ready = False

        # Try loading spaCy model (optional, for better segmentation)
        global _SPACY_AVAILABLE, _NLP_MODEL
        if not _SPACY_AVAILABLE and _NLP_MODEL is None:
            try:
                import spacy
                _NLP_MODEL = spacy.load("en_core_web_sm")
                _SPACY_AVAILABLE = True
            except Exception:
                pass  # spaCy not available — fall back to NLTK

    # ── Public API ────────────────────────────────────────────────────────────

    def clean(self, text: str) -> str:
        """
        Cleans raw text:
        - Removes URLs, HTML tags, special characters
        - Collapses multiple spaces/newlines
        - Strips leading/trailing whitespace
        """
        if not text:
            return ""
        text = re.sub(r"http\S+|www\S+",           "", text)   # remove URLs
        text = re.sub(r"<[^>]+>",                  "", text)   # remove HTML tags
        text = re.sub(r"\[.*?\]",                  "", text)   # remove [references]
        text = re.sub(r"[^a-zA-Z0-9\s.,;:!?()'-]","", text)   # keep safe chars
        text = re.sub(r"\s+",                    " ", text)    # collapse whitespace
        return text.strip()

    def get_sentences(self, text: str) -> list[str]:
        """
        Splits cleaned text into individual sentences.
        Returns only sentences that meet the minimum length threshold.
        """
        cleaned = self.clean(text)
        if not cleaned:
            return []

        # Prefer spaCy (better boundary detection), fall back to NLTK, then split on "."
        if _SPACY_AVAILABLE and _NLP_MODEL:
            doc = _NLP_MODEL(cleaned)
            sentences = [sent.text.strip() for sent in doc.sents]
        elif self._nltk_ready:
            sentences = sent_tokenize(cleaned)
        else:
            # Simple fallback: split on period followed by space
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned)]

        # Filter out very short sentences
        return [
            s for s in sentences
            if len(s) >= config.MIN_SENTENCE_LENGTH
        ]

    def tokenize(self, sentence: str) -> list[str]:
        """
        Tokenizes a sentence into individual word tokens.
        Removes stopwords and applies lemmatization.
        Returns lowercase tokens.
        """
        if self._nltk_ready:
            tokens = word_tokenize(sentence.lower())
        else:
            tokens = re.findall(r"\b[a-zA-Z]{2,}\b", sentence.lower())

        # Remove stopwords
        if self._nltk_ready:
            tokens = [t for t in tokens if t not in self._stop_words]

        # Lemmatize — converts "running" → "run", "studies" → "study"
        if self._nltk_ready:
            tokens = [self._lemmatizer.lemmatize(t) for t in tokens]

        # Keep only alphabetic tokens of length >= 2
        tokens = [t for t in tokens if t.isalpha() and len(t) >= 2]
        return tokens

    def preprocess_paper(self, paper: dict) -> dict:
        """
        Convenience method: preprocesses a full paper dict.
        Adds 'sentences' and 'all_tokens' keys to the paper dict.
        """
        abstract  = paper.get("abstract", "")
        sentences = self.get_sentences(abstract)
        all_tokens = []
        for sent in sentences:
            all_tokens.extend(self.tokenize(sent))

        paper["sentences"]   = sentences
        paper["all_tokens"]  = all_tokens
        return paper
