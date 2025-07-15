# agents/audio_generation.py

import streamlit as st
from gtts import gTTS
import io

class AudioGenerationAgent:
    def __init__(self):
        self.name = "Audio Generation Agent"

    def generate_audio(self, text: str, filename: str = "summary.mp3") -> io.BytesIO | None:
        """
        Generates an audio file from the given text using gTTS.
        Returns a BytesIO object containing the MP3 data.
        """
        st.info("Generating audio summary...")
        if not text:
            st.warning("No text provided for audio generation.")
            return None
        try:
            tts = gTTS(text=text, lang='en')
            audio_bytes_io = io.BytesIO()
            tts.write_to_fp(audio_bytes_io)
            audio_bytes_io.seek(0) # Rewind to the beginning of the stream
            st.success("Audio generated.")
            return audio_bytes_io
        except Exception as e:
            st.error(f"Error generating audio: {e}")
            return None

    def run(self, text: str, filename: str = "summary.mp3") -> io.BytesIO | None:
        return self.generate_audio(text, filename)