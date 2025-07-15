import logging
import os
from typing import List, Optional
from celery import shared_task

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import settings
from database.crud import (
    get_topic_by_id, get_paper_by_id, get_extracted_data_by_paper_id,
    create_summary, get_all_topics, get_papers_by_topic,
    get_summary_by_id # Needed to fetch individual summaries
)
from database.models import SessionLocal, SummaryType, PaperStatus
from utils.llm_utils import synthesis_llm
from utils.file_utils import save_text_to_file, generate_unique_filename
from utils.citation_manager import get_citations_for_summary

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def generate_cross_paper_synthesis_task(self, topic_id: int, paper_ids: List[int]) -> Optional[int]:
    """
    Generates a cross-paper synthesis for a given topic based on multiple papers.
    Returns the synthesis summary_id on success, None on failure.
    """
    with SessionLocal() as db:
        topic = get_topic_by_id(db, topic_id)
        if not topic:
            logger.error(f"Topic with ID {topic_id} not found for synthesis.")
            return None

        relevant_paper_summaries = []
        for p_id in paper_ids:
            paper = get_paper_by_id(db, p_id)
            if paper and paper.status == PaperStatus.SUMMARIZED: # Ensure paper is summarized
                # Find the individual summary for this paper
                individual_summary = next((s for s in paper.summaries if s.summary_type == SummaryType.INDIVIDUAL_PAPER), None)
                if individual_summary:
                    relevant_paper_summaries.append(f"Paper: {paper.title} (DOI: {paper.doi or 'N/A'})\nSummary: {individual_summary.content}")
                else:
                    logger.warning(f"No individual summary found for paper ID {p_id} in topic {topic.name}.")
            else:
                logger.warning(f"Paper ID {p_id} not summarized or found for topic {topic.name}.")

        if not relevant_paper_summaries:
            logger.warning(f"No individual summaries available for topic '{topic.name}' (ID: {topic_id}). Skipping synthesis.")
            return None

        combined_summaries_text = "\n\n---\n\n".join(relevant_paper_summaries)

        prompt = (
            f"Synthesize the key findings, trends, and common themes from the following research paper summaries "
            f"related to the topic '{topic.name}'. Identify any conflicting findings or research gaps. "
            f"Provide an overview suitable for a short podcast segment (around 300-500 words).\n\n"
            f"Topic: {topic.name}\n\n"
            f"Individual Paper Summaries:\n{combined_summaries_text}\n\n"
            "Cross-Paper Synthesis:"
        )

        try:
            synthesis_content = synthesis_llm.generate_text(prompt, max_tokens=600, temperature=0.7)

            if synthesis_content:
                # Add citations to the end of the synthesis
                citations_text = get_citations_for_summary(db, paper_ids)
                if citations_text:
                    synthesis_content += "\n\n---\n\nReferences:\n" + citations_text

                # Save synthesis to file
                synthesis_filename = generate_unique_filename(f"topic_{topic.name.replace(' ', '_').lower()}_synthesis", "txt", settings.SUMMARIES_DIR)
                synthesis_file_path = save_text_to_file(synthesis_content, settings.SUMMARIES_DIR, synthesis_filename)

                # Store synthesis in DB, linking to topic
                db_synthesis = create_summary(
                    db,
                    summary_type=SummaryType.CROSS_PAPER_SYNTHESIS,
                    content=synthesis_content,
                    topic_id=topic.id,
                    audio_path=None # Audio path will be updated by audio agent
                )
                logger.info(f"Cross-paper synthesis generated for topic '{topic.name}'. Summary ID: {db_synthesis.id}")
                return db_synthesis.id
            else:
                logger.warning(f"Failed to generate synthesis for topic ID {topic_id}.")
                return None

        except Exception as e:
            logger.error(f"Error in CrossPaperSynthesisAgent for topic ID {topic_id}: {e}")
            self.retry(exc=e)
            return None