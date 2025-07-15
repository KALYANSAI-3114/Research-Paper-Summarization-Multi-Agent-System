import fitz # PyMuPDF
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from a PDF file using PyMuPDF."""
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        logger.info(f"Successfully extracted text from {pdf_path}")
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
        text = "" # Return empty string on failure
    return text

def extract_metadata_from_pdf(pdf_path: str) -> dict:
    """Extracts basic metadata from a PDF file."""
    metadata = {}
    try:
        with fitz.open(pdf_path) as doc:
            meta = doc.metadata
            metadata['title'] = meta.get('title', 'No Title')
            metadata['author'] = meta.get('author', 'No Author')
            metadata['creation_date'] = meta.get('creationDate', None)
            metadata['mod_date'] = meta.get('modDate', None)
            # Add more fields as needed
        logger.info(f"Successfully extracted metadata from {pdf_path}")
    except Exception as e:
        logger.error(f"Error extracting metadata from PDF {pdf_path}: {e}")
    return metadata

# You could add more advanced functions here for:
# - extract_sections_from_text(text: str) -> dict: Use regex/LLM to identify Introduction, Methods, Results, Conclusion
# - extract_figures_tables(pdf_path: str) -> list: More complex, might involve image processing or advanced PyMuPDF features