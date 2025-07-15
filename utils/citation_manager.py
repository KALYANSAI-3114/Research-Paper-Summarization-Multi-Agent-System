from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

def format_citation(paper_details: Dict[str, str], style: str = "APA") -> str:
    """
    Formats a citation string based on provided paper details and style.
    This is a simplified example; real citation formatting is complex.
    """
    title = paper_details.get("title", "Unknown Title")
    authors = paper_details.get("authors", "Unknown Authors")
    year = paper_details.get("publication_year", "N.D.")
    journal = paper_details.get("journal_conf", "")
    doi = paper_details.get("doi", "")
    url = paper_details.get("url", "")

    if style.lower() == "apa":
        # Simplified APA 7th edition
        authors_list = [a.strip() for a in authors.split(',')]
        formatted_authors = ""
        if len(authors_list) == 1:
            formatted_authors = authors_list[0]
        elif len(authors_list) == 2:
            formatted_authors = f"{authors_list[0]} & {authors_list[1]}"
        else: # For more than 2, simplified to first author et al.
            formatted_authors = f"{authors_list[0]} et al."

        citation = f"{formatted_authors} ({year}). {title}. {journal}."
        if doi:
            citation += f" doi:{doi}"
        elif url:
            citation += f" {url}"
        return citation
    elif style.lower() == "mla":
        # Simplified MLA style
        authors_list = [a.strip() for a in authors.split(',')]
        if len(authors_list) > 1:
            formatted_authors = f"{authors_list[0]}, et al."
        else:
            formatted_authors = authors_list[0]

        citation = f"{formatted_authors}. \"{title}.\" {journal}, {year}."
        if doi:
            citation += f" doi:{doi}"
        elif url:
            citation += f" {url}"
        return citation
    else:
        logger.warning(f"Unsupported citation style: {style}. Returning a default format.")
        return f"{authors} ({year}). {title}. {journal}. DOI: {doi if doi else url}"

def extract_and_store_citation(db_session, paper_id: int, paper_data: dict) -> Optional[int]:
    """
    Extracts citation details from paper_data and stores it in the database.
    Returns the citation ID if successful.
    """
    citation_text = format_citation(paper_data, style="APA") # You can choose your default style

    try:
        from database.crud import create_citation # Import here to avoid circular dependency with models/main
        citation = create_citation(
            db=db_session,
            paper_id=paper_id,
            citation_text=citation_text,
            doi=paper_data.get('doi'),
            authors=paper_data.get('authors'),
            title=paper_data.get('title'),
            year=paper_data.get('publication_year')
            # Add other fields as needed
        )
        logger.info(f"Citation created for paper ID {paper_id}")
        return citation.id
    except Exception as e:
        logger.error(f"Failed to create citation for paper ID {paper_id}: {e}")
        return None

def get_citations_for_summary(db_session, paper_ids: List[int]) -> str:
    """
    Retrieves and formats citations for a given list of paper IDs.
    Useful for cross-paper synthesis.
    """
    from database.crud import get_paper_by_id # Import here
    citations_list = []
    for p_id in paper_ids:
        paper = get_paper_by_id(db_session, p_id)
        if paper and paper.citations:
            # Assuming one citation per paper for simplicity
            citations_list.append(paper.citations[0].citation_text)
    return "\n".join(sorted(list(set(citations_list)))) # Sort and remove duplicates