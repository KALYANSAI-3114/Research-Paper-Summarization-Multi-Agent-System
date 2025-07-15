# agents/cross_synthesis.py

import streamlit as st
from utils.llm_interface import LLMInterface
from utils.constants import DEFAULT_SYNTHESIS_PROMPT

class CrossPaperSynthesisAgent:
    def __init__(self, llm_interface: LLMInterface):
        self.name = "Cross-Paper Synthesis Agent"
        self.llm = llm_interface

    def synthesize(self, summaries: list[str]) -> str:
        """
        Synthesizes information from multiple paper summaries using an LLM.
        """
        st.info("Generating cross-paper synthesis...")
        if not summaries:
            return "No summaries provided for synthesis."

        combined_summaries = "\n\n---\n\n".join(summaries)
        
        # Ensure combined summaries do not exceed LLM context window
        context_text = combined_summaries[:self.llm.max_tokens_for_synthesis()]

        prompt = DEFAULT_SYNTHESIS_PROMPT.format(summaries=context_text)

        try:
            response = self.llm.get_llm_response(prompt, temperature=0.5)
            st.success("Cross-paper synthesis generated.")
            return response.strip()
        except Exception as e:
            st.error(f"Error generating synthesis with LLM: {e}")
            return "Error generating synthesis."

    def run(self, summaries: list[str]) -> str:
        return self.synthesize(summaries)