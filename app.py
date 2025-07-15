import streamlit as st
import os
import io
import requests # Used for downloading PDFs from search results

# Import agents
from agents.paper_search import PaperSearchAgent
from agents.paper_processing import PaperProcessingAgent
from agents.topic_classification import TopicClassificationAgent
from agents.summary_generation import SummaryGenerationAgent
from agents.cross_synthesis import CrossPaperSynthesisAgent
from agents.audio_generation import AudioGenerationAgent

# Import utilities
from utils.llm_interface import LLMInterface
from utils.constants import DEFAULT_USER_TOPICS, MAX_SEARCH_RESULTS, MAX_ABSTRACT_DISPLAY_CHARS
from utils.helpers import format_citation, clean_text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Initialize Agents ---
llm_interface = LLMInterface() 
search_agent = PaperSearchAgent()
processing_agent = PaperProcessingAgent()
topic_agent = TopicClassificationAgent(llm_interface)
summary_agent = SummaryGenerationAgent(llm_interface)
synthesis_agent = CrossPaperSynthesisAgent(llm_interface)
audio_agent = AudioGenerationAgent()

# --- Streamlit UI Configuration ---
# Removed 'icon' argument and 'key' from expander due to persistent TypeError on some environments.
# If your Streamlit version (>= 1.10.0 for icon, >= 1.22.0 for expander key) supports them, you can add them back.
st.set_page_config(layout="wide", page_title="Research Paper Multi-Agent Summarizer") 

# Inject custom CSS
try:
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("`style.css` not found. Using default Streamlit styling. Please create `style.css` in the project root.")

st.title("📚 Research Paper Multi-Agent System") 
st.markdown("### Your AI-Powered Research Assistant") 
st.markdown("Staying updated on research across multiple fields is challenging and time-consuming. This system helps you find, analyze, summarize, and even listen to research papers!")

# Session state to store processed papers
if 'processed_papers' not in st.session_state:
    st.session_state.processed_papers = [] 

# --- Sidebar for Navigation/Settings ---
with st.sidebar:
    st.header("Settings")
    st.markdown("---")
    st.subheader("LLM Status")
    st.info(f"LLM Model: {llm_interface.model_name}") 
    
    if llm_interface.client.__class__.__name__ == '_MockLLMClient':
         st.warning("LLM API key not configured or failed to initialize. LLM operations will use mock responses. Please set OPENROUTER_API_KEY in your .env file (or ensure Ollama is running if you configured for that).")
    else:
        st.success("LLM API initialized.")

    st.markdown("---")
    st.subheader("Project Info")
    st.markdown("Developed by: A.Kalyan Sai")
    st.markdown("Source Code: [GitHub Repo](https://github.com/KALYANSAI-3114/Research-Paper-Summarization-Multi-Agent-System)") 

# --- Paper Search Section ---
st.header("1. Find & Discover Papers 🔍") 
search_query = st.text_input("Enter keywords to search for research papers (e.g., 'causal inference', 'federated learning'):", key="search_input")
search_source = st.selectbox("Select Search Source:", ["arXiv", "Google Scholar (Experimental)"], key="search_source_select")
num_search_results = st.slider("Number of search results:", 1, MAX_SEARCH_RESULTS, 5, key="num_search_results_slider")

