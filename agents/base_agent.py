import logging
from database.models import SessionLocal
from database.crud import update_paper_status, PaperStatus

logger = logging.getLogger(__name__)

class BaseAgent:
    """Base class for all agents to provide common functionalities."""
    def __init__(self):
        # You might initialize common resources here, though for Celery tasks
        # direct use of SessionLocal or LLMService instances might be simpler.
        pass

    def _update_paper_status(self, paper_id: int, status: PaperStatus):
        """Helper to update a paper's status in the database."""
        try:
            with SessionLocal() as db:
                update_paper_status(db, paper_id, status)
                logger.info(f"Paper {paper_id} status updated to {status.value}")
        except Exception as e:
            logger.error(f"Failed to update status for paper {paper_id} to {status.value}: {e}")