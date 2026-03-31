# =============================================================================
# agents/research_agent.py — Research Agent
# =============================================================================
# PURPOSE: Fetches research papers from arXiv and Semantic Scholar APIs.
# HOW IT WORKS:
#   1. Accepts a search query string from the controller
#   2. Sends HTTP GET requests to both APIs
#   3. Parses and normalises results into a consistent dictionary format
#   4. Returns a combined list of paper metadata + abstracts

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class ResearchAgent:
    """
    Fetches academic papers from arXiv and Semantic Scholar.

    Each paper is returned as a dictionary with keys:
        title, authors, abstract, year, source, url
    """

    def __init__(self):
        self.name = "Research Agent"

    # ── Public Entry Point ────────────────────────────────────────────────────

    def fetch_papers(self, query: str) -> list[dict]:
        """
        Main method — fetches papers from both APIs and returns combined results.

        Args:
            query: Search query string (e.g. "transformer attention mechanism")

        Returns:
            List of paper dictionaries. Empty list if all requests fail.
        """
        print(f"[{self.name}] Searching for: '{query}'")
        papers = []

        # Fetch from arXiv first (free, no API key needed)
        arxiv_papers = self._fetch_arxiv(query)
        papers.extend(arxiv_papers)
        print(f"[{self.name}] arXiv → {len(arxiv_papers)} papers found")

        # Fetch from Semantic Scholar
        semantic_papers = self._fetch_semantic_scholar(query)
        papers.extend(semantic_papers)
        print(f"[{self.name}] Semantic Scholar → {len(semantic_papers)} papers found")

        # Remove duplicates based on title similarity
        papers = self._deduplicate(papers)
        print(f"[{self.name}] Total unique papers: {len(papers)}")
        return papers

    # ── arXiv Fetcher ─────────────────────────────────────────────────────────

    def _fetch_arxiv(self, query: str) -> list[dict]:
        """
        Queries the arXiv Atom API and parses XML response.
        arXiv is completely free — no API key required.
        """
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": config.MAX_RESULTS_PER_SOURCE,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        try:
            response = requests.get(
                config.ARXIV_BASE_URL,
                params=params,
                timeout=config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return self._parse_arxiv_xml(response.text)

        except requests.exceptions.Timeout:
            print(f"[{self.name}] arXiv request timed out.")
            return []
        except requests.exceptions.RequestException as e:
            print(f"[{self.name}] arXiv error: {e}")
            return []

    def _parse_arxiv_xml(self, xml_text: str) -> list[dict]:
        """Parses the Atom XML returned by arXiv."""
        papers = []
        try:
            root = ET.fromstring(xml_text)
            # arXiv uses the Atom namespace
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            for entry in root.findall("atom:entry", ns):
                title = entry.findtext("atom:title", default="", namespaces=ns).strip()
                abstract = entry.findtext("atom:summary", default="", namespaces=ns).strip()
                url = entry.findtext("atom:id", default="", namespaces=ns).strip()

                # Collect author names
                authors = [
                    a.findtext("atom:name", default="", namespaces=ns)
                    for a in entry.findall("atom:author", ns)
                ]

                # Parse publication year
                published = entry.findtext("atom:published", default="", namespaces=ns)
                year = published[:4] if published else "Unknown"

                if title and abstract:
                    papers.append({
                        "title":    title.replace("\n", " "),
                        "authors":  authors,
                        "abstract": abstract.replace("\n", " "),
                        "year":     year,
                        "source":   "arXiv",
                        "url":      url,
                    })
        except ET.ParseError as e:
            print(f"[{self.name}] XML parse error: {e}")

        return papers

    # ── Semantic Scholar Fetcher ───────────────────────────────────────────────

    def _fetch_semantic_scholar(self, query: str) -> list[dict]:
        """
        Queries the Semantic Scholar Graph API.
        Works without an API key (rate-limited to ~100 requests/5 min).
        """
        params = {
            "query": query,
            "limit": config.MAX_RESULTS_PER_SOURCE,
            "fields": "title,authors,abstract,year,externalIds,openAccessPdf",
        }

        headers = {}
        if config.SEMANTIC_SCHOLAR_API_KEY:
            headers["x-api-key"] = config.SEMANTIC_SCHOLAR_API_KEY

        try:
            response = requests.get(
                config.SEMANTIC_SCHOLAR_BASE_URL,
                params=params,
                headers=headers,
                timeout=config.REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_semantic_scholar_json(data)

        except requests.exceptions.Timeout:
            print(f"[{self.name}] Semantic Scholar request timed out.")
            return []
        except requests.exceptions.RequestException as e:
            print(f"[{self.name}] Semantic Scholar error: {e}")
            return []

    def _parse_semantic_scholar_json(self, data: dict) -> list[dict]:
        """Parses JSON response from Semantic Scholar."""
        papers = []
        for item in data.get("data", []):
            title    = item.get("title") or ""
            abstract = item.get("abstract") or ""
            year     = str(item.get("year") or "Unknown")

            authors = [
                a.get("name", "") for a in item.get("authors", [])
            ]

            # Build a URL from the paper ID if available
            paper_id = item.get("externalIds", {}).get("ArXiv", "")
            url = f"https://arxiv.org/abs/{paper_id}" if paper_id else ""

            if title and abstract:
                papers.append({
                    "title":    title,
                    "authors":  authors,
                    "abstract": abstract,
                    "year":     year,
                    "source":   "Semantic Scholar",
                    "url":      url,
                })
        return papers

    # ── Deduplication ─────────────────────────────────────────────────────────

    def _deduplicate(self, papers: list[dict]) -> list[dict]:
        """
        Removes duplicate papers by comparing lowercased titles.
        Keeps the first occurrence (usually arXiv).
        """
        seen_titles = set()
        unique = []
        for paper in papers:
            key = paper["title"].lower().strip()
            if key not in seen_titles:
                seen_titles.add(key)
                unique.append(paper)
        return unique
