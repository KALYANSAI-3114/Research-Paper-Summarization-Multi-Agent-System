import logging
import os
import requests
from celery import shared_task

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import settings
from database.crud import (
    get_paper_by_id, update_paper_status, update_paper_details,
    create_extracted_data, create_citation
)
from database.models import SessionLocal, PaperStatus, ExtractedData
from utils.pdf_parser import extract_text_from_pdf, extract_metadata_from_pdf
from utils.web_scraper import get_html_content, extract_text_from_html, resolve_doi_to_url
from utils.file_utils import save_text_to_file, generate_unique_filename
from utils.citation_manager import extract_and_store_citation # Import the helper

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_paper_task(self, paper_id: int) -> Optional[int]:
    """
    Processes a single paper: downloads if necessary, extracts text, and updates DB.
    Returns the paper_id on success, None on failure.
    """
    with SessionLocal() as db:
        paper = get_paper_by_id(db, paper_id)
        if not paper:
            logger.error(f"Paper with ID {paper_id} not found for processing.")
            return None

        update_paper_status(db, paper.id, PaperStatus.PROCESSING)
        full_text = None
        extracted_metadata = {}
        downloaded_path = None

        try:
            if paper.local_path and os.path.exists(paper.local_path):
                # Process local PDF
                full_text = extract_text_from_pdf(paper.local_path)
                extracted_metadata = extract_metadata_from_pdf(paper.local_path)
                logger.info(f"Processed local PDF: {paper.local_path}")
            elif paper.doi:
                # Resolve DOI and download/scrape
                resolved_url = resolve_doi_to_url(paper.doi)
                if resolved_url:
                    paper.url = resolved_url # Update URL in DB
                    html_content = get_html_content(resolved_url)
                    full_text = extract_text_from_html(html_content)
                    # For DOI, also try to download PDF if possible (more advanced)
                    # This would involve finding PDF links on the page, or using APIs
                    # For simplicity, we'll just extract text from HTML for now.
                    logger.info(f"Processed DOI: {paper.doi} via URL: {resolved_url}")
                else:
                    logger.warning(f"Could not resolve DOI {paper.doi} to a URL.")
            elif paper.url:
                # Scrape URL
                html_content = get_html_content(paper.url)
                full_text = extract_text_from_html(html_content)
                logger.info(f"Processed URL: {paper.url}")
            else:
                logger.warning(f"Paper ID {paper_id} has no local_path, DOI, or URL to process.")
                update_paper_status(db, paper.id, PaperStatus.FAILED)
                return None

            if full_text:
                # Save extracted text to file
                text_filename = generate_unique_filename(f"paper_{paper.id}", "txt", settings.PROCESSED_TEXTS_DIR)
                text_file_path = save_text_to_file(full_text, settings.PROCESSED_TEXTS_DIR, text_filename)

                # Update paper details if new info was extracted (e.g., from PDF metadata)
                update_paper_details(db, paper.id,
                                     title=extracted_metadata.get('title') or paper.title,
                                     authors=extracted_metadata.get('author') or paper.authors,
                                     status=PaperStatus.PROCESSED)

                # Store extracted data
                create_extracted_data(db, paper.id, full_text_path=text_file_path)

                # Create citation entry
                extract_and_store_citation(db, paper.id, {
                    'title': paper.title,
                    'authors': paper.authors,
                    'publication_year': paper.publication_year,
                    'doi': paper.doi,
                    'url': paper.url
                })


                update_paper_status(db, paper.id, PaperStatus.PROCESSED)
                logger.info(f"Paper {paper.id} processed successfully. Text saved to {text_file_path}")
                return paper.id
            else:
                logger.warning(f"No text extracted for paper ID {paper.id}.")
                update_paper_status(db, paper.id, PaperStatus.FAILED)
                return None

        except Exception as e:
            logger.error(f"Error in IngestionProcessingAgent for paper ID {paper.id}: {e}")
            update_paper_status(db, paper.id, PaperStatus.FAILED)
            self.retry(exc=e) # Retry the task on failure
            return None