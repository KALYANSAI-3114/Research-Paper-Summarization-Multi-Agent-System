import logging
from typing import List, Optional
from celery import shared_task

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import settings
from database.crud import (
    get_paper_by_id, get_extracted_data_by_paper_id,
    get_topic_by_name, create_topic, add_paper_to_topic,
    update_paper_status
)
from database.models import SessionLocal, PaperStatus
from utils.llm_utils import classification_llm

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def classify_paper_task(self, paper_id: int, topic_list: List[str]) -> Optional[int]:
    """
    Classifies a paper into one or more topics from a user-provided list using an LLM.
    Returns paper_id on success, None on failure.
    """
    if not topic_list:
        logger.warning(f"No topics provided for classification for paper {paper_id}. Skipping.")
        return None

    with SessionLocal() as db:
        paper = get_paper_by_id(db, paper_id)
        if not paper:
            logger.error(f"Paper with ID {paper_id} not found for classification.")
            return None

        extracted_data = get_extracted_data_by_paper_id(db, paper.id)
        if not extracted_data or not extracted_data.full_text_path:
            logger.warning(f"No extracted text found for paper ID {paper_id}. Cannot classify.")
            update_paper_status(db, paper.id, PaperStatus.FAILED)
            return None

        try:
            with open(extracted_data.full_text_path, 'r', encoding='utf-8') as f:
                paper_text = f.read()

            # Use abstract first, fall back to full text if abstract is too short
            text_to_classify = paper.abstract or paper_text[:2000] # Limit full text to avoid token limits

            prompt = (
                f"Given the following research paper abstract/text, classify it into one or more of "
                f"the following topics: {', '.join(topic_list)}.\n"
                "Respond ONLY with the topic names, comma-separated. If no topic fits, respond 'None'.\n\n"
                f"Paper Title: {paper.title}\n"
                f"Paper Abstract/Text:\n{text_to_classify}\n\n"
                "Topics:"
            )

            classification_result = classification_llm.generate_text(prompt, max_tokens=100, temperature=0.0) # Low temperature for classification

            if classification_result and classification_result.lower() != 'none':
                classified_topics = [t.strip() for t in classification_result.split(',') if t.strip()]
                for topic_name in classified_topics:
                    # Ensure topic exists in DB
                    topic = get_topic_by_name(db, topic_name)
                    if not topic:
                        topic = create_topic(db, name=topic_name)
                    # Associate paper with topic
                    add_paper_to_topic(db, paper.id, topic.id)
                update_paper_status(db, paper.id, PaperStatus.CLASSIFIED)
                logger.info(f"Paper {paper.id} classified into topics: {', '.join(classified_topics)}")
            else:
                logger.info(f"Paper {paper.id} could not be classified into any provided topics.")

            return paper.id

        except Exception as e:
            logger.error(f"Error in TopicClassificationAgent for paper ID {paper.id}: {e}")
            update_paper_status(db, paper.id, PaperStatus.FAILED)
            self.retry(exc=e)
            return None