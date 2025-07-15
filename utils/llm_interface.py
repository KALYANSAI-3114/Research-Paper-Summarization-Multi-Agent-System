# utils/llm_interface.py

import os
import streamlit as st
import requests
from openai import OpenAI # Used for OpenRouter compatibility

class LLMInterface:
    class _MockLLMClient:
        def __init__(self):
            self.model_name = "Mock_LLM" 

        def get_llm_response(self, prompt, temperature=0.7):
            if "summarize" in prompt.lower():
                text_start_idx = prompt.find('Text:')
                if text_start_idx != -1:
                    mock_text = prompt[text_start_idx + len('Text:'):].split('---')[0].strip()
                    return f"Mock Summary of: {mock_text[:200]}..."
                return "Mock Summary: No specific text found."
            elif "classify" in prompt.lower():
                topics_start = prompt.find('Available Topics:') + len('Available Topics:')
                topics_end = prompt.find('\n\nText:', topics_start)
                topics_str = prompt[topics_start:topics_end].strip()
                if topics_str:
                    return f"Mock Topic: {topics_str.split(',')[0].strip()}"
                return "Mock Topic: General"
            elif "synthesize" in prompt.lower():
                return f"Mock Synthesis of provided summaries. Key theme: Data analysis."
            return "Mock LLM Response: Please configure a real LLM (OpenRouter recommended!)"

        def chat(self): return self
        def completions(self): return self
        def create(self, model, messages, temperature):
            mock_response = {"choices": [{"message": {"content": self.get_llm_response(messages[1]['content'], temperature)}}]}
            return type('obj', (object,), mock_response)()
        
        def generate_content(self, prompt, generation_config):
            return type('obj', (object,), {'text': self.get_llm_response(prompt)})()

        def max_tokens_for_summary(self): return 4000
        def max_tokens_for_classification(self): return 2000
        def max_tokens_for_synthesis(self): return 6000

    def __init__(self):
        # --- OPENROUTER MODEL CONFIGURATION ---
        self.openrouter_model_name = "mistralai/mistral-7b-instruct-v0.2" # <--- Set your chosen OpenRouter model here
        
        self.model_name = self.openrouter_model_name # Name for UI display
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.client = self._initialize_llm_client()

    def _initialize_llm_client(self):
        # --- OpenRouter Initialization (using OpenAI SDK compatibility) ---
        if self.openrouter_api_key:
            st.success("OpenRouter API key loaded. Using OpenRouter for LLM tasks.")
            try:
                return OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.openrouter_api_key,
                    default_headers={
                        "HTTP-Referer": "https://streamlit.app", # Replace with your app's URL if deployed
                        "X-Title": "Research Paper Summarizer", 
                    }
                )
            except Exception as e:
                st.error(f"Failed to initialize OpenRouter client: {e}. Check your API key and network.")
                return self._MockLLMClient() 
        
        st.warning("No valid LLM API key (OpenRouter, OpenAI, Hugging Face, Ollama) found. LLM functions will use mock responses.")
        return self._MockLLMClient()


    def get_llm_response(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Sends a prompt to the LLM and returns its response.
        """
        if isinstance(self.client, LLMInterface._MockLLMClient):
            return self.client.get_llm_response(prompt, temperature)

        # --- OpenRouter API Call (using OpenAI SDK) ---
        try:
            response = self.client.chat.completions.create(
                model=self.openrouter_model_name, 
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant that summarizes research papers concisely, classifies topics, and synthesizes findings."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"Error calling OpenRouter API: {e}. Check your OpenRouter key, model choice, and credits.")
            return f"Error with OpenRouter: {e}"
        
        return "LLM integration not implemented or failed to initialize for this client type."


    def max_tokens_for_summary(self) -> int:
        if "mistral" in self.openrouter_model_name.lower():
            return 7000 
        elif "gpt-3.5-turbo" in self.openrouter_model_name.lower():
            return 12000 
        elif "gemini-pro" in self.openrouter_model_name.lower():
            return 28000
        return 4000 

    def max_tokens_for_classification(self) -> int:
        if "mistral" in self.openrouter_model_name.lower():
            return 4000
        elif "gpt-3.5-turbo" in self.openrouter_model_name.lower():
            return 8000
        elif "gemini-pro" in self.openrouter_model_name.lower():
            return 15000
        return 2000

    def max_tokens_for_synthesis(self) -> int:
        if "mistral" in self.openrouter_model_name.lower():
            return 6000
        elif "gpt-3.5-turbo" in self.openrouter_model_name.lower():
            return 12000
        elif "gemini-pro" in self.openrouter_model_name.lower():
            return 28000
        return 3000