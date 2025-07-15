# utils/queue_manager.py
# This file will primarily contain utilities to interact with Celery tasks
# and is less about abstracting the queue itself, but rather helping with task management.

from celery.result import AsyncResult
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def get_task_status(task_id: str) -> str:
    """Get the current status of a Celery task."""
    result = AsyncResult(task_id)
    return result.status

def get_task_result(task_id: str, timeout: int = None) -> Any:
    """Get the result of a Celery task, potentially blocking until ready."""
    result = AsyncResult(task_id)
    try:
        return result.get(timeout=timeout)
    except Exception as e:
        logger.error(f"Error retrieving result for task {task_id}: {e}")
        return None

def collect_task_results(task_results: List[AsyncResult], timeout_per_task: int = 60) -> List[Any]:
    """Collects results from a list of Celery AsyncResult objects."""
    results = []
    for task_result in task_results:
        try:
            result = task_result.get(timeout=timeout_per_task)
            if result is not None:
                results.append(result)
        except Exception as e:
            logger.warning(f"Failed to get result for task {task_result.id}: {e}")
    return results