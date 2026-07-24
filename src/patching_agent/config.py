import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """Centralized System Configuration Profile."""
    
    # API Server Settings
    HOST: str = Field(default="127.0.0.1")
    PORT: int = Field(default=8000)
    
    # MongoDB Atlas Settings
    MONGODB_URI: str = Field(validation_alias="MONGODB_URI")
    DB_NAME: str = Field(default="patching_agent_db")
    VECTOR_INDEX_NAME: str = Field(default="vector_index")
    
    # AI Engine Settings (Configured for Mistral)
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    LLM_MODEL: str = Field(default="mistral")
    EMBEDDING_MODEL_NAME: str = Field(default="BAAI/bge-small-en-v1.5")
    
    # Automation Safeguards
    MAX_RETRIES: int = Field(default=3)

    # Allow reading from environment variables
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate a global configuration singleton
settings = Settings()