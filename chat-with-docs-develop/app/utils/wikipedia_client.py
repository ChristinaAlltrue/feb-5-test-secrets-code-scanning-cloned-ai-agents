# wikipedia_client.py
from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


class WikipediaClient:
    """
    Minimal client for Wikipedia (read-only) using the official APIs.

    - Search: MediaWiki Action API (list=search)
    - Article content & metadata: Action API (prop=extracts/links/categories/coordinates/parse)
    - Summaries (/page/summary)
    """

    ACTION_API = "https://{lang}.wikipedia.org/w/api.php"
    REST_API = "https://{lang}.wikipedia.org/api/rest_v1"

    def __init__(
        self,
        language: str = "en",
        user_agent: str = "WikipediaClient/1.0 (https://www.alltrue.ai)",
        timeout: int = 15,
        max_retries: int = 2,
        retry_backoff: float = 0.8,
    ) -> None:
        self.lang = language
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept": "application/json",
            }
        )

    # ---------------------------
    # Public API
    # ---------------------------

    def search_wikipedia(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search Wikipedia for articles matching a query.

        Returns a list of search results with: title, snippet, pageid, wordcount, size, timestamp, url
        """
        params = {
            "action": "query",
            "format": "json",
            "formatversion": 2,
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "srprop": "snippet|titlesnippet|wordcount|size|timestamp",
            "redirects": 1,
        }
        data = self._action_get(params)
        items = data.get("query", {}).get("search", []) or []
        results = []
        for it in items:
            title = it.get("title", "")
            results.append(
                {
                    "title": title,
                    "snippet": self._strip_html(it.get("snippet", "")),
                    "pageid": it.get("pageid"),
                    "wordcount": it.get("wordcount"),
                    "size": it.get("size"),
                    "timestamp": it.get("timestamp"),
                    "url": self._canonical_url(title),
                }
            )
        return results

    def get_article(self, title: str) -> Dict[str, Any]:
        """
        Get the full content of a Wikipedia article.

        Returns dict with: title, pageid, url, summary, text, sections (metadata),
                           links, categories
        """
        # 1) Extract main plaintext + page info
        extract_data = self._action_get(
            {
                "action": "query",
                "format": "json",
                "formatversion": 2,
                "prop": "extracts|info",
                "explaintext": 1,
                "exsectionformat": "plain",
                "inprop": "url",
                "redirects": 1,
                "titles": title,
            }
        )

        page = self._extract_single_page(extract_data)
        if not page:
            return {"title": title, "exists": False}

        page_title = page.get("title", title)
        pageid = page.get("pageid")
        text = page.get("extract", "") or ""
        url = page.get("fullurl") or self._canonical_url(page_title)

        # 2) Summary via REST API
        summary = self._get_summary_rest(page_title)

        # 3) Sections metadata
        sections_meta = self._get_sections_meta(page_title)

        # 4) Links (article namespace only)
        links = self._get_all_links(page_title)

        # 5) Categories (plain names)
        categories = self._get_all_categories(page_title)

        return {
            "title": page_title,
            "pageid": pageid,
            "url": url,
            "summary": summary or "",
            "text": text,
            "sections": sections_meta,  # metadata only here
            "links": links,
            "categories": categories,
        }

    def get_summary(self, title: str) -> str:
        """
        Get a concise summary of a Wikipedia article (first paragraph style).
        """
        summary = self._get_summary_rest(title)
        if summary:
            return summary

        # Fallback via extracts if REST is unavailable
        data = self._action_get(
            {
                "action": "query",
                "format": "json",
                "formatversion": 2,
                "prop": "extracts",
                "explaintext": 1,
                "exsentences": 3,
                "redirects": 1,
                "titles": title,
            }
        )
        page = self._extract_single_page(data)
        return (page or {}).get("extract", "") or ""

    def get_sections(self, title: str) -> List[Dict[str, Any]]:
        """
        Get the sections of a Wikipedia article with their content.

        Returns: List[{index, number, line, level, content}]
        """
        sections_meta = self._get_sections_meta(title)
        # Fetch each section's content via parse&section=INDEX
        results = []
        for sec in sections_meta:
            idx = sec.get("index")
            if not idx:
                continue
            html = self._parse_section_html(title, idx)
            content = self._html_to_text(html) if html else ""
            sec_with_content = dict(sec)
            sec_with_content["content"] = content.strip()
            results.append(sec_with_content)
        return results

    def get_links(self, title: str) -> List[str]:
        """
        Get links contained within a Wikipedia article (article namespace only).
        """
        return self._get_all_links(title)

    def get_coordinates(self, title: str) -> Dict[str, Any]:
        """
        Get the coordinates of a Wikipedia article.

        Returns:
        {
            title: str,
            pageid: int | None,
            coordinates: List[{lat, lon, ...}],
            exists: bool,
            error: str | None
        }
        """
        try:
            data = self._action_get(
                {
                    "action": "query",
                    "format": "json",
                    "formatversion": 2,
                    "prop": "coordinates",
                    "coprimary": "primary",
                    "colimit": 1,
                    "redirects": 1,
                    "titles": title,
                }
            )
            page = self._extract_single_page(data)
            if not page:
                return {
                    "title": title,
                    "pageid": None,
                    "coordinates": [],
                    "exists": False,
                    "error": "Article not found",
                }

            coords = page.get("coordinates") or []
            return {
                "title": page.get("title", title),
                "pageid": page.get("pageid"),
                "coordinates": [
                    {
                        "lat": c.get("lat"),
                        "lon": c.get("lon"),
                        "primary": c.get("primary"),
                        "globe": c.get("globe"),
                        "dim": c.get("dim"),
                        "type": c.get("type"),
                    }
                    for c in coords
                ],
                "exists": True,
                "error": None,
            }
        except Exception as e:
            return {
                "title": title,
                "pageid": None,
                "coordinates": [],
                "exists": False,
                "error": str(e),
            }

    def summarize_article_for_query(
        self, title: str, query: str, max_length: int = 250
    ) -> Dict[str, str]:
        """
        Build a short extractive summary of an article tailored to a query.
        Heuristic scoring of sentences by keyword overlap.
        """
        article = self.get_article(title)
        text = article.get("text", "") or article.get("summary", "")
        summary = self._focused_summary(text, query, max_length=max_length)
        return {
            "title": article.get("title", title),
            "query": query,
            "summary": summary,
        }

    def summarize_article_section(
        self, title: str, section_title: str, max_length: int = 150
    ) -> Dict[str, str]:
        """
        Get a concise summary of a specific section (by title match, case-insensitive).
        """
        sections = self.get_sections(title)
        best = self._best_section_match(sections, section_title)
        content = best.get("content", "") if best else ""
        if not content:
            return {"title": title, "section_title": section_title, "summary": ""}

        summary = self._focused_summary(content, section_title, max_length=max_length)
        return {"title": title, "section_title": section_title, "summary": summary}

    def extract_key_facts(
        self, title: str, topic_within_article: Optional[str] = None, count: int = 5
    ) -> Dict[str, Any]:
        """
        Extract key facts (heuristic) from an article, optionally focused on a topic.

        Strategy:
          - If topic provided, prefer sentences from the best-matching section.
          - Prefer definitional sentences and those with dates/numbers.
          - Return up to `count` concise facts.
        """
        base = self.get_article(title)
        text_source = base.get("text", "") or base.get("summary", "")

        if topic_within_article:
            sections = self.get_sections(title)
            best = self._best_section_match(sections, topic_within_article)
            if best and best.get("content"):
                text_source = best["content"]

        sentences = self._split_sentences(text_source)
        scored = []
        for s in sentences:
            score = 0
            # Weight definitional pattern and presence of numbers/dates/proper nouns
            if re.search(r"\b(is|are|was|were|refers to|means)\b", s, re.I):
                score += 2
            if re.search(r"\b\d{4}\b", s):  # year-like
                score += 2
            if re.search(r"\d", s):  # any numbers
                score += 1
            if topic_within_article and re.search(
                re.escape(topic_within_article), s, re.I
            ):
                score += 2
            # Prefer shorter, crisper sentences
            score += max(0, 3 - len(s) / 180)  # type: ignore
            scored.append((score, s.strip()))

        scored.sort(key=lambda x: x[0], reverse=True)
        facts = []
        seen = set()
        for _, sent in scored:
            normalized = re.sub(r"\s+", " ", sent)
            if normalized.lower() in seen:
                continue
            if len(normalized) < 20:  # skip fragments
                continue
            facts.append(normalized)
            seen.add(normalized.lower())
            if len(facts) >= count:
                break

        return {
            "title": base.get("title", title),
            "topic": topic_within_article,
            "facts": facts,
        }

    # ---------------------------
    # Internal helpers
    # ---------------------------

    def _action_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """GET wrapper with retries for the MediaWiki Action API."""
        url = self.ACTION_API.format(lang=self.lang)
        return self._get_json_with_retries(url, params=params)

    def _rest_get_json(self, url: str) -> Dict[str, Any]:
        """GET wrapper with retries for the REST API."""
        return self._get_json_with_retries(url)

    def _get_json_with_retries(
        self, url: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                last_exc = e
                if attempt >= self.max_retries:
                    raise
                time.sleep(self.retry_backoff * (attempt + 1))
        # Should never hit here
        raise last_exc or RuntimeError("Unknown request error")

    @staticmethod
    def _strip_html(html: str) -> str:
        return BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True)

    @staticmethod
    def _html_to_text(html: str) -> str:
        soup = BeautifulSoup(html or "", "html.parser")
        # Remove tables/infoboxes to keep text concise
        for tag in soup(["table", "style", "script"]):
            tag.decompose()
        return soup.get_text("\n", strip=True)

    def _canonical_url(self, title: str) -> str:
        return (
            f"https://{self.lang}.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"
        )

    @staticmethod
    def _extract_single_page(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pages = (data or {}).get("query", {}).get("pages", [])
        if not pages:
            return None
        page = pages[0]
        if page.get("missing"):
            return None
        return page

    def _get_summary_rest(self, title: str) -> Optional[str]:
        url = f"{self.REST_API.format(lang=self.lang)}/page/summary/{quote(title)}"
        try:
            data = self._rest_get_json(url)
            return (data or {}).get("extract")
        except Exception:
            return None

    def _get_sections_meta(self, title: str) -> List[Dict[str, Any]]:
        """
        Return sections metadata (no content).
        Elements: {index, number, line, level}
        """
        data = self._action_get(
            {
                "action": "parse",
                "format": "json",
                "formatversion": 2,
                "page": title,
                "prop": "sections",
                "redirects": 1,
            }
        )
        sections = (data or {}).get("parse", {}).get("sections", []) or []
        # Normalize keys
        result = []
        for s in sections:
            result.append(
                {
                    "index": s.get("index"),
                    "number": s.get("number"),
                    "line": s.get("line"),
                    "level": int(s.get("level", "2")),
                }
            )
        return result

    def _parse_section_html(self, title: str, section_index: str) -> str:
        """
        Get HTML for a specific section.
        """
        data = self._action_get(
            {
                "action": "parse",
                "format": "json",
                "formatversion": 2,
                "page": title,
                "prop": "text",
                "section": section_index,
                "redirects": 1,
            }
        )
        return (data or {}).get("parse", {}).get("text", "") or ""

    # -- links & categories with continuation --

    def _get_all_links(
        self, title: str, namespace: int = 0, max_items: int = 2000
    ) -> List[str]:
        """
        Collect links (to other article titles) with continuation, up to max_items.
        """
        params = {
            "action": "query",
            "format": "json",
            "formatversion": 2,
            "prop": "links",
            "plnamespace": namespace,
            "pllimit": "max",
            "redirects": 1,
            "titles": title,
        }
        links: List[str] = []
        cont: Dict[str, Any] = {}
        while True:
            merged = dict(params)
            merged.update(cont)
            data = self._action_get(merged)
            page = self._extract_single_page(data)
            if not page:
                break
            for l in page.get("links", []) or []:
                lt = l.get("title")
                if lt and lt not in links:
                    links.append(lt)
            if "continue" not in data or len(links) >= max_items:
                break
            cont = data["continue"]
        return links[:max_items]

    def _get_all_categories(self, title: str, max_items: int = 500) -> List[str]:
        """
        Collect categories (plain names, no 'Category:' prefix) with continuation.
        """
        params = {
            "action": "query",
            "format": "json",
            "formatversion": 2,
            "prop": "categories",
            "clshow": "!hidden",
            "cllimit": "max",
            "redirects": 1,
            "titles": title,
        }
        cats: List[str] = []
        cont: Dict[str, Any] = {}
        while True:
            merged = dict(params)
            merged.update(cont)
            data = self._action_get(merged)
            page = self._extract_single_page(data)
            if not page:
                break
            for c in page.get("categories", []) or []:
                name = c.get("title", "")
                # Strip "Category:" prefix if present
                if name.startswith("Category:"):
                    name = name[len("Category:") :]
                if name and name not in cats:
                    cats.append(name)
            if "continue" not in data or len(cats) >= max_items:
                break
            cont = data["continue"]
        return cats[:max_items]

    # -- simple text processing for summaries/facts --

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        # Simple sentence splitter (avoid heavy NLP deps)
        text = re.sub(r"\s+", " ", text or "").strip()
        if not text:
            return []
        # Split on '.', '?', '!' while preserving abbreviations somewhat crudely
        parts = re.split(r"(?<=[^.A-Z0-9][.?!])\s+(?=[A-Z(])", text)
        # Fallback if split produced nothing reasonable
        return [p.strip() for p in parts if p and len(p.strip()) > 0]

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"[A-Za-z0-9']+", (text or "").lower())

    def _focused_summary(self, text: str, query: str, max_length: int = 250) -> str:
        if not text:
            return ""
        q_tokens = [t for t in self._tokenize(query) if len(t) > 2]
        q_set = set(q_tokens)
        sents = self._split_sentences(text)
        if not sents:
            return ""

        scored: List[Tuple[float, str]] = []
        for s in sents:
            stoks = self._tokenize(s)
            overlap = len(q_set.intersection(stoks))
            # Extra weight if sentence starts the article/section
            anchor = 1.0 if s == sents[0] else 0.0
            # Length regularization (prefer medium sentences)
            length_penalty = abs(len(s) - 140) / 140.0
            score = overlap + anchor + (0.3 - min(0.3, length_penalty * 0.3))
            scored.append((score, s))

        scored.sort(key=lambda x: x[0], reverse=True)
        picked: List[str] = []
        total_len = 0
        for _, s in scored:
            if s in picked:
                continue
            if total_len + len(s) > max_length and picked:
                continue
            picked.append(s)
            total_len += len(s)
            if total_len >= max_length:
                break

        if not picked:  # fallback to the first sentence(s)
            picked = []
            total_len = 0
            for s in sents:
                if total_len + len(s) > max_length and picked:
                    break
                picked.append(s)
                total_len += len(s)

        summary = " ".join(picked).strip()
        return summary

    @staticmethod
    def _best_section_match(
        sections: List[Dict[str, Any]], query_title: str
    ) -> Optional[Dict[str, Any]]:
        q = (query_title or "").strip().lower()
        if not q or not sections:
            return None
        # Exact match first
        for s in sections:
            if s.get("line", "").strip().lower() == q:
                return s
        # Otherwise case-insensitive contains, then prefix
        contains = [s for s in sections if q in (s.get("line", "").lower())]
        if contains:
            return contains[0]
        starts = [s for s in sections if (s.get("line", "").lower()).startswith(q)]
        return starts[0] if starts else (sections[0] if sections else None)


# example usage
if __name__ == "__main__":
    wiki = WikipediaClient(language="en", user_agent="AllTrue-Example/0.1")

    print("== search_wikipedia('Alan Turing') ==")
    for r in wiki.search_wikipedia("Alan Turing", limit=3):
        print("-", r["title"], "->", r["url"])

    print("\n== get_article('Alan Turing') ==")
    art = wiki.get_article("Alan Turing")
    print("Title:", art["title"])
    print("Summary:", art["summary"][:200], "...")
    print("#sections:", len(art["sections"]))
    print("#links:", len(art["links"]))
    print("#categories:", len(art["categories"]))

    print("\n== get_summary('Alan Turing') ==")
    print(wiki.get_summary("Alan Turing"))

    print("\n== get_sections('Alan Turing') (first 2) ==")
    secs = wiki.get_sections("Alan Turing")
    for s in secs[:2]:
        print(f"- {s['number']} {s['line']} -> {len(s['content'])} chars")

    print("\n== get_links('Alan Turing') (first 10) ==")
    print(wiki.get_links("Alan Turing")[:10])

    print("\n== get_coordinates('Eiffel Tower') ==")
    print(wiki.get_coordinates("Eiffel Tower"))

    print(
        "\n== summarize_article_for_query('Alan Turing', 'codebreaking Enigma war') =="
    )
    print(
        wiki.summarize_article_for_query(
            "Alan Turing", "codebreaking Enigma war", max_length=300
        )
    )

    print("\n== summarize_article_section('Alan Turing', 'Early life') ==")
    print(wiki.summarize_article_section("Alan Turing", "Early life", max_length=200))

    print("\n== extract_key_facts('Eiffel Tower') ==")
    print(wiki.extract_key_facts("Eiffel Tower", count=5))
