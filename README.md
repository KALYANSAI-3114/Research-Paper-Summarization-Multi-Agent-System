# 📚 AI-Powered Research Paper Summarizer & Synthesis System 🚀


## Table of Contents

1.  [🌟 Project Overview](#-project-overview)
2.  [💡 Problem Statement](#-problem-statement)
3.  [✨ Key Features](#-key-features)
4.  [🚀 Architecture: The Multi-Agent Approach](#-architecture-the-multi-agent-approach)
    * [Agent Breakdown](#agent-breakdown)
    * [Data Flow & Coordination](#data-flow--coordination)
5.  [🛠️ Technology Stack](#%EF%B8%8F-technology-stack)
6.  [⚙️ Setup & Installation](#%EF%B8%8F-setup--installation)
    * [Prerequisites](#prerequisites)
    * [Local Setup (2 Commands!)](#local-setup-2-commands)
    * [Secrets Management](#secrets-management)
7.  [🎬 Demo](#-demo)
8.  [🔍 Problem-Solving & Design Decisions](#-problem-solving--design-decisions)
    * [Handling Edge Cases & Robustness](#handling-edge-cases--robustness)
    * [UI/UX Philosophy](#uiux-philosophy)
9.  [📈 Limitations & Future Enhancements](#-limitations--future-enhancements)
10. [📞 Contact](#-contact)

---

## 🌟 Project Overview

In today's fast-paced world, staying abreast of the latest research across diverse academic domains is a monumental task. This project presents an innovative, **AI-powered Multi-Agent System** designed to revolutionize how professionals and researchers consume academic literature. It automates the entire lifecycle from discovery to digestible audio insights, transforming tedious manual review into an efficient, interactive experience.

Developed with a strong emphasis on **problem-solving, engineering best practices, and sophisticated LLM integration**, this system prioritizes core functionality while demonstrating thoughtful software design and clear technical communication.

## 💡 Problem Statement

The sheer volume of new research papers makes it incredibly challenging and time-consuming for individuals to stay updated, understand key findings, and identify emerging trends across multiple fields. Manual review is inefficient, leading to missed insights and knowledge gaps.

## ✨ Key Features

This system automates and streamlines the research consumption process through:

* **🔍 Advanced Research Article Search:** Find relevant papers from sources like arXiv and Google Scholar (experimental) with filtering options.
* **📄 Versatile Document Processing:** Ingest research papers from various formats including direct PDF uploads, academic URLs, and DOI references.
* **🧠 Intelligent Topic Classification:** Automatically categorize processed papers into user-defined topics using Large Language Models (LLMs).
* **📝 Concise Summary Generation:** Generate high-quality, individual summaries for each research paper, highlighting objectives, methodologies, and key findings.
* **🤝 Cross-Paper Topic Synthesis:** Synthesize findings from multiple papers belonging to the same topic, providing cohesive, overarching insights – a true knowledge consolidation feature!
* **🎧 Audio Podcast Generation:** Convert both individual and synthesized summaries into accessible audio podcasts, enabling hands-free learning.
* **🔗 Robust Citation System:** Trace all extracted and summarized information directly back to its original source with clear citations.

## 🚀 Architecture: The Multi-Agent Approach

Our system is engineered as a **Multi-Agent System**, where specialized, autonomous "agents" collaborate to perform complex tasks. This modular and distributed design significantly enhances **maintainability, scalability, and clarity of function**, allowing for independent development and robust error handling for each stage of the research processing pipeline.

### Agent Breakdown

Each agent is a focused, intelligent module with a distinct responsibility:

* **🕵️ Paper Search & Discovery Agent:**
    * **Role:** Identifies and fetches metadata for research papers.
    * **Technologies:** `arxiv` (for arXiv API), `scholarly` (for Google Scholar, experimental).
* **⚙️ Paper Processing & Information Extraction Agent:**
    * **Role:** Extracts clean, readable text and key metadata (title, authors, abstract, DOI) from diverse sources.
    * **Technologies:** `PyPDF2` (for PDFs), `requests` & `BeautifulSoup` (for URLs/HTML parsing), Crossref API (for DOI resolution).
* **🧠 Topic Classification Agent:**
    * **Role:** Assigns processed papers to relevant topics based on user-defined categories.
    * **Technologies:** Large Language Models (LLMs) via `OpenRouter.ai` (or Ollama/OpenAI for configurable backend).
* **📝 Summary Generation Agent:**
    * **Role:** Crafts concise, informative summaries for individual papers.
    * **Technologies:** Large Language Models (LLMs) via `OpenRouter.ai`.
* **🤝 Cross-Paper Synthesis Agent:**
    * **Role:** Aggregates and synthesizes insights from multiple summaries within the same topic.
    * **Technologies:** Large Language Models (LLMs) via `OpenRouter.ai`.
* **🔊 Audio Generation Agent:**
    * **Role:** Converts text summaries into natural-sounding audio podcasts.
    * **Technologies:** `gTTS` (Google Text-to-Speech).


## 🛠️ Technology Stack

Our technology choices prioritize Python for its rich ecosystem in AI/NLP, coupled with robust libraries and APIs to ensure efficient and reliable operations.

* **Frontend & Orchestration:** `Streamlit` (Python framework for rapid web app development)
* **Core Logic:** `Python 3.9+`
* **LLM Integration:** `OpenRouter.ai` (Unified API for diverse LLMs, providing flexibility and cost control. Uses `openai` Python client for compatibility.)
    * *Justification:* Chosen for its ability to access multiple models (some free-tier options available) through a single, consistent API, mitigating provider-specific rate limits and offering a flexible path for future model upgrades. This balances performance with cost-effectiveness for demonstration.
* **PDF Processing:** `PyPDF2`
* **Web Content Extraction:** `requests`, `BeautifulSoup4`
* **Academic Search:** `arxiv`, `scholarly`
* **Text-to-Speech:** `gTTS`
* **Environment Management:** `python-dotenv`, `venv`

## ⚙️ Setup & Installation

The application is designed for quick and straightforward setup, enabling anyone to launch it with minimal commands.

### Prerequisites

* **Python 3.9+** installed on your system.
* **Git** installed (for cloning the repository).
* **Tesseract OCR:** Required for extracting text from images within PDFs. Follow the official installation guide: [https://tesseract-ocr.github.io/tessdoc/Installation.html](https://tesseract-ocr.github.io/tessdoc/Installation.html). Ensure it's added to your system's PATH.

### Local Setup (2 Commands!)

Follow these steps to get the application running on your local machine:

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/KALYANSAI-3114/Research-Paper-Summarization-Multi-Agent-System](https://github.com/KALYANSAI-3114/Research-Paper-Summarization-Multi-Agent-System)
    cd Research-Paper-Summarization-Multi-Agent-System
    ```

2.  **Install Dependencies & Run:**
    ```bash
    python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && streamlit run app.py
    ```
    *(On Windows Command Prompt, use: `python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && streamlit run app.py`)*

    This single command performs the following:
    * Creates a Python virtual environment (`venv`).
    * Activates the virtual environment.
    * Installs all required dependencies listed in `requirements.txt`.
    * Launches the Streamlit application.

    Your application should automatically open in your web browser at `http://localhost:8501`.

### Secrets Management

This project uses API keys for LLM services. For security, these are **never committed to the repository.**

1.  **Obtain API Key:**
    * **OpenRouter.ai:** Sign up at [openrouter.ai](https://openrouter.ai) and generate an API Key from your dashboard. (Check their "Models" page for free-tier options, e.g., `mistralai/mistral-7b-instruct-v0.2`).
2.  **Create `.env` file:** In the root directory of your project (where `app.py` is), create a file named `.env`.
3.  **Add your API key:**
    ```
    # .env
    OPENROUTER_API_KEY="sk-or-YOUR_ACTUAL_OPENROUTER_KEY_HERE"
    ```
    *(Replace with your actual key. This file is ignored by Git via `.gitignore`.)*

## 🎬 Demo

<video width="100%" controls autoplay loop muted>
  <source src="assets/demo.webm" type="video/webm">
  Your browser does not support the video tag.
</video>

<p align="center"><em>🎥 Watch a demonstration of the system in action above.</em></p>

---

## 🔍 Problem-Solving & Design Decisions

This project allowed me to tackle several complex challenges and make thoughtful engineering decisions:

* **LLM Integration & Orchestration:** Successfully integrated external LLM APIs (via OpenRouter for flexibility) and orchestrated their specialized roles (summarization, classification, synthesis) within a multi-agent framework. This showcased strong **LLM integration capabilities**.
* **Robust Document Processing:** Implemented sophisticated text extraction from diverse, often messy, sources like PDFs (handling embedded metadata vs. visual text) and varied HTML structures. This was a significant **problem-solving** challenge, moving beyond basic parsing to heuristic-based extraction for metadata like authors and abstracts.
* **Error Handling & User Feedback:** Built robust `try-except` blocks and detailed `st.info`/`st.warning`/`st.error` messages, particularly around LLM calls, API key validation, and file processing, ensuring clear communication with the user even during failures.
* **Multi-Agent Design:** The decision to use a multi-agent system (even as functional modules in Python classes) provided clear separation of concerns, making the codebase modular, testable, and conceptually scalable. This demonstrates strong **software design decisions**.
* **Streamlit as UI/UX:** Prioritized Streamlit for its rapid prototyping capabilities, allowing quick iteration on features and a user-friendly interface for demonstration within the tight **time management** constraints.

### Handling Edge Cases & Robustness

* **Unhashable Parameters:** Addressed Streamlit's caching limitations by correctly handling `self` in cached class methods (`_self`).
* **PDF Metadata vs. Text Extraction:** Implemented logic to extract metadata from PDF internal fields *and* heuristically from the first page's text for greater accuracy.
* **Dynamic Web Content:** Utilized `BeautifulSoup` with advanced regex patterns and class matching to intelligently extract content from diverse web page layouts, falling back gracefully to "N/A" if information is truly absent.
* **LLM Response Consistency:** Implemented post-processing logic for LLM classification outputs (stripping, lowercasing, smart matching) to ensure consistent topic grouping, critical for the synthesis feature.
* **Network Resilience:** Included timeouts and `try-except` blocks for all external API calls (`requests`, LLMs) to handle network issues or service unavailability gracefully.

### UI/UX Philosophy

While prioritizing core functionality (as per assignment guidelines), a significant effort was made to enhance the **visual polish** and **user experience**:

* **Clean & Modern Aesthetic:** Utilized custom CSS (`style.css`) and Streamlit's theme configuration (`.streamlit/config.toml`) to implement a fresh color palette, improved typography, and consistent spacing.
* **Intuitive Workflow:** Structured the application into clear, numbered sections ("Find & Discover", "Process", "Summaries", "Synthesis") guiding the user through the process.
* **Actionable Feedback:** Implemented clear success, warning, and error messages to inform the user about the status of operations.
* **Enhanced Interactivity:** Leveraged Streamlit's widgets (sliders, expanders, file uploaders) effectively to create an engaging experience.

## 📈 Limitations & Future Enhancements

Recognizing project constraints and paving the way for future development:

* **LLM Robustness:** Performance of summarization and classification heavily depends on the chosen LLM and its rate limits/costs. Local Ollama or OpenRouter free tiers might have slower response times or lower quality than paid models.
* **PDF/Web Extraction Completeness:** While improved, complex PDF layouts (e.g., heavily scanned, multi-column tables) or highly dynamic/paywalled websites may still present extraction challenges.
* **Search Scope:** Limited to arXiv and basic Google Scholar; could integrate more academic search APIs.
* **True Agent Orchestration Framework:** For more complex, dynamic, and self-correcting multi-agent behaviors, integrating a dedicated framework (e.g., CrewAI, AutoGen) would be the next step.
* **Persistent Storage:** Currently, processed papers are lost on app refresh. Implementing a database (e.g., SQLite, PostgreSQL) would enable saving user sessions and a library of processed research.
* **Domain-Specific LLM Fine-tuning:** For even higher accuracy in a specific research field, fine-tuning an LLM on domain-specific papers could be explored.

## 📞 Contact

Feel free to connect with me for any questions, feedback, or collaborations!

* **Name:** A.Kalyan Sai
* **Email:** kalyansai0909@gmail.com
