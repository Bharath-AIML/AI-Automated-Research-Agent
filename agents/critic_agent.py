# =============================================================================
# agents/critic_agent.py — Critic Agent
# =============================================================================
# PURPOSE: Acts like a "sceptical reviewer" in the multi-agent debate.
# ROLE   : Identifies weaknesses, limitations, unsupported claims, missing
#          details, and potential biases in the research paper.
# VIVA TIP: The Critic agent simulates a peer reviewer who finds problems
#           and lists reasons to reject or revise the paper.

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class CriticAgent:
    """
    Generates critical arguments (weaknesses) about a research paper.

    It focuses on limitation sentences, low-confidence claims, and 
    missing or vague method/result descriptions.
    """

    def __init__(self):
        self.name = "Critic Agent"

    # ── Public API ────────────────────────────────────────────────────────────

    def critique(self, paper: dict, classified: list[dict]) -> dict:
        """
        Generates a critique response for a paper.

        Args:
            paper:      Full paper dict (title, abstract, etc.)
            classified: List of classified sentence dicts from the NLP module

        Returns:
            {
                'agent'            : 'Critic',
                'paper_title'      : str,
                'criticisms'       : list of weakness strings,
                'key_limitations'  : list of limitation sentence strings,
                'missing_sections' : list of identified gaps,
                'overall_stance'   : str,
            }
        """
        print(f"[{self.name}] Analysing weaknesses of: '{paper['title'][:60]}…'")

        limitations   = self._top_sentences(classified, "Limitation", config.CRITIC_TOP_N)
        low_conf_claims = self._low_confidence(classified, "Claim")
        vague_methods   = self._low_confidence(classified, "Method")
        missing         = self._identify_missing(classified)

        criticisms = []
        criticisms.extend(self._criticise_limitations(limitations))
        criticisms.extend(self._criticise_weak_claims(low_conf_claims))
        criticisms.extend(self._criticise_vague_methods(vague_methods))
        criticisms.extend(self._criticise_missing(missing))

        if not criticisms:
            criticisms = [
                "❌ The abstract lacks explicit limitations or future work discussion."
            ]

        stance = self._overall_stance(len(limitations), len(missing))

        return {
            "agent":          "Critic",
            "paper_title":    paper.get("title", "Unknown"),
            "criticisms":     criticisms,
            "key_limitations":[lim["sentence"] for lim in limitations],
            "missing_sections": missing,
            "overall_stance": stance,
        }

    # ── Internal Helpers ──────────────────────────────────────────────────────

    def _top_sentences(
        self, classified: list[dict], label: str, n: int
    ) -> list[dict]:
        """Returns top-n sentences of a given label sorted by confidence."""
        matching = [r for r in classified if r["label"] == label]
        matching.sort(key=lambda x: x["confidence"], reverse=True)
        return matching[:n]

    def _low_confidence(
        self, classified: list[dict], label: str, threshold: float = 0.4
    ) -> list[dict]:
        """Returns sentences of given label with confidence below threshold."""
        return [
            r for r in classified
            if r["label"] == label and r["confidence"] < threshold
        ]

    def _identify_missing(self, classified: list[dict]) -> list[str]:
        """
        Identifies which key sections are absent from the abstract.
        Missing sections are a genuine weakness — reviewers expect all four.
        """
        present_labels = {r["label"] for r in classified}
        missing = []
        if "Limitation" not in present_labels:
            missing.append("No limitations or future work mentioned")
        if "Result" not in present_labels:
            missing.append("No quantitative results reported")
        if "Method" not in present_labels:
            missing.append("Methodology not clearly described")
        if "Claim" not in present_labels:
            missing.append("No clear research claim or hypothesis stated")
        return missing

    def _criticise_limitations(self, limitations: list[dict]) -> list[str]:
        templates = [
            "Acknowledged Limitation: {}",
            "Potential Weakness: {}",
            "Unresolved Challenge: {}",
        ]
        return [
            templates[i % len(templates)].format(lim["sentence"])
            for i, lim in enumerate(limitations)
        ]

    def _criticise_weak_claims(self, claims: list[dict]) -> list[str]:
        if not claims:
            return []
        return [
            f"Unsupported / Vague Claim: {c['sentence']}"
            for c in claims[:2]
        ]

    def _criticise_vague_methods(self, methods: list[dict]) -> list[str]:
        if not methods:
            return []
        return [
            f"Insufficiently Described Method: {m['sentence']}"
            for m in methods[:2]
        ]

    def _criticise_missing(self, missing: list[str]) -> list[str]:
        return [f"Missing Section: {m}" for m in missing]

    def _overall_stance(self, n_limitations: int, n_missing: int) -> str:
        total_issues = n_limitations + n_missing
        if total_issues >= 4:
            return ("This paper has significant gaps that require major revision "
                    "before acceptance. Key sections and limitations need addressing.")
        elif total_issues >= 2:
            return ("The paper requires moderate revision. Some weaknesses exist "
                    "but the core contribution is identifiable.")
        else:
            return ("Minor issues noted. The paper is generally sound but would "
                    "benefit from clearer limitation disclosure.")
