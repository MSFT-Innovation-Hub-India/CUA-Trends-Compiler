"""Configuration management for trends analysis."""
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

load_dotenv()


@dataclass
class TrendsConfig:
    """Configuration settings for trends analysis."""
    
    # Azure OpenAI settings
    azure_endpoint: str
    model_name: str
    api_version: str
    vision_model_name: str
    
    # Application settings
    web_crawl_url: str
    mcp_server_url: Optional[str]
    max_pages_for_crawling: int
    display_width: int = 1024
    display_height: int = 768
    
    @classmethod
    def from_env(cls) -> 'TrendsConfig':
        """Create configuration from environment variables."""
        return cls(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            model_name=os.getenv("MODEL_NAME", "computer-use-preview"),
            api_version=os.getenv("AZURE_API_VERSION", "2025-03-01-preview"),
            vision_model_name=os.getenv("VISION_MODEL_NAME", "gpt-4o"),
            web_crawl_url=os.getenv("web_crawl_url", "https://in.pinterest.com/ideas"),
            mcp_server_url=os.getenv("MCP_SERVER_URL"),
            max_pages_for_crawling=int(os.getenv("max_pages_for_crawling", "5")),
        )
    
    def validate(self) -> None:
        """Validate required configuration values."""
        required_fields = ["azure_endpoint", "model_name", "api_version"]
        missing = [field for field in required_fields if not getattr(self, field)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
