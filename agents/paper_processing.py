# agents/paper_processing.py

import streamlit as st
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader # Ensure you have PyPDF2 installed
import io
import re
from typing import Dict, Any, Optional, Union, Tuple

class PaperProcessingAgent:
    def __init__(self):
        self.name = "Paper Processing and Information Extraction Agent"

    def _extract_pdf_metadata(self, file_object: io.BytesIO) -> Dict[str, Any]:
        """
        Tries to extract basic metadata (title, authors, DOI) from a PDF's internal metadata.
        This method will NOT raise an error if raw_metadata is not found.
        """
        metadata_dict = {"title": "N/A", "authors": ["N/A"], "abstract": "N/A", "doi": "N/A"}
        try:
            reader = PdfReader(file_object)
            metadata = reader.metadata
            if metadata:
                # Try to get Title
                title = metadata.get('/Title', '').strip()
                if title:
                    metadata_dict["title"] = title
                
                # Try to get Author(s)
                author_str = metadata.get('/Author', '').strip()
                if author_str:
                    authors_list = [a.strip() for a in re.split(r';|,|and', author_str) if a.strip()]
                    if authors_list:
                        metadata_dict["authors"] = authors_list
                
                # Try to extract DOI from common PDF custom metadata fields
                # This is a heuristic and might not always find it.
                if metadata.get('/DOI'):
                    metadata_dict["doi"] = metadata.get('/DOI').strip()
                elif metadata.get('/Identifier'):
                    doi_match = re.search(r'(10\.\d{4,9}/[^\s"]+)', metadata.get('/Identifier'))
                    if doi_match:
                        metadata_dict["doi"] = doi_match.group(1)
                
                # Try from other common fields that might contain DOI
                for key in metadata.keys():
                    if 'doi' in key.lower() and isinstance(metadata[key], str):
                        doi_match = re.search(r'(10\.\d{4,9}/[^\s"]+)', metadata[key])
                        if doi_match:
                            metadata_dict["doi"] = doi_match.group(1)
                            break

        except Exception as e:
            st.warning(f"Error extracting PDF metadata (some fields might be N/A): {e}")
        return metadata_dict

    def extract_text_from_pdf(self, file_object: io.BytesIO) -> Tuple[str | None, Dict[str, Any]]:
        """
        Extracts text from a PDF file object and tries to get basic metadata.
        Returns (text, metadata_dict).
        """
        st.info("Extracting text from PDF...")
        text = ""
        # Get metadata first; _extract_pdf_metadata needs to read the file, so ensure it's at start
        file_object.seek(0) 
        metadata = self._extract_pdf_metadata(file_object) 
        
        try:
            # Ensure file_object is at the beginning for text extraction after metadata read
            file_object.seek(0) 
            pdf_reader = PdfReader(file_object)
            
            # Extract text from all pages
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            
            text = re.sub(r'\s+', ' ', text).strip()
            text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text) # Handle hyphenated words
            
            # --- NEW HEURISTICS: Extract Title/Authors/Abstract from first page text if metadata is N/A ---
            first_page_text = pdf_reader.pages[0].extract_text() or ""
            
            # Try to get Title from first page if not in metadata
            if metadata["title"] == "N/A" or not metadata["title"].strip():
                # Heuristic: Title is often the first bold, large text block, or first few lines
                title_match = re.search(r'^\s*([^\n\r]+)\n\s*(?:author|by|abstract)', first_page_text, re.I | re.DOTALL | re.MULTILINE)
                if title_match:
                    potential_title = title_match.group(1).strip()
                    if 10 < len(potential_title) < 200 and not any(kw in potential_title.lower() for kw in ['abstract', 'introduction', 'keywords']):
                        metadata["title"] = potential_title
                elif len(pdf_reader.pages) > 0: # Fallback: just take the first few lines if they look like a title
                    first_lines = "\n".join(first_page_text.split('\n')[:3]).strip()
                    if 10 < len(first_lines) < 200 and '\n' in first_lines:
                         metadata["title"] = first_lines
            
            # Try to get Authors from first page if not in metadata
            if metadata["authors"] == ["N/A"] or not metadata["authors"][0].strip():
                # Look for common author patterns in the first 500-1500 characters of the first page
                author_section_search = re.search(
                    r"(?:author(?:s)?|by|contributors|affiliation(?:s)?)\s*([A-Z].*?)(?=\n\s*(?:abstract|introduction|keywords|\d+\s*\.)|\n\n\s*[A-Z][a-zA-Z\s]+(?:\s+section))",
                    first_page_text[:1500], # Search in the first N characters
                    re.IGNORECASE | re.DOTALL | re.MULTILINE
                )
                if author_section_search:
                    potential_authors_str = author_section_search.group(1).strip()
                    # Filter out obvious non-author related words (affiliations, emails, etc.)
                    potential_authors_str = re.sub(r'\(.*?\)|\[.*?\]|\d+|@\S+', '', potential_authors_str) # Remove parenthesized/bracketed text, numbers, emails
                    potential_authors_str = re.sub(r'Department|University|Institute|College|Centre|Lab|Corresponding Author|Email|Address', '', potential_authors_str, flags=re.I)
                    potential_authors_str = re.sub(r'\s+', ' ', potential_authors_str).strip()

                    # Split by common author list delimiters (comma, ' and ')
                    extracted_authors = [
                        a.strip() for a in re.split(r',?\s*(?:and|,\s*)\s*', potential_authors_str)
                        if a.strip() and len(a.split()) >= 1 and len(a) < 50 # At least one name part, not too long
                    ]
                    
                    # Further refine: check if names look plausible
                    final_authors = []
                    for author in extracted_authors:
                        if re.match(r'^[A-Z][a-z\'-]+(?:\s+[A-Z][a-z\'-]+){0,2}$', author): # Basic check for Capitalized Words
                            final_authors.append(author)
                        elif len(author.split()) >= 2: # Accept if it's multiple words (e.g., First Last)
                            final_authors.append(author)

                    if final_authors:
                        metadata["authors"] = list(set(final_authors)) # Deduplicate
                
                # Fallback: simple line-by-line check if still N/A
                if metadata["authors"] == ["N/A"] or not metadata["authors"][0].strip():
                    lines = first_page_text.split('\n')
                    potential_lines_for_authors = []
                    for line in lines[3:10]: # Check lines typically after title, before abstract/intro
                        line_stripped = line.strip()
                        if re.fullmatch(r'^[A-Z][a-zA-Z.-]+\s+[A-Z][a-zA-Z.-]+(?:,\s*[A-Z][a-zA-Z.-]+\s+[A-Z][a-zA-Z.-]+)*$', line_stripped) and len(line_stripped) < 150:
                            potential_lines_for_authors.append(line_stripped)
                    if potential_lines_for_authors:
                        combined_authors = ", ".join(potential_lines_for_authors)
                        extracted_authors = [a.strip() for a in re.split(r',|\s*and\s*', combined_authors) if a.strip()]
                        extracted_authors = [a for a in extracted_authors if len(a.split()) >= 2] # Ensure it's like a name
                        if extracted_authors:
                            metadata["authors"] = list(set(extracted_authors))

            # Simple heuristic to try and find abstract in text if not in metadata
            if metadata.get("abstract", 'N/A') == 'N/A' or not metadata["abstract"].strip():
                abstract_match = re.search(r'(?:abstract|summary)\s*(.+?)(?=\n(?:1\s+Introduction|I\s+Introduction|Keywords|1\s*\.|2\s*\.)|\n\n\s*[A-Z][a-zA-Z\s]+(?:\s+section|\s+I|\s+II))', text, re.I | re.DOTALL)
                if abstract_match:
                    abstract_candidate = abstract_match.group(1).strip()
                    if 50 < len(abstract_candidate) < 2000 and '\n' in abstract_candidate:
                        metadata["abstract"] = abstract_candidate
            
            st.success("Text extracted from PDF.")
            return text, metadata
        except Exception as e:
            st.error(f"Error processing PDF: {e}")
            metadata["text"] = None # Indicate text extraction failed in metadata
            return None, metadata


    def extract_text_and_metadata_from_url(self, url: str) -> Tuple[str | None, Dict[str, Any]]:
        """
        Extracts text and attempts to parse metadata (title, authors, abstract) from a URL.
        Returns (text, metadata_dict).
        """
        st.info(f"Extracting text and metadata from URL: {url}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        text = None
        metadata = {"title": "N/A", "authors": ["N/A"], "abstract": "N/A", "url": url, "pdf_url": "N/A", "doi": "N/A"}

        try:
            response = requests.get(url, timeout=20, headers=headers)
            response.raise_for_status()

            # Handle direct PDF links
            if 'application/pdf' in response.headers.get('Content-Type', ''):
                st.info("URL points directly to a PDF. Processing as PDF...")
                pdf_bytes_io = io.BytesIO(response.content)
                extracted_text_from_pdf, pdf_metadata = self.extract_text_from_pdf(pdf_bytes_io) # This now returns (text, metadata)
                
                # Merge PDF metadata with URL metadata (URL metadata takes precedence for URL, pdf_url, doi if found)
                metadata.update(pdf_metadata)
                metadata["url"] = url # Retain original URL
                metadata["pdf_url"] = url # Mark as PDF URL
                
                return extracted_text_from_pdf, metadata

            # Handle HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # --- Attempt to extract metadata from HTML (common academic patterns) ---
            metadata["title"] = soup.find('title').get_text(strip=True) if soup.find('title') else 'N/A'
            
            authors_list = []
            # Try meta tags first
            meta_author = soup.find('meta', attrs={'name': 'author'}) or soup.find('meta', attrs={'property': 'og:author'})
            if meta_author and meta_author.get('content'):
                authors_list.extend([a.strip() for a in meta_author.get('content').split(',') if a.strip()])
            
            if not authors_list: # Only if authors not found in meta tags
                common_author_classes = [
                    re.compile(r'author', re.I), # 'author', 'article-author', etc.
                    re.compile(r'creator', re.I),
                    re.compile(r'person', re.I), # 'person_name'
                    re.compile(r'name', re.I),   # 'name', 'full-name', 'c-card__author-name'
                    re.compile(r'contrib-group', re.I), # For JATS XML based sites (e.g., PubMed)
                    re.compile(r'article-meta', re.I), # Metadata sections often contain authors
                    re.compile(r'ArticleAuthor|authors-list', re.I) # More specific patterns
                ]
                
                for cls_pattern in common_author_classes:
                    for tag in soup.find_all(class_=cls_pattern):
                        text_content = tag.get_text(separator=' ', strip=True)
                        if len(text_content) > 3 and len(text_content) < 100 and len(text_content.split()) >= 2:
                            # Filter out obvious non-author content (affiliations, roles etc.)
                            if not re.search(r'(department|university|institution|editor|prof\.|contributor|affiliation|corresponding author)', text_content, re.I):
                                authors_list.extend([a.strip() for a in re.split(r',|\sand\s', text_content) if a.strip()])
                    if authors_list:
                        break
            
            if authors_list:
                authors_list = list(set([re.sub(r'[\(\[].*?[\)\]]|\d+|@\S+', '', a).strip() for a in authors_list if a.strip()])) # Remove more noise
                authors_list = [a for a in authors_list if len(a.split()) >= 2 and len(a) < 50 and a.lower() not in ["abstract", "introduction", "keywords"]] # Final filter
                if authors_list:
                    metadata["authors"] = authors_list
                else:
                    metadata["authors"] = ["N/A"]
            else:
                metadata["authors"] = ["N/A"]


            abstract_tag = soup.find('meta', attrs={'name': 'description'}) or \
                           soup.find('meta', attrs={'property': 'og:description'}) or \
                           soup.find(lambda tag: 'abstract' in tag.get('class', []) or tag.get('id') == 'abstract' or (tag.name == 'p' and 'abstract' in tag.get_text(strip=True).lower()[:15])) or \
                           soup.find('section', class_=re.compile(r'abstract', re.I))

            if abstract_tag:
                if abstract_tag.name == 'meta':
                    metadata["abstract"] = abstract_tag.get('content', 'N/A').strip()
                else:
                    abstract_text = abstract_tag.get_text(strip=True)
                    abstract_text = re.sub(r'^abstract\s*[-—:]?\s*', '', abstract_text, flags=re.I).strip()
                    metadata["abstract"] = abstract_text
            
            doi_tag = soup.find('meta', attrs={'name': 'citation_doi'}) or \
                      soup.find('meta', attrs={'property': 'og:doi'}) or \
                      soup.find('a', href=re.compile(r'doi\.org'))
            if doi_tag:
                if doi_tag.name == 'meta':
                    metadata["doi"] = doi_tag.get('content', 'N/A').strip()
                elif doi_tag.name == 'a' and doi_tag.get('href'):
                    doi_match = re.search(r'(10\.\d{4,9}/[^\s"]+)', doi_tag['href'])
                    if doi_match:
                        metadata["doi"] = doi_match.group(1)

            # --- Extract raw text content ---
            article_body = soup.find('div', class_=re.compile(r'article-body|content-body|main-content', re.I)) or \
                           soup.find('article') or \
                           soup.find('div', id=re.compile(r'content|body|main', re.I))

            if article_body:
                text_elements = article_body.find_all(['p', 'h1', 'h2', 'h3', 'li'])
            else:
                text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'li'])
            
            main_content_text = []
            for element in text_elements:
                parent_classes = ' '.join(element.parent.get('class', []))
                if not any(cls in parent_classes for cls in ['header', 'footer', 'nav', 'sidebar', 'menu', 'citation_info', 'references', 'acknowledgments', 'footnotes']):
                    main_content_text.append(element.get_text())

            text = "\n".join(main_content_text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            st.success("Text and metadata extracted from URL.")
            metadata["text"] = text # Add text to metadata for a single return dict
            return text, metadata 
        except requests.exceptions.RequestException as e:
            st.error(f"Network or HTTP error fetching URL: {e}")
            metadata["text"] = None
            return None, metadata
        except Exception as e:
            st.error(f"Error parsing URL content: {e}")
            metadata["text"] = None
            return None, metadata

    def extract_text_and_metadata_from_doi(self, doi: str) -> Tuple[str | None, Dict[str, Any]]:
        """
        Resolves a DOI and attempts to extract text and metadata from the linked content.
        Returns (text, metadata_dict).
        """
        st.info(f"Attempting to resolve DOI: {doi} and extract content...")
        metadata = {"title": "N/A", "authors": ["N/A"], "abstract": "N/A", "url": "N/A", "pdf_url": "N/A", "doi": doi}
        text = None
        try:
            crossref_api_url = f"https://api.crossref.org/works/{doi}"
            headers = {'User-Agent': 'ResearchPaperSummarizer/1.0 (mailto:your_email@example.com)'}
            response = requests.get(crossref_api_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data['status'] == 'ok' and 'message' in data:
                message = data['message']
                
                metadata["title"] = message.get('title', ['N/A'])[0] if message.get('title') else 'N/A'
                if message.get('author'):
                    metadata["authors"] = [a.get('given', '') + ' ' + a.get('family', '') for a in message['author'] if a.get('given') or a.get('family')]
                    metadata["authors"] = [a.strip() for a in metadata["authors"] if a.strip()]
                
                abstract_raw = message.get('abstract', 'N/A')
                if abstract_raw != 'N/A':
                    metadata["abstract"] = re.sub(r'<[^>]+>', '', abstract_raw).strip()
                
                metadata["doi"] = doi
                metadata["url"] = message.get('URL', 'N/A')
                
                if 'link' in message:
                    for link in message['link']:
                        if link.get('content-type') == 'application/pdf' and link.get('URL'):
                            metadata["pdf_url"] = link['URL']
                            st.info(f"Crossref found direct PDF URL: {metadata['pdf_url']}")
                            extracted_text_from_pdf, _ = self.extract_text_from_pdf(io.BytesIO(requests.get(metadata['pdf_url'], stream=True, timeout=20, headers=headers).content))
                            metadata["text"] = extracted_text_from_pdf
                            return extracted_text_from_pdf, metadata 
                
                if metadata["url"] != 'N/A' and metadata["url"] != url:
                    st.info(f"No direct PDF found via Crossref. Attempting to extract text from main URL: {metadata['url']}")
                    extracted_text_from_url, url_metadata_from_scrape = self.extract_text_and_metadata_from_url(metadata['url'])
                    metadata.update({k: v for k, v in url_metadata_from_scrape.items() if v not in ['N/A', ['N/A'], ''] and k != 'text'})
                    metadata["text"] = extracted_text_from_url
                    return extracted_text_from_url, metadata

            st.warning(f"Could not directly extract content for DOI: {doi}. Metadata might be limited.")
            metadata["text"] = None
            return None, metadata

        except requests.exceptions.RequestException as e:
            st.error(f"Network or HTTP error resolving DOI {doi}: {e}")
            metadata["text"] = None
            return None, metadata
        except Exception as e:
            st.error(f"Error handling DOI {doi}: {e}")
            metadata["text"] = None
            return None, metadata

    def run(self, source_type: str, input_data: Union[io.BytesIO, str], return_metadata: bool = False) -> Union[str | None, Dict[str, Any]]:
        """
        Processes input and extracts text and metadata.
        If return_metadata is True, returns a dictionary {"text": ..., "title": ..., "authors": ..., ...}.
        Otherwise (for old calls), returns just text.
        """
        extracted_text = None
        extracted_metadata = {"title": "N/A", "authors": ["N/A"], "abstract": "N/A", "url": "N/A", "pdf_url": "N/A", "doi": "N/A"}

        if source_type == "pdf_upload":
            extracted_text, extracted_metadata = self.extract_text_from_pdf(input_data)
        elif source_type == "url":
            extracted_text, extracted_metadata = self.extract_text_and_metadata_from_url(input_data)
        elif source_type == "doi":
            extracted_text, extracted_metadata = self.extract_text_and_metadata_from_doi(input_data)
        else:
            st.error(f"Unknown source type: {source_type}")
        
        extracted_metadata["text"] = extracted_text 

        if return_metadata:
            return extracted_metadata
        else:
            return extracted_text