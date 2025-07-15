# agents/summary_generation.py

import streamlit as st
from utils.llm_interface import LLMInterface
from utils.constants import DEFAULT_SUMMARY_PROMPT

class SummaryGenerationAgent:
    def __init__(self, llm_interface: LLMInterface):
        self.name = "Summary Generation Agent"
        self.llm = llm_interface

    def generate_individual_summary(self, text: str) -> str:
        """
        Generates a concise summary of the given text using an LLM.
        """
        st.info("Generating individual summary...")
        if not text:
            return "No text provided for summarization."

        # Ensure text does not exceed LLM context window
        context_text = text[:self.llm.max_tokens_for_summary()]

        prompt = DEFAULT_SUMMARY_PROMPT.format(text=context_text)

        try:
            response = self.llm.get_llm_response(prompt, temperature=0.3)
            st.success("Individual summary generated.")
            return response.strip()
        except Exception as e:
            st.error(f"Error generating summary with LLM: {e}")
            return "Error generating summary."

    def run(self, text: str) -> str:
        return self.generate_individual_summary(text)