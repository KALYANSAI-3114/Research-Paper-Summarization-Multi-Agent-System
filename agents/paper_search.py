# agents/paper_search.py

import streamlit as st
import arxiv
from scholarly import scholarly # Be aware this might require a proxy or can be rate-limited
import requests
import time

class PaperSearchAgent:
    def __init__(self):
        self.name = "Paper Search and Discovery Agent"

    @st.cache_data(ttl=3600) # Cache results for 1 hour
    def search_arxiv(_self, query: str, max_results: int = 5) -> list:
        """
        Searches arXiv for research papers.
        """
        st.info(f"Searching arXiv for '{query}'...")
        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
                sort_order=arxiv.SortOrder.Descending
            )
            results = []
            for r in arxiv.Client().results(search):
                results.append({
                    "title": r.title,
                    "authors": [a.name for a in r.authors],
                    "abstract": r.summary,
                    "url": r.entry_id,
                    "pdf_url": r.pdf_url,
                    "doi": r.doi if r.doi else "N/A"
                })
            st.success(f"Found {len(results)} results on arXiv.")
            return results
        except Exception as e:
            st.error(f"Error searching arXiv: {e}")
            return []

    @st.cache_data(ttl=3600) # Cache results for 1 hour
    def search_scholarly(_self, query: str, max_results: int = 5) -> list:
        """
        Searches Google Scholar for research papers using scholarly.
        NOTE: scholarly can be unstable due to rate-limiting/blocking.
        """
        st.info(f"Searching Google Scholar for '{query}' (Experimental)...")
        results = []
        try:
            search_query = scholarly.search_pubs(query)
            for i, pub in enumerate(search_query):
                if i >= max_results:
                    break
                # Fetch more details if available (can be slow)
                # pub = scholarly.fill(pub)
                results.append({
                    "title": pub['bib'].get('title', 'No Title'),
                    "authors": pub['bib'].get('author', ['N/A']),
                    "abstract": pub['bib'].get('abstract', 'No abstract available.'),
                    "url": pub.get('pub_url', 'N/A'),
                    "doi": pub['bib'].get('doi', 'N/A')
                })
                time.sleep(0.5) # Be kind to the server
            st.success(f"Found {len(results)} results on Google Scholar.")
            return results
        except Exception as e:
            st.warning(f"Error searching Google Scholar (might be due to rate limiting/blocking). Please try arXiv or manual input: {e}")
            return []

    def run(self, query: str, source: str, num_results: int) -> list:
        if source == "arXiv":
            return self.search_arxiv(query, num_results)
        elif source == "Google Scholar (Experimental)":
            return self.search_scholarly(query, num_results)
        return []