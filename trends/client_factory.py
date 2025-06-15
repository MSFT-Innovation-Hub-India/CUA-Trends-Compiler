"""Factory for creating Azure OpenAI clients with shared configuration."""

from typing import Optional
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from .config import TrendsConfig


class AzureOpenAIClientFactory:
    """Factory for creating Azure OpenAI clients."""

    @staticmethod
    def create_client(config: Optional[TrendsConfig] = None) -> AzureOpenAI:
        """
        Create Azure OpenAI client with proper authentication.

        Args:
            config: TrendsConfig instance. If None, will create from environment.

        Returns:
            Configured AzureOpenAI client
        """
        if config is None:
            config = TrendsConfig.from_env()
            config.validate()

        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
        )

        return AzureOpenAI(
            base_url=f"{config.azure_endpoint}/openai/v1/",
            azure_ad_token_provider=token_provider,
            api_version="preview",
        )