if st.button("Search Papers", key="search_button"):
    st.session_state.processed_papers = [] 
    if not search_query:
        st.warning("Please enter a search query.")
    else:
        with st.spinner("Searching for papers..."):
            results = search_agent.run(search_query, search_source, num_search_results)

            if results:
                st.subheader(f"Search Results from {search_source}:")
                for i, paper_metadata in enumerate(results): 
                    st.markdown(f"**{i+1}. {paper_metadata['title']}**")
                    st.write(f"Authors: {', '.join(paper_metadata['authors'])}")
                    st.write(f"Abstract: {paper_metadata['abstract'][:MAX_ABSTRACT_DISPLAY_CHARS]}...")
                    
                    cols = st.columns(3)
                    with cols[0]:
                        st.link_button("Read on Source", paper_metadata['url'])
                    with cols[1]:
                        if paper_metadata.get('pdf_url') and paper_metadata['pdf_url'] != "N/A":
                            st.link_button("Download PDF", paper_metadata['pdf_url'])
                        else:
                            st.markdown("*(PDF not directly available)*")
                    
                    with cols[2]:
                        if st.button(f"Process & Summarize this Paper", key=f"process_search_result_{i}"):
                            with st.spinner(f"Processing '{paper_metadata['title']}'..."):
                                processed_info = None
                                
                                if paper_metadata.get('pdf_url') and paper_metadata['pdf_url'] != "N/A":
                                    try:
                                        pdf_response = requests.get(paper_metadata['pdf_url'], stream=True, timeout=20)
                                        pdf_response.raise_for_status()
                                        processed_info = processing_agent.run("pdf_upload", io.BytesIO(pdf_response.content), return_metadata=True)
                                    except Exception as e:
                                        st.warning(f"Could not download/process PDF from {paper_metadata['pdf_url']}. Trying source URL. Error: {e}")
                                        processed_info = processing_agent.run("url", paper_metadata['url'], return_metadata=True)
                                elif paper_metadata.get('url') and paper_metadata['url'] != "N/A":
                                    processed_info = processing_agent.run("url", paper_metadata['url'], return_metadata=True)
                                elif paper_metadata.get('doi') and paper_metadata['doi'] != "N/A":
                                    processed_info = processing_agent.run("doi", paper_metadata['doi'], return_metadata=True)
                                    
                                extracted_text = processed_info['text'] if processed_info else None
                                
                                current_paper_metadata = {
                                    "title": processed_info.get('title', paper_metadata['title']) if processed_info else paper_metadata['title'],
                                    "authors": processed_info.get('authors', paper_metadata['authors']) if processed_info else paper_metadata['authors'],
                                    "abstract": processed_info.get('abstract', paper_metadata['abstract']) if processed_info else paper_metadata['abstract'],
                                    "url": processed_info.get('url', paper_metadata['url']) if processed_info else paper_metadata['url'],
                                    "pdf_url": processed_info.get('pdf_url', paper_metadata.get('pdf_url')) if processed_info else paper_metadata.get('pdf_url'),
                                    "doi": processed_info.get('doi', paper_metadata.get('doi')) if processed_info else paper_metadata.get('doi'),
                                    "text": clean_text(extracted_text) if extracted_text else None 
                                }
                                    
                                if extracted_text: 
                                    summary = summary_agent.run(extracted_text)
                                    st.session_state.processed_papers.append({
                                        "title": current_paper_metadata['title'],
                                        "authors": current_paper_metadata['authors'],
                                        "abstract": current_paper_metadata['abstract'],
                                        "url": current_paper_metadata['url'],
                                        "pdf_url": current_paper_metadata.get('pdf_url'),
                                        "doi": current_paper_metadata.get('doi'),
                                        "summary": summary,
                                        "text": current_paper_metadata['text'],
                                        "topic": None, 
                                        "source": f"Search: {search_source}",
                                        "citation": format_citation(current_paper_metadata)
                                    })
                                    st.success(f"'{current_paper_metadata['title']}' processed and added to queue.")
                                else:
                                    st.error(f"Failed to extract text from '{current_paper_metadata['title']}'. Please try manual input.")
                    st.markdown("---")
            else:
                st.info("No papers found for your query. Try a different search term or source.")

# --- Manual Paper Input Section ---
st.header("2. Process Papers from Files, URLs, or DOIs 📄") 

uploaded_files = st.file_uploader("Upload PDF research papers", type=["pdf"], key="file_uploader", accept_multiple_files=True)
paper_url = st.text_input("Enter URL of a research paper (e.g., from ArXiv, IEEE Xplore, ResearchGate):", key="url_input")
paper_doi = st.text_input("Enter DOI of a research paper (e.g., 10.1007/s11270-019-4122-1):", key="doi_input")

