import os
import sys
from celery import Celery
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import track
from rich.panel import Panel
from rich.table import Table

# Add project root to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from database.crud import (
    get_paper_by_id, get_papers_by_topic, create_paper,
    create_summary, update_paper_status, get_all_topics, create_topic,
    get_topic_by_name
)
from database.models import Base, engine, SessionLocal
from database.models import PaperStatus, SummaryType # Import enums

# Import Celery tasks from agents
# Note: In a real Celery setup, tasks are typically defined in the agent files
# and imported here for registration with the Celery app.
from agents.search_discovery_agent import search_papers_task
from agents.ingestion_processing_agent import process_paper_task
from agents.topic_classification_agent import classify_paper_task
from agents.summary_generation_agent import generate_individual_summary_task
from agents.cross_paper_synthesis_agent import generate_cross_paper_synthesis_task
from agents.audio_generation_agent import generate_audio_task

# Initialize Rich Console for better CLI output
console = Console()

# --- Celery App Initialization ---
celery_app = Celery(
    'research_summarizer',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'agents.search_discovery_agent',
        'agents.ingestion_processing_agent',
        'agents.topic_classification_agent',
        'agents.summary_generation_agent',
        'agents.cross_paper_synthesis_agent',
        'agents.audio_generation_agent'
    ]
)
# Ensure Celery tasks are visible to the worker
# celery_app.autodiscover_tasks(['agents'], related_name='tasks') # Alternative for automatic discovery

def init_db():
    """Initializes the database schema."""
    Base.metadata.create_all(bind=engine)
    console.print("[green]Database initialized![/green]")

def display_paper_details(paper_id: int):
    with SessionLocal() as db:
        paper = get_paper_by_id(db, paper_id)
        if not paper:
            console.print(f"[red]Paper with ID {paper_id} not found.[/red]")
            return

        console.print(Panel(
            f"[bold blue]Paper Details:[/bold blue]\n\n"
            f"[bold]Title:[/bold] {paper.title}\n"
            f"[bold]Authors:[/bold] {paper.authors}\n"
            f"[bold]Publication Year:[/bold] {paper.publication_year}\n"
            f"[bold]DOI:[/bold] {paper.doi or 'N/A'}\n"
            f"[bold]URL:[/bold] {paper.url or 'N/A'}\n"
            f"[bold]Status:[/bold] {paper.status.value}\n"
            f"[bold]Topics:[/bold] {', '.join([t.name for t in paper.topics]) if paper.topics else 'N/A'}\n"
            f"[bold]Local Path:[/bold] {paper.local_path or 'N/A'}\n"
            f"[bold]Abstract:[/bold] {paper.abstract}\n",
            title=f"Paper: {paper.title}",
            expand=False
        ))

        # Display summaries
        for summary in paper.summaries:
            console.print(Panel(
                f"[bold green]Summary Type:[/bold green] {summary.summary_type.value}\n"
                f"[bold]Content:[/bold] {summary.content}\n"
                f"[bold]Audio File:[/bold] {summary.audio_path or 'N/A'}",
                title=f"Summary for {paper.title}",
                expand=False
            ))

