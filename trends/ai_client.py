"""Azure OpenAI client wrapper for trends analysis."""
import base64
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from .config import TrendsConfig


class TrendsAIClient:
    """Wrapper for Azure OpenAI client with trends-specific functionality."""
    
    def __init__(self, config: TrendsConfig):
        self.config = config
        self._client = self._create_client()
        self._tools = self._create_tools()
    
    def _create_client(self) -> AzureOpenAI:
        """Create Azure OpenAI client with proper authentication."""
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), 
            "https://cognitiveservices.azure.com/.default"
        )
        
        return AzureOpenAI(
            azure_endpoint=self.config.azure_endpoint,
            azure_ad_token_provider=token_provider,
            api_version=self.config.api_version,
        )
    
    def _create_tools(self) -> List[Dict[str, Any]]:
        """Create tools configuration for computer use."""
        return [
            {
                "type": "computer-preview",
                "display_width": self.config.display_width,
                "display_height": self.config.display_height,
                "environment": "browser",
            }
        ]
    
    async def get_response(self, messages: List[Dict[str, Any]]) -> Any:
        """Get response from Azure OpenAI with computer use capabilities."""
        try:
            response = self._client.responses.create(
                model=self.config.model_name,
                input=messages,
                tools=self._tools,
                truncation="auto",
            )
            return response
        except Exception as e:
            print(f"Error getting AI response: {e}")
            raise
    
    def create_message(self, text: str, screenshot_base64: Optional[str] = None) -> Dict[str, Any]:
        """Create a properly formatted message for the AI."""
        content = [{"type": "input_text", "text": text}]
        
        if screenshot_base64:
            content.append({
                "type": "input_image",
                "image_url": f"data:image/png;base64,{screenshot_base64}",
            })
        
        return {
            "role": "user",
            "content": content
        }
