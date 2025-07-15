from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import json

from database.models import Paper, Topic, PaperTopic, Summary, ExtractedData, Citation, PaperStatus, SummaryType
from database.models import SessionLocal # Import SessionLocal for direct use in functions

def get_paper_by_id(db: Session, paper_id: int):
    return db.query(Paper).filter(Paper.id == paper_id).first()

def get_paper_by_doi(db: Session, doi: str):
    return db.query(Paper).filter(Paper.doi == doi).first()

def get_paper_by_url(db: Session, url: str):
    return db.query(Paper).filter(Paper.url == url).first()

def get_all_papers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Paper).offset(skip).limit(limit).all()

def create_paper(
    db: Session,
    title: str,
    abstract: str,
    authors: str,
    status: PaperStatus = PaperStatus.PENDING,
    publication_year: Optional[int] = None,
    doi: Optional[str] = None,
    url: Optional[str] = None,
    local_path: Optional[str] = None
):
    db_paper = Paper(
        title=title,
        abstract=abstract,
        authors=authors,
        publication_year=publication_year,
        doi=doi,
        url=url,
        local_path=local_path,
        status=status
    )
    db.add(db_paper)
    db.commit()
    db.refresh(db_paper)
    return db_paper

def update_paper_status(db: Session, paper_id: int, new_status: PaperStatus):
    db_paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if db_paper:
        db_paper.status = new_status
        db.commit()
        db.refresh(db_paper)
    return db_paper

def update_paper_details(
    db: Session,
    paper_id: int,
    title: Optional[str] = None,
    abstract: Optional[str] = None,
    authors: Optional[str] = None,
    publication_year: Optional[int] = None,
    doi: Optional[str] = None,
    url: Optional[str] = None,
    local_path: Optional[str] = None,
    status: Optional[PaperStatus] = None
):
    db_paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if db_paper:
        if title: db_paper.title = title
        if abstract: db_paper.abstract = abstract
        if authors: db_paper.authors = authors
        if publication_year: db_paper.publication_year = publication_year
        if doi: db_paper.doi = doi
        if url: db_paper.url = url
        if local_path: db_paper.local_path = local_path
        if status: db_paper.status = status
        db.commit()
        db.refresh(db_paper)
    return db_paper

def get_topic_by_id(db: Session, topic_id: int):
    return db.query(Topic).filter(Topic.id == topic_id).first()

def get_topic_by_name(db: Session, name: str):
    return db.query(Topic).filter(func.lower(Topic.name) == func.lower(name)).first()

def get_all_topics(db: Session):
    return db.query(Topic).all()

def create_topic(db: Session, name: str):
    db_topic = Topic(name=name)
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic

def add_paper_to_topic(db: Session, paper_id: int, topic_id: int):
    # Check if association already exists
    existing = db.query(PaperTopic).filter(
        PaperTopic.paper_id == paper_id,
        PaperTopic.topic_id == topic_id
    ).first()
    if not existing:
        db_paper_topic = PaperTopic(paper_id=paper_id, topic_id=topic_id)
        db.add(db_paper_topic)
        db.commit()
    return True

def get_papers_by_topic(db: Session, topic_id: int):
    return db.query(Paper).join(PaperTopic).filter(PaperTopic.topic_id == topic_id).all()


def get_summary_by_id(db: Session, summary_id: int):
    return db.query(Summary).filter(Summary.id == summary_id).first()

def create_summary(
    db: Session,
    summary_type: SummaryType,
    content: str,
    paper_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    audio_path: Optional[str] = None
):
    db_summary = Summary(
        summary_type=summary_type,
        content=content,
        paper_id=paper_id,
        topic_id=topic_id,
        audio_path=audio_path
    )
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)
    return db_summary

def update_summary_audio_path(db: Session, summary_id: int, audio_path: str):
    db_summary = db.query(Summary).filter(Summary.id == summary_id).first()
    if db_summary:
        db_summary.audio_path = audio_path
        db.commit()
        db.refresh(db_summary)
    return db_summary

def create_extracted_data(
    db: Session,
    paper_id: int,
    full_text_path: Optional[str] = None,
    sections_json: Optional[dict] = None, # Pass dict, convert to JSON internally
    keywords_json: Optional[list] = None,
    figures_info_json: Optional[list] = None,
    tables_info_json: Optional[list] = None
):
    db_extracted_data = ExtractedData(
        paper_id=paper_id,
        full_text_path=full_text_path,
        sections_json=json.dumps(sections_json) if sections_json else None,
        keywords_json=json.dumps(keywords_json) if keywords_json else None,
        figures_info_json=json.dumps(figures_info_json) if figures_info_json else None,
        tables_info_json=json.dumps(tables_info_json) if tables_info_json else None
    )
    db.add(db_extracted_data)
    db.commit()
    db.refresh(db_extracted_data)
    return db_extracted_data

def get_extracted_data_by_paper_id(db: Session, paper_id: int):
    return db.query(ExtractedData).filter(ExtractedData.paper_id == paper_id).first()

def create_citation(
    db: Session,
    paper_id: int,
    citation_text: str,
    bibtex_entry: Optional[str] = None,
    doi: Optional[str] = None,
    authors: Optional[str] = None,
    title: Optional[str] = None,
    year: Optional[int] = None,
    journal_conf: Optional[str] = None
):
    db_citation = Citation(
        paper_id=paper_id,
        citation_text=citation_text,
        bibtex_entry=bibtex_entry,
        doi=doi,
        authors=authors,
        title=title,
        year=year,
        journal_conf=journal_conf
    )
    db.add(db_citation)
    db.commit()
    db.refresh(db_citation)
    return db_citation