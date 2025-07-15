import os
import logging

logger = logging.getLogger(__name__)

def save_text_to_file(content: str, directory: str, filename: str) -> Optional[str]:
    """Saves text content to a specified file within a directory."""
    try:
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Text saved to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving text to {filename} in {directory}: {e}")
        return None

def generate_unique_filename(base_name: str, extension: str, directory: str) -> str:
    """Generates a unique filename to avoid overwrites."""
    counter = 0
    filename = f"{base_name}.{extension}"
    file_path = os.path.join(directory, filename)
    while os.path.exists(file_path):
        counter += 1
        filename = f"{base_name}_{counter}.{extension}"
        file_path = os.path.join(directory, filename)
    return filename