if st.button("Process Manual Input", key="process_manual_button"):
    st.session_state['manual_input_status'] = [] 
    processed_any = False

    if uploaded_files: 
        for i, file in enumerate(uploaded_files): 
            st.session_state['manual_input_status'].append(f"Processing uploaded file: {file.name}")
            with st.spinner(f"Processing uploaded file: {file.name}..."):
                processed_info = processing_agent.run("pdf_upload", file, return_metadata=True) 
                extracted_text = processed_info['text'] if processed_info else None
                
                if extracted_text:
                    summary = summary_agent.run(extracted_text)
                    paper_data = {
                        "title": processed_info.get('title', file.name), 
                        "authors": processed_info.get('authors', ["N/A"]), 
                        "abstract": processed_info.get('abstract', "N/A"), 
                        "url": "N/A", 
                        "pdf_url": "N/A", 
                        "doi": processed_info.get('doi', "N/A"), 
                        "summary": summary,
                        "text": clean_text(extracted_text),
                        "topic": None,
                        "source": f"Uploaded PDF: {file.name}",
                        "citation": format_citation(processed_info) 
                    }
                    st.session_state.processed_papers.append(paper_data)
                    st.session_state['manual_input_status'].append(f"✅ '{paper_data['title']}' processed and added to queue.")
                    processed_any = True
                else:
                    st.session_state['manual_input_status'].append(f"❌ Failed to extract text from '{file.name}'.")

    elif paper_url: 
        st.session_state['manual_input_status'].append(f"Processing URL: {paper_url}")
        with st.spinner(f"Processing URL: {paper_url}..."):
            processed_info = processing_agent.run("url", paper_url, return_metadata=True) 
            extracted_text = processed_info['text'] if processed_info and 'text' in processed_info else None
            
            if extracted_text:
                summary = summary_agent.run(extracted_text)
                paper_data = {
                    "title": processed_info.get('title', f"Paper from URL: {paper_url[:50]}..."), 
                    "authors": processed_info.get('authors', ["N/A"]), 
                    "abstract": processed_info.get('abstract', "N/A"), 
                    "url": paper_url,
                    "pdf_url": processed_info.get('pdf_url', "N/A"), 
                    "doi": processed_info.get('doi', "N/A"),
                    "summary": summary,
                    "text": clean_text(extracted_text),
                    "topic": None,
                    "source": f"URL: {paper_url}",
                    "citation": format_citation(processed_info)
                }
                st.session_state.processed_papers.append(paper_data)
                st.session_state['manual_input_status'].append(f"✅ URL '{paper_url}' processed and added to queue.")
                processed_any = True
            else:
                st.session_state['manual_input_status'].append(f"❌ Failed to extract text from URL: {paper_url}.")

    elif paper_doi: 
        st.session_state['manual_input_status'].append(f"Processing DOI: {paper_doi}")
        with st.spinner(f"Processing DOI: {paper_doi}..."):
            processed_info = processing_agent.run("doi", paper_doi, return_metadata=True) 
            extracted_text = processed_info['text'] if processed_info and 'text' in processed_info else None

            if extracted_text:
                summary = summary_agent.run(extracted_text)
                paper_data = {
                    "title": processed_info.get('title', f"Paper from DOI: {paper_doi}"), 
                    "authors": processed_info.get('authors', ["N/A"]), 
                    "abstract": processed_info.get('abstract', "N/A"), 
                    "url": processed_info.get('url', "N/A"), 
                    "pdf_url": processed_info.get('pdf_url', "N/A"), 
                    "doi": paper_doi,
                    "summary": summary,
                    "text": clean_text(extracted_text),
                    "topic": None,
                    "source": f"DOI: {paper_doi}",
                    "citation": format_citation(processed_info)
                }
                st.session_state.processed_papers.append(paper_data)
                st.session_state['manual_input_status'].append(f"✅ DOI '{paper_doi}' processed and added to queue.")
                processed_any = True
            else:
                st.session_state['manual_input_status'].append(f"❌ Failed to extract text from DOI: {paper_doi}.")
    
    if not uploaded_files and not paper_url and not paper_doi:
        st.warning("Please upload at least one PDF, enter a URL, or a DOI.")
    elif not processed_any: 
        st.error("No papers were successfully processed from manual input.")
    else: 
        for status_msg in st.session_state['manual_input_status']:
            if "❌" in status_msg:
                st.error(status_msg)
            elif "✅" in status_msg:
                st.success(status_msg)
            else:
                st.info(status_msg)
        st.success("Manual processing attempt finished.")
    st.session_state['manual_input_status'] = [] 
            
