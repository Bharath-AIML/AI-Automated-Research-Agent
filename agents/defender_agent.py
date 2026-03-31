# =============================================================================
# agents/defender_agent.py — Defender Agent
# =============================================================================
# PURPOSE: Acts like a research paper "supporter" in the debate.
# ROLE   : Reads classified sentences and generates arguments FOR the paper —
#          highlighting its originality, sound methods, and strong results.
# VIVA TIP: The Defender agent simulates a peer reviewer who thinks the paper
#           is good and lists reasons to accept it.

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class DefenderAgent:
    """
    Generates positive arguments (strengths) about a research paper.

    It picks the best Claim, Method, and Result sentences and wraps them
    in structured supporting statements.
    """

    def __init__(self):
        self.name = "Defender Agent"

    # ── Public API ────────────────────────────────────────────────────────────

    def defend(self, paper: dict, classified: list[dict]) -> dict:
        """
        Generates a defence response for a paper.

        Args:
            paper:      Full paper dict (title, abstract, etc.)
            classified: List of classified sentence dicts from the NLP module

        Returns:
            {
                'agent'         : 'Defender',
                'paper_title'   : str,
                'arguments'     : list of strength strings,
                'key_sentences' : {'Claims': [...], 'Methods': [...], 'Results': [...]},
                'overall_stance': str,
            }
        """
        print(f"[{self.name}] Analysing strengths of: '{paper['title'][:60]}…'")

        claims      = self._top_sentences(classified, "Claim",  config.DEFENDER_TOP_N)
        methods     = self._top_sentences(classified, "Method", config.DEFENDER_TOP_N)
        results     = self._top_sentences(classified, "Result", config.DEFENDER_TOP_N)

        arguments = []
        arguments.extend(self._argue_claims(claims))
        arguments.extend(self._argue_methods(methods))
        arguments.extend(self._argue_results(results))

        if not arguments:
            arguments = ["The paper presents a structured contribution to its field."]

        stance = self._overall_stance(len(claims), len(methods), len(results))

        return {
            "agent":       "Defender",
            "paper_title": paper.get("title", "Unknown"),
            "arguments":   arguments,
            "key_sentences": {
                "Claims":  [c["sentence"] for c in claims],
                "Methods": [m["sentence"] for m in methods],
                "Results": [r["sentence"] for r in results],
            },
            "overall_stance": stance,
        }

    # ── Internal Helpers ──────────────────────────────────────────────────────

    def _top_sentences(
        self, classified: list[dict], label: str, n: int
    ) -> list[dict]:
        """Returns the top-n sentences of a given label, sorted by confidence."""
        matching = [r for r in classified if r["label"] == label]
        matching.sort(key=lambda x: x["confidence"], reverse=True)
        return matching[:n]

    def _argue_claims(self, claims: list[dict]) -> list[str]:
        """Wraps claim sentences in supporting argument templates."""
        args = []
        templates = [
            "Original Contribution: {}",
            "Research Novelty: {}",
            "Strong Hypothesis: {}",
        ]
        for i, claim in enumerate(claims):
            tmpl = templates[i % len(templates)]
            args.append(tmpl.format(claim["sentence"]))
        return args

    def _argue_methods(self, methods: list[dict]) -> list[str]:
        """Wraps method sentences in positive argument templates."""
        args = []
        templates = [
            "Sound Methodology: {}",
            "Reproducible Approach: {}",
            "Well-defined Procedure: {}",
        ]
        for i, method in enumerate(methods):
            tmpl = templates[i % len(templates)]
            args.append(tmpl.format(method["sentence"]))
        return args

    def _argue_results(self, results: list[dict]) -> list[str]:
        """Wraps result sentences in positive argument templates."""
        args = []
        templates = [
            "Strong Empirical Evidence: {}",
            "Quantifiable Achievement: {}",
            "Validated Performance: {}",
        ]
        for i, result in enumerate(results):
            tmpl = templates[i % len(templates)]
            args.append(tmpl.format(result["sentence"]))
        return args

    def _overall_stance(
        self, n_claims: int, n_methods: int, n_results: int
    ) -> str:
        """Returns a summarised overall stance sentence."""
        total = n_claims + n_methods + n_results
        if total >= 8:
            return ("This paper demonstrates a strong, well-rounded contribution "
                    "with clear claims, sound methods, and solid empirical results.")
        elif total >= 4:
            return ("This paper makes a reasonable contribution to the field "
                    "with adequate evidence and a clear research direction.")
        else:
            return ("The paper presents an initial contribution. While evidence "
                    "is limited, the direction appears promising.")
