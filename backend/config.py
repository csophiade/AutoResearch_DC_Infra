import os
from dotenv import load_dotenv

# Load local .env file if it exists
load_dotenv()

class Settings:
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    
    # Modal config
    MODAL_APP_NAME: str = os.getenv("MODAL_APP_NAME", "voice-researcher-agent")
    
    # Server configs
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    
    # Force Mock Mode for presentation safety
    FORCE_MOCK_MODE: bool = os.getenv("FORCE_MOCK_MODE", "false").lower() in ("true", "1", "yes")

    @property
    def has_openai(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    @property
    def has_tavily(self) -> bool:
        return bool(self.TAVILY_API_KEY)

    @property
    def is_mock_mode(self) -> bool:
        # If forced or if OpenAI API key is missing, run in Mock/Demo mode
        return self.FORCE_MOCK_MODE or not self.has_openai

settings = Settings()
