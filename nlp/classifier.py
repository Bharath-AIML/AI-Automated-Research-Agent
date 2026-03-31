# =============================================================================
# nlp/classifier.py — Sentence Classifier
# =============================================================================
# PURPOSE: Classifies each sentence from a research abstract into one of:
#   - Claim      : A bold research statement or hypothesis
#   - Method     : How the experiment / system was built or run
#   - Result     : What the system achieved — numbers, outcomes
#   - Limitation : Weaknesses, gaps, future work, constraints
#
# APPROACH: Hybrid — keyword-based scoring (fast, explainable) + optional
#           sentence-transformer semantic similarity (more accurate).
# EVALUATION: sklearn metrics (accuracy, F1) computed on a small labelled set.

import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# ── Keyword banks for each category ──────────────────────────────────────────
# These are the "clues" the rule-based classifier uses.
KEYWORDS = {
    "Claim": [
        "we propose", "we present", "this paper", "this work", "we introduce",
        "novel", "new approach", "state-of-the-art", "outperform", "contribute",
        "our model", "our method", "our framework", "significantly", "demonstrates",
        "show that", "we argue", "hypothesis", "claim",
    ],
    "Method": [
        "we use", "we train", "we apply", "we implement", "using", "based on",
        "algorithm", "architecture", "neural network", "dataset", "trained on",
        "evaluated on", "procedure", "pipeline", "framework", "approach",
        "layers", "encoder", "decoder", "attention", "fine-tun",
        "pre-trained", "experiment", "model", "classifier",
    ],
    "Result": [
        "accuracy", "precision", "recall", "f1", "score", "performance",
        "outperforms", "achieves", "improves", "gain", "better", "best",
        "result", "evaluation", "benchmark", "bleu", "rouge", "auc",
        "error rate", "baseline", "percentage", "reduction", "increase",
        "decrease", "%", "state of the art",
    ],
    "Limitation": [
        "limitation", "drawback", "weakness", "however", "although",
        "future work", "not handle", "fail to", "challenge", "difficulty",
        "despite", "does not", "cannot", "unable", "constraint", "assumption",
        "restricted", "only", "require", "expensive", "lack", "insufficient",
    ],
}

# Optional: sentence-transformers for improved classification
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False


