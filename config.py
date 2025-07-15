# config.py
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv() # Load environment variables from .env file

class Settings(BaseSettings):
    # ... (API Keys)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    SEMANTIC_SCHOLAR_API_KEY: str = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

    # For Google Cloud TTS, if you use a service account JSON key file
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/database.db")

    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0") # "redis" is the service name in docker-compose
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

    # Paths (relative to WORKDIR /app inside container)
    BASE_DATA_DIR: str = "./data"
    RAW_PAPERS_DIR: str = os.path.join(BASE_DATA_DIR, "raw_papers")
    PROCESSED_TEXTS_DIR: str = os.path.join(BASE_DATA_DIR, "processed_texts")
    SUMMARIES_DIR: str = os.path.join(BASE_DATA_DIR, "summaries")
    AUDIO_PODCASTS_DIR: str = os.path.join(BASE_DATA_DIR, "audio_podcasts")

    # ... (LLM Models, Default Search Params)

    def create_directories(self):
        # These paths are relative to the container's /app/data directory
        os.makedirs(self.RAW_PAPERS_DIR, exist_ok=True)
        os.makedirs(self.PROCESSED_TEXTS_DIR, exist_ok=True)
        os.makedirs(self.SUMMARIES_DIR, exist_ok=True)
        os.makedirs(self.AUDIO_PODCASTS_DIR, exist_ok=True)

settings = Settings()
settings.create_directories()