# --- Processed Papers Section ---
st.header("3. Processed Papers & Individual Summaries ✨") 
if st.session_state.processed_papers:
    # Topic Classification Input
    st.subheader("Topic Classification")
    user_topics_input = st.text_input("Enter comma-separated topics for classification:",
                                      value="Machine Learning, Computer Vision, Natural Language Processing, Robotics, Healthcare AI")
    user_topic_list = [t.strip() for t in user_topics_input.split(',') if t.strip()]

    if user_topic_list and st.button("Classify Topics for All Processed Papers"):
        with st.spinner("Classifying topics..."):
            for i, paper in enumerate(st.session_state.processed_papers):
                if not paper['topic']: # Only classify if not already classified
                    paper['topic'] = topic_agent.classify(paper['text'], user_topic_list)
            st.success("Topics classified for all processed papers.")

    # Display individual paper details
    grouped_papers = {}
    for paper in st.session_state.processed_papers:
        topic = paper['topic'] if paper['topic'] else "Unclassified"
        if topic not in grouped_papers:
            grouped_papers[topic] = []
        grouped_papers[topic].append(paper)

    for topic, papers in grouped_papers.items():
        st.subheader(f"Topic: {topic}")
        for i, paper in enumerate(papers):
            with st.expander(f"**{paper['title']}** (Source: {paper['source']})"):
                st.write(f"**Summary:**")
                st.write(paper['summary'])
                st.markdown(f"**Citation:** {paper['citation']}")

                audio_placeholder = st.empty()
                if audio_placeholder.button(f"Generate Audio Summary", key=f"audio_gen_{paper['title']}_{i}"):
                    with st.spinner("Generating audio..."):
                        audio_file = audio_agent.generate_audio(paper['summary'])
                        if audio_file:
                            audio_placeholder.audio(audio_file.getvalue(), format="audio/mp3", start_time=0)
                            st.download_button(
                                label="Download Audio",
                                data=audio_file.getvalue(),
                                file_name=f"{paper['title'].replace(' ', '_')}_summary.mp3",
                                mime="audio/mp3",
                                key=f"download_audio_{paper['title']}_{i}"
                            )
                        else:
                            st.error("Could not generate audio.")
                st.markdown("---")

    st.header("4. Cross-Paper Topic Synthesis")

    selected_topic_for_synthesis = st.selectbox(
        "Select a topic to synthesize (requires at least 2 papers in that topic):",
        ["Select a Topic"] + list(grouped_papers.keys())
    )

    if selected_topic_for_synthesis != "Select a Topic":
        papers_in_selected_topic = grouped_papers[selected_topic_for_synthesis]
        if len(papers_in_selected_topic) >= 2:
            if st.button(f"Synthesize Findings for '{selected_topic_for_synthesis}'"):
                with st.spinner(f"Synthesizing findings for {selected_topic_for_synthesis}..."):
                    summaries_to_synthesize = [p['summary'] for p in papers_in_selected_topic]
                    synthesis = synthesis_agent.synthesize(summaries_to_summarize)
                    st.subheader(f"Synthesis for: {selected_topic_for_synthesis}")
                    st.write(synthesis)

                    st.markdown("**Contributing Papers:**")
                    for p in papers_in_selected_topic:
                        st.markdown(f"- {p['citation']}")

                    audio_placeholder_synthesis = st.empty()
                    if audio_placeholder_synthesis.button(f"Generate Audio for Synthesis", key=f"audio_synthesis_{selected_topic_for_synthesis}"):
                        with st.spinner("Generating audio for synthesis..."):
                            audio_file_synthesis = audio_agent.generate_audio(synthesis, filename=f"{selected_topic_for_synthesis}_synthesis.mp3")
                            if audio_file_synthesis:
                                audio_placeholder_synthesis.audio(audio_file_synthesis.getvalue(), format="audio/mp3", start_time=0)
                                st.download_button(
                                    label="Download Synthesis Audio",
                                    data=audio_file_synthesis.getvalue(),
                                    file_name=f"{selected_topic_for_synthesis}_synthesis.mp3",
                                    mime="audio/mp3",
                                    key=f"download_synthesis_audio_{selected_topic_for_synthesis}"
                                )
                            else:
                                st.error("Could not generate audio for synthesis.")
        else:
            st.info(f"Need at least 2 processed papers in '{selected_topic_for_synthesis}' to perform synthesis.")
    else:
        st.info("Select a topic above to generate a cross-paper synthesis.")

else:
    st.info("No papers processed yet. Start by searching or uploading a paper!")

st.markdown("---")
st.markdown("Developed as a Multi-Agent System prototype. Note: LLM integrations are placeholders and require actual API keys.")