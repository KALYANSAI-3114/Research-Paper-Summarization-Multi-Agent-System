from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base # Import Base from __init__.py

class PaperStatus(enum.Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    PROCESSED = "Processed"
    FAILED = "Failed"
    SUMMARIZED = "Summarized" # After individual summary
    CLASSIFIED = "Classified" # After topic classification

class SummaryType(enum.Enum):
    INDIVIDUAL_PAPER = "Individual Paper Summary"
    CROSS_PAPER_SYNTHESIS = "Cross-Paper Synthesis"

class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    abstract = Column(Text)
    authors = Column(String)
    publication_year = Column(Integer, nullable=True)
    doi = Column(String, unique=True, nullable=True) # Digital Object Identifier
    url = Column(String, nullable=True) # Direct URL to paper
    local_path = Column(String, nullable=True) # Path to locally stored PDF
    status = Column(Enum(PaperStatus), default=PaperStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    topics = relationship("Topic", secondary="paper_topics", back_populates="papers")
    summaries = relationship("Summary", back_populates="paper", cascade="all, delete-orphan")
    extracted_data = relationship("ExtractedData", back_populates="paper", uselist=False, cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="paper", cascade="all, delete-orphan")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    papers = relationship("Paper", secondary="paper_topics", back_populates="topics")
    summaries = relationship("Summary", back_populates="topic", cascade="all, delete-orphan") # For cross-paper summaries

class PaperTopic(Base):
    __tablename__ = "paper_topics"

    paper_id = Column(Integer, ForeignKey("papers.id"), primary_key=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), primary_key=True)


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=True) # Nullable for cross-paper synthesis
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True) # Only for cross-paper synthesis
    summary_type = Column(Enum(SummaryType), nullable=False)
    content = Column(Text, nullable=False)
    audio_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    paper = relationship("Paper", back_populates="summaries")
    topic = relationship("Topic", back_populates="summaries") # Links to the topic for synthesis summaries


class ExtractedData(Base):
    """Stores key extracted information from a paper, beyond just text."""
    __tablename__ = "extracted_data"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), unique=True)
    full_text_path = Column(String, nullable=True) # Path to the cleaned, extracted text file
    sections_json = Column(Text, nullable=True) # JSON representation of extracted sections (e.g., intro, methods, results)
    keywords_json = Column(Text, nullable=True) # JSON list of keywords
    figures_info_json = Column(Text, nullable=True) # JSON list of figure captions/details
    tables_info_json = Column(Text, nullable=True) # JSON list of table captions/details

    paper = relationship("Paper", back_populates="extracted_data")


class Citation(Base):
    """Stores detailed citation information for a paper."""
    __tablename__ = "citations"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"))
    citation_text = Column(Text) # Full formatted citation (e.g., APA, MLA)
    bibtex_entry = Column(Text, nullable=True) # Optional: BibTeX format
    doi = Column(String, nullable=True) # Redundant but useful for quick lookup
    authors = Column(String, nullable=True)
    title = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    journal_conf = Column(String, nullable=True) # Journal or Conference name

    paper = relationship("Paper", back_populates="citations")