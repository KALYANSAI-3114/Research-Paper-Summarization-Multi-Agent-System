import logging
import requests
from typing import List, Dict, Optional
from celery import shared_task

# Add project root to sys.path if running agent as standalone
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import settings
from utils.web_scraper import get_paper_details_from_doi_or_url, resolve_doi_to_url # Assuming Semantic Scholar client added

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def search_papers_task(self, keywords: str, year: Optional[str] = None, limit: int = settings.DEFAULT_SEARCH_LIMIT) -> List[Dict]:
    """
    Searches for research papers using academic APIs (e.g., Semantic Scholar, arXiv).
    Returns a list of dictionaries with paper metadata.
    """
    papers_found = []
    try:
        # --- Example: Semantic Scholar API (Requires `semanticscholar` library) ---
        from semanticscholar import SemanticScholar
        schol = SemanticScholar(api_key=settings.SEMANTIC_SCHOLAR_API_KEY)

        query = keywords
        if year:
            query += f" year:{year}"

        # Fields to retrieve: title, abstract, authors, year, externalIds (for DOI, URL)
        search_results = schol.search_papers(
            query,
            limit=limit,
            fields=['title', 'abstract', 'authors', 'year', 'externalIds', 'url', 'venue']
        )

        for paper in search_results:
            if paper: # Ensure paper object is not None
                paper_data = {
                    'title': paper.title,
                    'abstract': paper.abstract,
                    'authors': ", ".join([a['name'] for a in paper.authors]) if paper.authors else 'N/A',
                    'publication_year': paper.year,
                    'doi': paper.externalIds.get('DOI') if paper.externalIds else None,
                    'url': paper.url,
                    'source_api': 'Semantic Scholar'
                }
                papers_found.append(paper_data)

        logger.info(f"Search found {len(papers_found)} papers for '{keywords}' from Semantic Scholar.")

        # --- Example: arXiv API (Basic) ---
        # import arxiv
        # search_query = f'ti:"{keywords}" OR abs:"{keywords}"'
        # if year:
        #     # arXiv API doesn't have direct year filter in basic search, needs more complex date filtering or post-filtering
        #     pass
        # client = arxiv.Client()
        # search = arxiv.Search(
        #     query=search_query,
        #     max_results=limit,
        #     sort_by=arxiv.SortCriterion.Relevance,
        #     sort_order=arxiv.SortOrder.Descending
        # )
        # for result in client.results(search):
        #     # You'd convert result to your common paper_data dict format
        #     # Example: result.title, result.authors, result.summary, result.pdf_url, result.doi
        #     pass

    except Exception as e:
        logger.error(f"SearchPapersAgent failed for keywords '{keywords}': {e}")
        self.retry(exc=e) # Celery will retry the task
        return []

    return papers_found