def handle_search_papers():
    """Handles the paper search and processing workflow."""
    keywords = Prompt.ask("[bold cyan]Enter topic keywords[/bold cyan] (e.g., 'large language models in healthcare')")
    year = Prompt.ask("[bold cyan]Enter desired publication year[/bold cyan] (e.g., 2023, leave blank for any)", default="")
    limit = Prompt.ask(f"[bold cyan]Maximum number of papers to search[/bold cyan] (default: {settings.DEFAULT_SEARCH_LIMIT})", default=str(settings.DEFAULT_SEARCH_LIMIT))

    try:
        limit = int(limit)
    except ValueError:
        console.print("[red]Invalid limit. Using default.[/red]")
        limit = settings.DEFAULT_SEARCH_LIMIT

    console.print(f"[green]Searching for papers with keywords: '{keywords}' (Year: {year or 'Any'}, Limit: {limit})...[/green]")

    # Dispatch search task
    search_result = search_papers_task.delay(keywords, year, limit)
    paper_data_list = search_result.get(timeout=60) # Wait for results, with timeout

    if not paper_data_list:
        console.print("[yellow]No papers found or search failed.[/yellow]")
        return

    console.print(f"[green]Found {len(paper_data_list)} papers. Starting processing...[/green]")

    processing_tasks = []
    with SessionLocal() as db:
        for paper_data in track(paper_data_list, description="[bold blue]Queuing papers for processing...[/bold blue]"):
            # Create paper entry in DB with PENDING status
            paper = create_paper(db,
                title=paper_data.get('title'),
                abstract=paper_data.get('abstract'),
                authors=paper_data.get('authors'),
                publication_year=paper_data.get('publication_year'),
                doi=paper_data.get('doi'),
                url=paper_data.get('url'),
                status=PaperStatus.PENDING # Initial status
            )
            # Dispatch processing task for each paper
            processing_tasks.append(process_paper_task.delay(paper.id))

    console.print(f"[green]Processing {len(processing_tasks)} papers asynchronously...[/green]")
    # You'd typically poll for status or wait for callbacks in a real UI
    # For CLI, we can block, or show a progress bar for result retrieval
    processed_paper_ids = []
    for i, task in enumerate(track(processing_tasks, description="[bold blue]Waiting for papers to be processed...[/bold blue]")):
        try:
            result = task.get(timeout=300) # Wait up to 5 minutes per paper for processing
            if result: # Result should be paper_id if successful
                processed_paper_ids.append(result)
                console.print(f"[green]Paper ID {result} processed successfully.[/green]")
        except Exception as e:
            console.print(f"[red]Error processing paper {i+1}: {e}[/red]")
            continue

    if not processed_paper_ids:
        console.print("[yellow]No papers were successfully processed.[/yellow]")
        return

    console.print(f"[green]Successfully processed {len(processed_paper_ids)} papers. Now classifying and summarizing...[/green]")
    classify_and_summarize_papers(processed_paper_ids)


def handle_upload_pdf():
    """Handles PDF file uploads."""
    file_path = Prompt.ask("[bold cyan]Enter the path to the PDF file[/bold cyan]")
    if not os.path.exists(file_path):
        console.print("[red]File not found. Please provide a valid path.[/red]")
        return
    if not file_path.lower().endswith('.pdf'):
        console.print("[red]Only PDF files are supported.[/red]")
        return

    # Simulate saving to raw_papers directory
    file_name = os.path.basename(file_path)
    destination_path = os.path.join(settings.RAW_PAPERS_DIR, file_name)
    import shutil
    shutil.copy(file_path, destination_path)
    console.print(f"[green]PDF copied to {destination_path}[/green]")

    with SessionLocal() as db:
        # Create a new paper entry in the database
        paper = create_paper(db,
                             title=f"Uploaded PDF: {file_name}",
                             local_path=destination_path,
                             status=PaperStatus.PENDING,
                             abstract="Abstract will be extracted after processing.",
                             authors="N/A",
                             publication_year=None
                            )
        console.print(f"[green]Paper entry created with ID: {paper.id}. Starting processing...[/green]")
        process_result = process_paper_task.delay(paper.id)
        try:
            processed_paper_id = process_result.get(timeout=300)
            if processed_paper_id:
                console.print(f"[green]PDF ID {processed_paper_id} processed successfully.[/green]")
                classify_and_summarize_papers([processed_paper_id])
            else:
                console.print("[red]PDF processing failed.[/red]")
        except Exception as e:
            console.print(f"[red]Error processing uploaded PDF: {e}[/red]")


def handle_process_url_doi():
    """Handles processing from URL or DOI."""
    identifier_type = Prompt.ask("[bold cyan]Process by[/bold cyan] [b]U[/b]RL or [b]D[/b]OI?", choices=["U", "D"]).upper()
    identifier = Prompt.ask(f"[bold cyan]Enter the {'URL' if identifier_type == 'U' else 'DOI'}[/bold cyan]")

    with SessionLocal() as db:
        # Check if paper already exists (optional, but good for idempotency)
        existing_paper = None
        if identifier_type == 'D':
            # You'd need a get_paper_by_doi in your crud.py
            pass # For simplicity, we'll always create new for now

        paper = create_paper(db,
                             title=f"External Source: {identifier[:50]}...",
                             url=identifier if identifier_type == 'U' else None,
                             doi=identifier if identifier_type == 'D' else None,
                             status=PaperStatus.PENDING,
                             abstract="Abstract will be extracted after processing.",
                             authors="N/A",
                             publication_year=None
                            )
        console.print(f"[green]Paper entry created with ID: {paper.id}. Starting processing...[/green]")
        process_result = process_paper_task.delay(paper.id)
        try:
            processed_paper_id = process_result.get(timeout=300)
            if processed_paper_id:
                console.print(f"[green]Source ID {processed_paper_id} processed successfully.[/green]")
                classify_and_summarize_papers([processed_paper_id])
            else:
                console.print("[red]Source processing failed.[/red]")
        except Exception as e:
            console.print(f"[red]Error processing URL/DOI: {e}[/red]")


