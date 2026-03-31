# =============================================================================
# agents/judge_agent.py — Judge Agent
# =============================================================================
# PURPOSE: Acts as the "final arbiter" in the multi-agent debate.
# ROLE   : Reads both the Defender's strengths and the Critic's weaknesses
#          and produces a balanced, scored verdict about the paper.
# VIVA TIP: The Judge is the most important agent — it synthesises both sides
#           and gives an overall recommendation (Accept / Revise / Reject).

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class JudgeAgent:
    """
    Synthesises Defender and Critic perspectives into a final verdict.

    Scoring:
        Each strength   adds  +1  point
        Each weakness   deducts -1 point
        Each limitation deducts -0.5 point
        Score is normalised to 0–10 scale
        Decision:
            8–10  → Accept
            5–7   → Minor Revision
            3–4   → Major Revision
            0–2   → Reject
    """

    VERDICT_THRESHOLDS = {
        "Accept":         8,
        "Minor Revision": 5,
        "Major Revision": 3,
    }

    def __init__(self):
        self.name = "Judge Agent"

    # ── Public API ────────────────────────────────────────────────────────────

    def judge(
        self,
        paper:           dict,
        defence_result:  dict,
        critique_result: dict,
        classified:      list[dict],
    ) -> dict:
        """
        Produces a balanced verdict.

        Args:
            paper:           Original paper dict
            defence_result:  Output from DefenderAgent.defend()
            critique_result: Output from CriticAgent.critique()
            classified:      NLP-classified sentence list

        Returns:
            {
                'agent'         : 'Judge',
                'paper_title'   : str,
                'score'         : float (0–10),
                'verdict'       : str ('Accept' / 'Minor Revision' / ...)
                'summary'       : str (balanced paragraph)
                'strengths'     : list[str]
                'weaknesses'    : list[str]
                'recommendation': str
                'breakdown'     : dict of subscores
            }
        """
        print(f"[{self.name}] Deliberating on: '{paper['title'][:60]}…'")

        # ── Count arguments from each side ────────────────────────────────────
        n_strengths    = len(defence_result.get("arguments", []))
        n_weaknesses   = len(critique_result.get("criticisms", []))
        n_limitations  = len(critique_result.get("key_limitations", []))
        n_missing      = len(critique_result.get("missing_sections", []))

        # ── Compute sub-scores (each out of 10) ───────────────────────────────
        breakdown = self._compute_breakdown(classified)

        # ── Weighted overall score ─────────────────────────────────────────────
        # Positive contribution: strengths (max contribution = 5 pts)
        strength_score = min(n_strengths * 0.8, 5.0)
        # Negative: weaknesses and missing sections
        weakness_penalty   = min(n_weaknesses   * 0.5, 3.0)
        limitation_penalty = min(n_limitations  * 0.3, 1.5)
        missing_penalty    = min(n_missing      * 0.5, 2.0)

        raw_score = (
            breakdown["claim_score"]   * 0.25
            + breakdown["method_score"] * 0.25
            + breakdown["result_score"] * 0.30
            + strength_score
            - weakness_penalty
            - limitation_penalty
            - missing_penalty
        )
        score = round(max(0.0, min(10.0, raw_score)), 2)

        # ── Verdict ─────────────────────────────────────────────────────────
        verdict = self._get_verdict(score)

        # ── Balanced Summary ──────────────────────────────────────────────────
        summary = self._build_summary(
            paper, score, verdict,
            defence_result, critique_result, breakdown
        )

        # ── Recommendation ────────────────────────────────────────────────────
        recommendation = self._build_recommendation(verdict, critique_result)

        return {
            "agent":          "Judge",
            "paper_title":    paper.get("title", "Unknown"),
            "score":          score,
            "verdict":        verdict,
            "summary":        summary,
            "strengths":      defence_result.get("arguments",  [])[:config.JUDGE_TOP_N],
            "weaknesses":     critique_result.get("criticisms",[])[:config.JUDGE_TOP_N],
            "recommendation": recommendation,
            "breakdown":      breakdown,
        }

    # ── Internal Helpers ─────────────────────────────────────────────────────

    def _compute_breakdown(self, classified: list[dict]) -> dict:
        """
        Computes category-level sub-scores based on sentence confidence scores.
        A category score = mean confidence of its sentences × 10.
        """
        def _avg_confidence(label: str) -> float:
            sents = [r for r in classified if r["label"] == label]
            if not sents:
                return 0.0
            return sum(r["confidence"] for r in sents) / len(sents)

        return {
            "claim_score":      round(_avg_confidence("Claim")      * 10, 2),
            "method_score":     round(_avg_confidence("Method")     * 10, 2),
            "result_score":     round(_avg_confidence("Result")     * 10, 2),
            "limitation_score": round(_avg_confidence("Limitation") * 10, 2),
            "total_sentences":  len(classified),
        }

    def _get_verdict(self, score: float) -> str:
        """Maps numeric score to a verdict label."""
        if score >= self.VERDICT_THRESHOLDS["Accept"]:
            return "Accept"
        elif score >= self.VERDICT_THRESHOLDS["Minor Revision"]:
            return "Minor Revision"
        elif score >= self.VERDICT_THRESHOLDS["Major Revision"]:
            return "Major Revision"
        else:
            return "Reject"

    def _build_summary(
        self, paper, score, verdict,
        defence, critique, breakdown
    ) -> str:
        """Generates a human-readable balanced paragraph summary."""
        title    = paper.get("title", "This paper")
        year     = paper.get("year",  "")
        year_str = f" ({year})" if year and year != "Unknown" else ""

        def_stance  = defence.get("overall_stance",  "")
        crit_stance = critique.get("overall_stance", "")

        return (
            f'"{title}"{year_str} has been reviewed by the multi-agent debate system.\n\n'
            f"Defender's View: {def_stance}\n\n"
            f"Critic's View: {crit_stance}\n\n"
            f"Judge's Assessment: The paper scores {score}/10 across "
            f"claim clarity ({breakdown['claim_score']}/10), "
            f"methodology ({breakdown['method_score']}/10), and "
            f"results ({breakdown['result_score']}/10). "
            f"Based on this analysis, the final recommendation is: {verdict}."
        )

    def _build_recommendation(self, verdict: str, critique: dict) -> str:
        """Generates actionable recommendations based on the verdict and missing sections."""
        missing = critique.get("missing_sections", [])

        base_recs = {
            "✅ Accept":          "The paper is ready for publication with minor proofreading.",
            "🔄 Minor Revision":  "Address the identified limitations and clarify methodology.",
            "⚠️  Major Revision": "Substantial revision needed: strengthen evidence, expand discussion.",
            "❌ Reject":          "Paper requires fundamental rethinking of goals and methodology.",
        }
        rec = base_recs.get(verdict, "Further review required.")

        if missing:
            rec += " Specifically, add: " + "; ".join(missing) + "."

        return rec
