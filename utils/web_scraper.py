import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def get_html_content(url: str) -> str:
    """Fetches HTML content from a given URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        logger.info(f"Successfully fetched HTML from {url}")
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return ""

def extract_text_from_html(html_content: str) -> str:
    """Extracts readable text from HTML content using BeautifulSoup."""
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove script, style, and other non-text elements
        for script in soup(["script", "style", "header", "footer", "nav"]):
            script.decompose()
        text = soup.get_text(separator='\n', strip=True)
        return text
    except Exception as e:
        logger.error(f"Error extracting text from HTML: {e}")
        return ""

def resolve_doi_to_url(doi: str) -> Optional[str]:
    """Resolves a DOI to its primary URL using CrossRef API."""
    if not doi:
        return None
    url = f"https://api.crossref.org/works/{doi}/agency"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data and 'message' in data and 'URL' in data['message']:
            logger.info(f"Resolved DOI {doi} to URL: {data['message']['URL']}")
            return data['message']['URL']
    except requests.exceptions.RequestException as e:
        logger.error(f"Error resolving DOI {doi}: {e}")
    return None

# Consider integrating with Semantic Scholar API or similar for richer URL/DOI processing
# Example: Using Semantic Scholar Python client (install `semanticscholar`)
# from semanticscholar import SemanticScholar
# schol = SemanticScholar()
# def get_paper_details_from_doi_or_url(identifier: str) -> Optional[dict]:
#     try:
#         # Semantic Scholar can resolve DOIs and some URLs
#         paper = schol.get_paper(identifier, fields=['title', 'authors', 'year', 'abstract', 'url', 'externalIds'])
#         if paper:
#             return {
#                 'title': paper.title,
#                 'authors': ", ".join([a['name'] for a in paper.authors]) if paper.authors else 'N/A',
#                 'publication_year': paper.year,
#                 'abstract': paper.abstract,
#                 'url': paper.url,
#                 'doi': paper.externalIds.get('DOI') if paper.externalIds else None
#             }
#     except Exception as e:
#         logger.error(f"Error getting paper details from Semantic Scholar for {identifier}: {e}")
#     return None