def classify_and_summarize_papers(paper_ids: list[int]):
    """Orchestrates classification, individual summary, and synthesis for given paper IDs."""
    if not paper_ids:
        console.print("[yellow]No papers to classify or summarize.[/yellow]")
        return

    # 1. Get user topics
    console.print("\n[bold magenta]--- Topic Classification ---[/bold magenta]")
    existing_topics = get_all_topics(SessionLocal())
    if existing_topics:
        console.print("[bold]Existing topics:[/bold] " + ", ".join([t.name for t in existing_topics]))
    topic_input = Prompt.ask("[bold cyan]Enter topics for classification (comma-separated)[/bold cyan] or leave blank to skip custom topics")
    user_topics = [t.strip() for t in topic_input.split(',') if t.strip()]

    if not user_topics and not existing_topics:
        console.print("[yellow]No topics provided for classification. Skipping explicit classification.[/yellow]")
    elif user_topics:
        with SessionLocal() as db:
            for topic_name in user_topics:
                # Create topics if they don't exist
                get_or_create_topic = get_topic_by_name(db, topic_name)
                if not get_or_create_topic:
                    create_topic(db, name=topic_name)
    else:
        # If user provides no new topics but existing ones exist, use existing
        user_topics = [t.name for t in existing_topics]


    # 2. Dispatch classification and individual summary tasks
    classification_tasks = []
    summary_tasks = []
    for paper_id in track(paper_ids, description="[bold blue]Queuing for classification and individual summary...[/bold blue]"):
        if user_topics:
            classification_tasks.append(classify_paper_task.delay(paper_id, user_topics))
        summary_tasks.append(generate_individual_summary_task.delay(paper_id))

    console.print("[green]Waiting for classification results...[/green]")
    classified_results = []
    for i, task in enumerate(track(classification_tasks, description="[bold blue]Retrieving classification results...[/bold blue]")):
        try:
            result = task.get(timeout=60)
            if result:
                classified_results.append(result)
        except Exception as e:
            console.print(f"[red]Error during classification for a paper: {e}[/red]")

    console.print("[green]Waiting for individual summary results...[/green]")
    summarized_paper_ids = []
    for i, task in enumerate(track(summary_tasks, description="[bold blue]Retrieving individual summaries...[/bold blue]")):
        try:
            summary_id = task.get(timeout=120)
            if summary_id:
                summarized_paper_ids.append(summary_id)
                console.print(f"[green]Summary generated for paper ID {summary_id}.[/green]")
        except Exception as e:
            console.print(f"[red]Error during individual summarization for a paper: {e}[/red]")

    # 3. Trigger audio generation for individual summaries
    audio_tasks = []
    with SessionLocal() as db:
        for paper_id in summarized_paper_ids:
            # Retrieve the created summary to get its content
            paper = get_paper_by_id(db, paper_id)
            if paper and paper.summaries:
                individual_summary = next((s for s in paper.summaries if s.summary_type == SummaryType.INDIVIDUAL_PAPER), None)
                if individual_summary:
                    audio_tasks.append(generate_audio_task.delay(individual_summary.id, individual_summary.content))

    console.print("[green]Waiting for audio generation for individual summaries...[/green]")
    for i, task in enumerate(track(audio_tasks, description="[bold blue]Retrieving audio results...[/bold blue]")):
        try:
            task.get(timeout=60)
        except Exception as e:
            console.print(f"[red]Error during audio generation for a summary: {e}[/red]")


    # 4. Cross-paper synthesis
    console.print("\n[bold magenta]--- Cross-Paper Synthesis ---[/bold magenta]")
    synthesis_topics = Prompt.ask("[bold cyan]Enter topics for cross-paper synthesis (comma-separated, from classified topics)[/bold cyan] or leave blank to skip")
    synthesis_topics_list = [t.strip() for t in synthesis_topics.split(',') if t.strip()]

    if not synthesis_topics_list:
        console.print("[yellow]No synthesis topics provided. Skipping cross-paper synthesis.[/yellow]")
        return

    synthesis_tasks = []
    with SessionLocal() as db:
        for topic_name in synthesis_topics_list:
            topic = get_topic_by_name(db, topic_name)
            if topic:
                # Get all papers associated with this topic that have been processed
                papers_in_topic = get_papers_by_topic(db, topic.id)
                relevant_paper_ids = [p.id for p in papers_in_topic if p.status == PaperStatus.PROCESSED]
                if relevant_paper_ids:
                    console.print(f"[green]Queuing synthesis for topic '{topic_name}' with {len(relevant_paper_ids)} papers.[/green]")
                    synthesis_tasks.append(generate_cross_paper_synthesis_task.delay(topic.id, relevant_paper_ids))
                else:
                    console.print(f"[yellow]No processed papers found for topic '{topic_name}'. Skipping synthesis.[/yellow]")
            else:
                console.print(f"[red]Topic '{topic_name}' not found in database. Skipping synthesis.[/red]")

    console.print("[green]Waiting for cross-paper synthesis results...[/green]")
    synthesized_summary_ids = []
    for i, task in enumerate(track(synthesis_tasks, description="[bold blue]Retrieving synthesis results...[/bold blue]")):
        try:
            summary_id = task.get(timeout=300)
            if summary_id:
                synthesized_summary_ids.append(summary_id)
                console.print(f"[green]Synthesis generated for topic {summary_id}.[/green]")
        except Exception as e:
            console.print(f"[red]Error during cross-paper synthesis: {e}[/red]")

    # 5. Trigger audio generation for synthesized summaries
    audio_tasks_synthesis = []
    with SessionLocal() as db:
        for summary_id in synthesized_summary_ids:
            # Need a way to get summary by ID and its content
            from database.crud import get_summary_by_id # Import here to avoid circular
            summary = get_summary_by_id(db, summary_id)
            if summary:
                audio_tasks_synthesis.append(generate_audio_task.delay(summary.id, summary.content))

    console.print("[green]Waiting for audio generation for synthesized summaries...[/green]")
    for i, task in enumerate(track(audio_tasks_synthesis, description="[bold blue]Retrieving synthesis audio results...[/bold blue]")):
        try:
            task.get(timeout=60)
        except Exception as e:
            console.print(f"[red]Error during audio generation for synthesis: {e}[/red]")

    console.print("[bold green]Workflow completed![/bold green]")


