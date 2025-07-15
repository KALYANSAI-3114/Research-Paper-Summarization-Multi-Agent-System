# utils/llm_utils.py

# ... (existing imports)
from google.cloud import texttospeech # Add this import if using Google Cloud TTS

# ... (LLMService class and instances)

def generate_audio_from_text(text: str, output_path: str, provider: str = "openai") -> Optional[str]:
    """Generates audio from text using a specified TTS provider."""
    try:
        if provider == "openai":
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text,
            )
            response.stream_to_file(output_path)
            logger.info(f"Audio saved to {output_path} using OpenAI TTS.")
            return output_path
        elif provider == "google_cloud":
            # The google-cloud-texttospeech library automatically uses GOOGLE_APPLICATION_CREDENTIALS
            # if the environment variable is set or if you are running in GCP.
            # No need to pass API key explicitly here.
            client = texttospeech.TextToSpeechClient()

            synthesis_input = texttospeech.SynthesisInput(text=text)

            # Select the type of voice and the language
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US", # You can make this configurable
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL # Or MALE, FEMALE
            )

            # Select the type of audio file you want
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3 # Or LINEAR16, OGG_OPUS
            )

            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            # The response's audio_content is binary.
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
            logger.info(f"Audio saved to {output_path} using Google Cloud TTS.")
            return output_path
        else:
            logger.error(f"Unsupported TTS provider: {provider}")
            return None
    except Exception as e:
        logger.error(f"Error generating audio with {provider}: {e}")
        return None