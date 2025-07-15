# agents/topic_classification.py

import streamlit as st
from utils.llm_interface import LLMInterface
from utils.constants import DEFAULT_TOPIC_CLASSIFICATION_PROMPT

class TopicClassificationAgent:
    def __init__(self, llm_interface: LLMInterface):
        self.name = "Topic Classification Agent"
        self.llm = llm_interface

    def classify(self, text: str, topic_list: list) -> str:
        """
        Classifies the given text into one of the provided topics using an LLM.
        """
        st.info("Classifying topic...")
        if not text or not topic_list:
            st.warning("Cannot classify: missing text or topic list.")
            return "Unclassified (missing text or topics)"

        # Ensure text does not exceed LLM context window defined in llm_interface
        context_text = text[:self.llm.max_tokens_for_classification()]

        prompt = DEFAULT_TOPIC_CLASSIFICATION_PROMPT.format(
            topics=", ".join(topic_list),
            text=context_text
        )
        
        try:
            # --- START DIAGNOSTIC ADDITION ---
            st.info("--- LLM Topic Classification Debug ---")
            st.markdown(f"**Prompt sent to LLM for classification (truncated to 1000 chars):**")
            st.code(prompt[:1000] + "..." if len(prompt) > 1000 else prompt, language='text') 

            raw_response = self.llm.get_llm_response(prompt, temperature=0.1)
            
            st.markdown(f"**RAW LLM Response for Classification:**")
            st.code(raw_response, language='text')

            # --- START FIX: Post-process LLM response for consistency ---
            # Aggressively clean the LLM's raw output for better matching
            cleaned_response = raw_response.strip().replace('.', '').replace(',', '').replace('"', '').replace("'", "").lower()
            
            best_match_topic = "Unclassified" # Default if no match is found or confidence is low

            matched = False
            # Try to find an exact or very close match in the provided topic list
            for topic in topic_list:
                cleaned_topic = topic.lower().strip()
                # Prioritize exact or near-exact match
                if cleaned_response == cleaned_topic:
                    best_match_topic = topic
                    matched = True
                    break
                # More flexible matching: if the cleaned response is contained within a topic, or vice-versa
                if cleaned_topic in cleaned_response or cleaned_response in cleaned_topic:
                    best_match_topic = topic # Take the first reasonable match
                    matched = True
                    break
            
            # If the LLM output explicitly suggests 'Other' or indicates inability to classify
            if "other" in cleaned_response or "not listed" in cleaned_response or "cannot classify" in cleaned_response:
                best_match_topic = "Other"
                matched = True

            # Fallback if LLM's response doesn't match any provided topic well,
            # but also didn't explicitly say 'Other'. This might happen with very
            # verbose LLMs or bad classifications.
            if not matched and topic_list:
                 best_match_topic = "Unclassified (No good match)" # Indicate why it's unclassified


            st.markdown(f"**Processed Classification (Final Result):**")
            st.code(best_match_topic, language='text')
            st.info("--- END LLM Topic Classification Debug ---")
            # --- END FIX ---

            st.success("Topic classified.")
            return best_match_topic # Return the cleaned and matched topic
        except Exception as e:
            st.error(f"Error classifying topic with LLM: {e}")
            return "Unclassified (LLM Error)"

    def run(self, text: str, topic_list: list) -> str:
        return self.classify(text, topic_list)