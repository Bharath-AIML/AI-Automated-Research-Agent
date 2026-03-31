# =============================================================================
# agents/controller.py — Central Controller / Orchestrator
# =============================================================================
# PURPOSE: The "brain" of the system. Coordinates all agents in order.
# FLOW:
#   1. ResearchAgent  → fetch papers
#   2. Preprocessor   → clean + split sentences
#   3. SentenceClassifier → label each sentence
#   4. DefenderAgent  → generate strengths
#   5. CriticAgent    → generate weaknesses
#   6. JudgeAgent     → produce verdict
#   7. Return structured results to the UI
#
# VIVA TIP: The Controller is the "manager" — each agent is a specialist
#           worker. The manager calls them in the right order and collects
#           their outputs.

import time
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from agents.research_agent  import ResearchAgent
from agents.defender_agent  import DefenderAgent
from agents.critic_agent    import CriticAgent
from agents.judge_agent     import JudgeAgent
from nlp.preprocessor       import Preprocessor
from nlp.classifier         import SentenceClassifier


class Controller:
    """
    Orchestrates the full multi-agent research critique pipeline.

    Usage:
        ctrl = Controller()
        results = ctrl.run(query="transformer attention mechanism")
        # results is a list of DebateResult dicts, one per paper
    """

    def __init__(self, classifier_mode: str = "keyword"):
        """
        Args:
            classifier_mode: 'keyword', 'transformer', or 'hybrid'
                             Use 'keyword' for fastest demo (no GPU needed).
        """
        print("[Controller] Initialising agents …")
        self.research_agent  = ResearchAgent()
        self.preprocessor    = Preprocessor()
        self.classifier      = SentenceClassifier(mode=classifier_mode)
        self.defender        = DefenderAgent()
        self.critic          = CriticAgent()
        self.judge           = JudgeAgent()
        print("[Controller] All agents ready ✓")

    # ── Main Pipeline ─────────────────────────────────────────────────────────

    def run(self, query: str, max_papers: int = 5) -> list[dict]:
        """
        Runs the full pipeline for a search query.

        Args:
            query:      User's research topic query
            max_papers: Maximum number of papers to process

        Returns:
            List of debate result dicts (one per paper).
        """
        start_time = time.time()
        print(f"\n{'='*60}")
        print(f"[Controller] Query: '{query}'")
        print(f"{'='*60}")

        # ── Step 1: Fetch Papers ──────────────────────────────────────────────
        papers = self.research_agent.fetch_papers(query)
        if not papers:
            print("[Controller] No papers found. Try a different query.")
            return []

        # Limit to max_papers
        papers = papers[:max_papers]
        print(f"[Controller] Processing {len(papers)} papers …\n")

        all_results = []

        # ── Steps 2–6: Process Each Paper ─────────────────────────────────────
        for idx, paper in enumerate(papers, start=1):
            print(f"\n[Controller] ── Paper {idx}/{len(papers)}: {paper['title'][:70]}")
            result = self._process_paper(paper)
            if result:
                all_results.append(result)

        elapsed = round(time.time() - start_time, 2)
        print(f"\n[Controller] ✅ Pipeline complete in {elapsed}s")
        print(f"[Controller] {len(all_results)} papers analysed.\n")

        # ── Step 7: Save session log ──────────────────────────────────────────
        self._save_log(query, all_results)

        return all_results

    # ── Per-Paper Processing ──────────────────────────────────────────────────

    def _process_paper(self, paper: dict) -> dict | None:
        """
        Runs NLP + all three agents on a single paper.
        Returns a complete DebateResult dict or None if abstract is missing.
        """
        if not paper.get("abstract"):
            print(f"  [!] No abstract — skipping")
            return None

        # Step 2: Preprocess
        paper = self.preprocessor.preprocess_paper(paper)
        sentences = paper.get("sentences", [])
        if not sentences:
            print(f"  [!] No extractable sentences — skipping")
            return None

        # Step 3: Classify sentences
        classified = self.classifier.classify_sentences(sentences)

        # Step 4: Defender
        defence = self.defender.defend(paper, classified)

        # Step 5: Critic
        critique = self.critic.critique(paper, classified)

        # Step 6: Judge
        verdict = self.judge.judge(paper, defence, critique, classified)

        # Assemble final result
        return {
            "paper":      self._paper_meta(paper),
            "classified": classified,
            "defence":    defence,
            "critique":   critique,
            "verdict":    verdict,
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _paper_meta(self, paper: dict) -> dict:
        """Returns a clean metadata dict (without heavy intermediate fields)."""
        return {
            "title":    paper.get("title",    ""),
            "authors":  paper.get("authors",  []),
            "abstract": paper.get("abstract", ""),
            "year":     paper.get("year",     ""),
            "source":   paper.get("source",   ""),
            "url":      paper.get("url",      ""),
        }

    def _save_log(self, query: str, results: list[dict]):
        """Saves the session results to data/session_log.json for later review."""
        try:
            os.makedirs(config.DATA_DIR, exist_ok=True)
            log_path = config.LOG_FILE
            log_entry = {
                "query":      query,
                "timestamp":  time.strftime("%Y-%m-%dT%H:%M:%S"),
                "num_papers": len(results),
                "verdicts":   [
                    {
                        "title":   r["paper"]["title"],
                        "score":   r["verdict"]["score"],
                        "verdict": r["verdict"]["verdict"],
                    }
                    for r in results
                ],
            }

            # Append to existing log
            existing = []
            if os.path.exists(log_path):
                with open(log_path, "r") as f:
                    existing = json.load(f)

            existing.append(log_entry)
            with open(log_path, "w") as f:
                json.dump(existing, f, indent=2)

            print(f"[Controller] Session saved → {log_path}")
        except Exception as e:
            print(f"[Controller] Could not save log: {e}")
