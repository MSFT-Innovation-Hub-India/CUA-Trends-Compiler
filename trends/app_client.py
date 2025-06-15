"""Application-specific client for trends compilation with MCP and function tools."""

from typing import List, Dict, Any, Optional
from .ai_client import TrendsAIClient
from .config import TrendsConfig


class TrendsAppClient(TrendsAIClient):
    """Extended TrendsAIClient for application-level functionality."""

    def __init__(self, config: Optional[TrendsConfig] = None):
        if config is None:
            config = TrendsConfig.from_env()
            config.validate()
        super().__init__(config)

    def create_app_tools(
        self, mcp_server_url: str, available_functions: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create tools configuration for app-level functionality with MCP and functions."""
        tools = [
            {
                "type": "mcp",
                "server_label": "azure-storage-mcp-server",
                "server_url": mcp_server_url,
                "require_approval": "never",
            }
        ]

        # Add function tools based on available functions
        for func_name, func in available_functions.items():
            if func_name == "compile_trends":
                tools.append(
                    {
                        "type": "function",
                        "name": "compile_trends",
                        "description": "compile fashion trends from user query",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "user_query": {
                                    "type": "string",
                                    "description": "The user query to compile fashion trends",
                                },
                            },
                            "required": ["user_query"],
                        },
                    }
                )

        return tools

    def create_app_response(
        self,
        instructions: str,
        conversation_history: List[Dict[str, Any]],
        mcp_server_url: str,
        available_functions: Dict[str, Any],
    ) -> Any:
        """Create response using app-specific tools and configuration."""
        tools = self.create_app_tools(mcp_server_url, available_functions)

        return self.create_response_with_tools(
            model=self.config.vision_model_name,
            instructions=instructions,
            input_messages=conversation_history,
            tools=tools,
            parallel_tool_calls=False,
        )