def view_existing_summaries():
    """Displays existing summaries organized by topic."""
    console.print("\n[bold magenta]--- Existing Summaries ---[/bold magenta]")
    topics = get_all_topics(SessionLocal())
    if not topics:
        console.print("[yellow]No topics found yet.[/yellow]")
        return

    for topic in topics:
        console.print(Panel(f"[bold blue]Topic: {topic.name}[/bold blue]", expand=False))
        papers_in_topic = get_papers_by_topic(SessionLocal(), topic.id)
        if not papers_in_topic:
            console.print("[yellow]No papers for this topic yet.[/yellow]")
            continue

        for paper in papers_in_topic:
            console.print(f"  [bold]Paper:[/bold] {paper.title} ({paper.publication_year})")
            for summary in paper.summaries:
                if summary.summary_type == SummaryType.INDIVIDUAL_PAPER:
                    console.print(f"    [bold green]  Individual Summary:[/bold green] {summary.content[:150]}...")
                    console.print(f"      [bold]Audio:[/bold] {summary.audio_path or 'N/A'}")
            # Display cross-paper synthesis for the topic
        for summary in topic.summaries:
            if summary.summary_type == SummaryType.CROSS_PAPER_SYNTHESIS:
                console.print(f"  [bold yellow]Cross-Paper Synthesis:[/bold yellow] {summary.content[:200]}...")
                console.print(f"    [bold]Audio:[/bold] {summary.audio_path or 'N/A'}")
        console.print("") # New line for separation


def main_menu():
    """Displays the main menu and handles user choices."""
    init_db() # Ensure DB is initialized on startup

    while True:
        console.print(Panel(
            "[bold green]Research Paper Summarizer Multi-Agent System[/bold green]\n\n"
            "1. [b]Search[/b] for papers by topic/keywords\n"
            "2. [b]Upload[/b] a PDF file\n"
            "3. [b]Process[/b] from URL or DOI\n"
            "4. [b]View[/b] existing summaries and podcasts\n"
            "5. [b]Exit[/b]\n",
            title="Main Menu",
            title_align="left",
            expand=False
        ))

        choice = Prompt.ask("[bold]Enter your choice[/bold] (1-5)", choices=["1", "2", "3", "4", "5"])

        if choice == "1":
            handle_search_papers()
        elif choice == "2":
            handle_upload_pdf()
        elif choice == "3":
            handle_process_url_doi()
        elif choice == "4":
            view_existing_summaries()
        elif choice == "5":
            console.print("[bold red]Exiting. Goodbye![/bold red]")
            break

if __name__ == "__main__":
    main_menu()