class SentenceClassifier:
    """
    Classifies research sentences into: Claim, Method, Result, Limitation.

    Modes:
        'keyword'     — fast rule-based keyword scoring (default, always works)
        'transformer' — uses sentence-transformers for semantic matching
        'hybrid'      — keyword first, transformer for tie-breaking
    """

    # Representative prototype sentences for each category
    # (used by the transformer-based classifier for semantic comparison)
    PROTOTYPES = {
        "Claim": "We propose a novel approach that outperforms existing methods.",
        "Method": "We train a deep neural network using the standard benchmark dataset.",
        "Result": "Our model achieves 95% accuracy with an F1 score of 0.93.",
        "Limitation": "However, the model fails to handle long sequences and has high memory requirements.",
    }

    def __init__(self, mode: str = "keyword"):
        """
        Args:
            mode: 'keyword', 'transformer', or 'hybrid'
        """
        self.mode   = mode
        self._model = None

        if mode in ("transformer", "hybrid") and _ST_AVAILABLE:
            try:
                print("[Classifier] Loading sentence transformer model …")
                self._model = SentenceTransformer(config.SENTENCE_TRANSFORMER_MODEL)
                # Pre-compute prototype embeddings
                self._proto_embeddings = {
                    cat: self._model.encode(text)
                    for cat, text in self.PROTOTYPES.items()
                }
                print("[Classifier] Model loaded ✓")
            except Exception as e:
                print(f"[Classifier] Transformer unavailable ({e}), using keyword mode.")
                self.mode  = "keyword"
                self._model = None
        elif mode in ("transformer", "hybrid"):
            print("[Classifier] sentence-transformers not installed, using keyword mode.")
            self.mode = "keyword"

    # ── Public API ─────────────────────────────────────────────────────────────

    def classify_sentence(self, sentence: str) -> dict:
        """
        Classifies a single sentence.

        Returns:
            {
                'sentence'  : original text
                'label'     : predicted category (str)
                'confidence': float 0–1
                'scores'    : {category: score} raw scores for all categories
            }
        """
        if self.mode == "transformer" and self._model:
            return self._classify_transformer(sentence)
        elif self.mode == "hybrid" and self._model:
            return self._classify_hybrid(sentence)
        else:
            return self._classify_keyword(sentence)

    def classify_sentences(self, sentences: list[str]) -> list[dict]:
        """Classifies a list of sentences. Returns a list of result dicts."""
        return [self.classify_sentence(s) for s in sentences]

    def get_sentences_by_label(
        self, classified: list[dict], label: str
    ) -> list[dict]:
        """Filters classified results to return only sentences of given label."""
        return [r for r in classified if r["label"] == label]

    # ── Evaluation (sklearn) ──────────────────────────────────────────────────

    def evaluate(self, labelled_sentences: list[tuple[str, str]]) -> dict:
        """
        Evaluates classifier performance on labelled data.

        Args:
            labelled_sentences: list of (sentence, true_label) tuples

        Returns:
            dict with accuracy, precision, recall, f1 for each class
        """
        try:
            from sklearn.metrics import (
                accuracy_score, precision_recall_fscore_support,
                classification_report
            )
        except ImportError:
            return {"error": "scikit-learn not installed"}

        y_true, y_pred = [], []
        for sentence, true_label in labelled_sentences:
            pred = self.classify_sentence(sentence)["label"]
            y_true.append(true_label)
            y_pred.append(pred)

        accuracy = accuracy_score(y_true, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_true, y_pred,
            labels=config.SENTENCE_CATEGORIES,
            average="weighted",
            zero_division=0,
        )
        report = classification_report(
            y_true, y_pred,
            labels=config.SENTENCE_CATEGORIES,
            zero_division=0,
        )
        return {
            "accuracy":  round(accuracy,  4),
            "precision": round(precision, 4),
            "recall":    round(recall,    4),
            "f1":        round(f1,        4),
            "report":    report,
        }

    # ── Internal Classifiers ──────────────────────────────────────────────────

    def _classify_keyword(self, sentence: str) -> dict:
        """
        Rule-based keyword scoring.
        Counts keyword matches for each category and picks the highest.
        """
        text_lower = sentence.lower()
        scores = {}

        for category, keywords in KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[category] = score

        total = sum(scores.values())
        if total == 0:
            # No keywords matched — default to Claim with low confidence
            label      = "Claim"
            confidence = 0.25
        else:
            label      = max(scores, key=scores.get)
            confidence = round(scores[label] / total, 3)

        return {
            "sentence":   sentence,
            "label":      label,
            "confidence": confidence,
            "scores":     scores,
        }

    def _classify_transformer(self, sentence: str) -> dict:
        """
        Semantic similarity to prototype sentences using sentence-transformers.
        Picks the category whose prototype is most similar to the input.
        """
        import numpy as np
        from numpy.linalg import norm

        emb = self._model.encode(sentence)
        similarities = {
            cat: float(
                np.dot(emb, proto) / (norm(emb) * norm(proto) + 1e-8)
            )
            for cat, proto in self._proto_embeddings.items()
        }

        best = max(similarities, key=similarities.get)
        total = sum(similarities.values())
        confidence = round(similarities[best] / total, 3) if total > 0 else 0.25

        return {
            "sentence":   sentence,
            "label":      best,
            "confidence": confidence,
            "scores":     {k: round(v, 4) for k, v in similarities.items()},
        }

    def _classify_hybrid(self, sentence: str) -> dict:
        """
        Keyword classification + transformer tie-breaking.
        If keyword scores are tied, use transformer to decide.
        """
        kw_result = self._classify_keyword(sentence)
        scores = kw_result["scores"]
        top_score = max(scores.values())
        tied = [cat for cat, sc in scores.items() if sc == top_score]

        if len(tied) <= 1:
            return kw_result   # Clear winner — no need for transformer

        # Tie: use transformer
        tr_result = self._classify_transformer(sentence)
        # Boost transformer label if it's in the tied set
        if tr_result["label"] in tied:
            return tr_result
        return kw_result
