import logging
import os
from celery import shared_task

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import settings
from database.crud import get_paper_by_id, get_extracted_data_by_paper_id, create_summary, update_paper_status
from database.models import SessionLocal, PaperStatus, SummaryType
from utils.llm_utils import summary_llm
from utils.file_utils import save_text_to_file, generate_unique_filename

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_individual_summary_task(self, paper_id: int) -> Optional[int]:
    """
    Generates a concise summary for a single research paper.
    Returns the summary_id on success, None on failure.
    """
    with SessionLocal() as db:
        paper = get_paper_by_id(db, paper_id)
        if not paper:
            logger.error(f"Paper with ID {paper_id} not found for summarization.")
            return None

        extracted_data = get_extracted_data_by_paper_id(db, paper.id)
        if not extracted_data or not extracted_data.full_text_path:
            logger.warning(f"No extracted text found for paper ID {paper_id}. Cannot summarize.")
            update_paper_status(db, paper.id, PaperStatus.FAILED)
            return None

        try:
            with open(extracted_data.full_text_path, 'r', encoding='utf-8') as f:
                full_text = f.read()

            # Prioritize abstract, then full text (first N characters)
            text_to_summarize = paper.abstract or full_text[:4000] # Limit to fit in LLM context

            prompt = (
                f"Summarize the following research paper abstract/full text. "
                f"Focus on the main objective, key methods, major findings, and conclusions. "
                f"Keep the summary concise, around 150-200 words.\n\n"
                f"Paper Title: {paper.title}\n"
                f"Paper Content:\n{text_to_summarize}\n\n"
                "Summary:"
            )

            summary_content = summary_llm.generate_text(prompt, max_tokens=250, temperature=0.7)

            if summary_content:
                # Save summary to file
                summary_filename = generate_unique_filename(f"paper_{paper.id}_summary", "txt", settings.SUMMARIES_DIR)
                summary_file_path = save_text_to_file(summary_content, settings.SUMMARIES_DIR, summary_filename)

                # Store summary in DB
                db_summary = create_summary(
                    db,
                    summary_type=SummaryType.INDIVIDUAL_PAPER,
                    content=summary_content,
                    paper_id=paper.id,
                    audio_path=None # Audio path will be updated by audio agent
                )
                update_paper_status(db, paper.id, PaperStatus.SUMMARIZED)
                logger.info(f"Individual summary generated for paper {paper.id}. Summary ID: {db_summary.id}")
                return db_summary.id
            else:
                logger.warning(f"Failed to generate summary for paper ID {paper.id}.")
                update_paper_status(db, paper.id, PaperStatus.FAILED)
                return None

        except Exception as e:
            logger.error(f"Error in SummaryGenerationAgent for paper ID {paper.id}: {e}")
            update_paper_status(db, paper.id, PaperStatus.FAILED)
            self.retry(exc=e)
            return None