# utils/helpers.py

import re

def clean_text(text: str) -> str:
    """
    Performs basic cleaning on extracted text.
    Removes multiple spaces, newlines, and common OCR artifacts.
    """
    if not isinstance(text, str):
        return ""
    text = re.sub(r'\s+', ' ', text).strip() # Replace multiple whitespaces with single space
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text) # Handle hyphenated words across lines
    # Remove common PDF header/footer repetitions if any
    # (More advanced methods might be needed for specific patterns)
    return text

def format_citation(paper_info: dict) -> str:
    """
    Generates a simple citation string for a paper.
    """
    title = paper_info.get("title", "Unknown Title")
    authors = paper_info.get("authors", ["Unknown Author"])
    source_url = paper_info.get("url") or paper_info.get("pdf_url") or paper_info.get("source", "No Source")
    
    authors_str = ", ".join(authors) if authors else "Unknown Author"
    
    citation = f"**{title}**. {authors_str}. [Source]({source_url})"
    if paper_info.get("doi") and paper_info["doi"] != "N/A":
        citation += f" DOI: [{paper_info['doi']}](https://doi.org/{paper_info['doi']})"
    return citation