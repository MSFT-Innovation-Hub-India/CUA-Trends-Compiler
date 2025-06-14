from openai import AzureOpenAI
import base64
import json
import os
import asyncio
import argparse
import sys
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from playwright.async_api import async_playwright, TimeoutError

from common.local_playwright import LocalPlaywrightComputer
from common.computer import Computer
from common.utils import check_blocklisted_url
from call_computer_use import (
    compile_trends,
)

load_dotenv()

AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
MODEL = os.getenv("MODEL_NAME")  # Use MODEL_NAME for computer use
DISPLAY_WIDTH = 1024
DISPLAY_HEIGHT = 768
API_VERSION = os.getenv("AZURE_API_VERSION")
WEB_CRAWL_URL = os.getenv("web_crawl_url")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
max_pages_for_crawling = int(
    os.getenv("max_pages_for_crawling", "3")
)  # Default to 10 if not set

ITERATIONS = 10  # Max number of iterations before returning control to human supervisor

model_instructions = f"""
You are an AI agent with the ability to control a browser. You can control the keyboard and mouse. You take a screenshot after each action to check if your action was successful.
- Your task is to help the user with their query on the latest trends on a topic of their choice.
- On the landing page of the browser, you will see a search bar. You can type in the search query from the user above and press enter to search.
- For each of the first {max_pages_for_crawling} image links that appear in the search results page, perform the following actions.
    - click on the image link.
    - Describe what you see on the current page that opens after clicking on the image link.
    - execute keystroke Alt+Left to go back to previous page, i.e., the search results page.
    - Click on the next image link and repeat the process, till you have clicked on the first {max_pages_for_crawling} image links.
- Once you have completed the requested task you should stop running and pass back control to your human operator.
"""


async def main():
    """Main entry point for the application."""

    user_query="get me the latest trends in men's sports wear"
    
    try:

        print(f"=== Trend Search Computer Use Agent ===")
        print(f"Query: {user_query}")
        print(f"Model: {MODEL}")
        print(f"Max pages to crawl: {max_pages_for_crawling}")
        print(f"Starting browser automation...")
        
        # Run the computer use agent
        conversation_history = await compile_trends(user_query)

        print("\n=== Session Summary ===")
        print(f"Total messages in conversation: {len(conversation_history)}")
        print("Trend search completed!")
        
    except KeyboardInterrupt:
        print("\nSession interrupted by user")
    except Exception as e:
        print(f"Error running application: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

