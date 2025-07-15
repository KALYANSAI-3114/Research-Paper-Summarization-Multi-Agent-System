# utils/constants.py

# Default LLM Prompts
DEFAULT_SUMMARY_PROMPT = """
Summarize the following research paper text concisely, highlighting the main objective, methodology, key findings, and conclusions. Focus on the most important information, aiming for 200-300 words.

Text:
---
{text}
---

Summary:
"""

DEFAULT_TOPIC_CLASSIFICATION_PROMPT = """
Classify the following research paper text into one single, most relevant topic from the provided list. Respond with ONLY the topic name, nothing else. If none fit, respond with 'Other'.

Available Topics: {topics}

Text:
---
{text}
---

Topic:
"""

DEFAULT_SYNTHESIS_PROMPT = """
Synthesize the key findings, common themes, and any conflicting points from the following research paper summaries. Identify overarching conclusions or advancements related to the shared topic. Aim for a comprehensive yet concise overview, around 400-600 words.

Summaries:
---
{summaries}
---

Synthesis:
"""

# Default user-provided topics for better classification consistency for the provided papers
# Broadened to help LLM group similar items more easily.
DEFAULT_USER_TOPICS = "Healthcare Systems, Medical Robotics, Simulation, Health Policy, Medical Technology, Artificial Intelligence"


# Max search results to display
MAX_SEARCH_RESULTS = 10

# Max characters to display for abstract/text snippets in UI
MAX_ABSTRACT_DISPLAY_CHARS = 300
MAX_TEXT_SNIPPET_CHARS = 500