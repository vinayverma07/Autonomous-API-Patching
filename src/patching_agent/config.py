import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Centralized System Configuration Profile."""
    
    # API Server Settings
    HOST: str = Field(default="127.0.0.1")
    PORT: int = Field(default=8000)
    
    # MongoDB Atlas Settings
    MONGODB_URI: str = Field(
        default="mongodb://localhost:27017", 
        validation_alias="MONGODB_URI"
    )
    DB_NAME: str = Field(default="patching_agent_db")
    VECTOR_INDEX_NAME: str = Field(default="vector_index")
    
    # --- OPENROUTER CONFIGURATION ---
    OPENROUTER_API_KEY: str = Field(default="", validation_alias="OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1")
    LLM_MODEL: str = Field(default="openai/gpt-4o-mini")  # Or any OpenRouter model like openai/gpt-4o-mini
    
    EMBEDDING_MODEL_NAME: str = Field(default="BAAI/bge-small-en-v1.5")
    
    # Automation Safeguards
    MAX_RETRIES: int = Field(default=3)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()