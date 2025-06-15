import asyncio
import argparse
import sys
from call_computer_use import compile_trends
import os
from dotenv import load_dotenv
from trends.app_client import TrendsAppClient
from trends.config import TrendsConfig
import json
import traceback
from datetime import datetime

load_dotenv()

# Load configuration
config = TrendsConfig.from_env()
config.validate()

# Create the AI client
ai_client = TrendsAppClient(config)
available_functions = {
    "compile_trends": compile_trends,
}

# Get current date in ddmmyy format
current_date = datetime.now().strftime("%d%m%y")

instructions = f"""
Step1: You will help the user to explore various trends in fashion by using the computer use agent. The user will provide a query, and you will compile the trends based on that query, in a Markdown document format.
Step2: You will then prompt the user to store the trends report in an Azure Blob Storage location, so that it can be referred to or shared with others. You will use the MCP Server provided as a tool, to perform this action. provide a suitable name for the blob and suffix it with the current date in ddmmyy format. For example: {current_date}
    - when the user asks for the list of containers, and when you display the response, show the values as comma separated container name values for readability.
Note that step2 can be performed only after step1 is completed successfully.

IMPORTANT: Maintain context of previously generated reports in this conversation. If a user asks to store a report, use the report that was previously generated in this conversation session. If no report has been generated yet, ask the user to provide a query first.
"""


async def main() -> str:
    """Main entry point for the application."""
    # Initialize conversation history to maintain context across iterations
    conversation_history = []
    generated_reports = []  # Store reports separately to avoid API format issues

    while True:
        # user_query = "get me the latest trends in men's sports wear"
        user_query = input("Enter your query for fashion trends:->  ")

        # Add the new user input to conversation history
        new_user_message = {
            "role": "user",
            "content": [
                {"type": "input_text", "text": user_query},
            ],
        }
        conversation_history.append(new_user_message)
        # Use the full conversation history as input messages
        input_messages = conversation_history.copy()

        try:
            print(f"Query: {user_query}")
            print(f"Conversation history length: {len(conversation_history)}")
            print(f"Generated reports count: {len(generated_reports)}")

            # Call the Responses API with the current state using the modular client
            response = ai_client.create_app_response(
                instructions=instructions,
                conversation_history=conversation_history,
                mcp_server_url=config.mcp_server_url,
                available_functions=available_functions,
            )

            print(f"Response status: {response.status}")

            # Process all outputs in the response
            for output in response.output:
                if output.type == "function_call":
                    print(f"Function call: {output.name}")
                    function_name = output.name
                    function_to_call = available_functions[function_name]
                    function_args = json.loads(output.arguments)

                    # Execute the function
                    if asyncio.iscoroutinefunction(function_to_call):
                        function_response = await function_to_call(**function_args)
                    else:
                        function_response = function_to_call(**function_args)

                    print(f"Function {function_name} completed")

                    # Add function call result as text to conversation history
                    conversation_history.append(
                        {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": f"I executed the function '{function_name}' and generated the fashion trends report.",
                                }
                            ],
                        }
                    )

                    # Store the report if it was generated
                    if function_name == "compile_trends" and function_response:
                        generated_reports.append(function_response)
                        print("Report generated and stored in context")

                elif output.type == "mcp_list_tools":
                    # MCP tools are being listed
                    print("MCP tools listed")
                    conversation_history.append(
                        {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": "MCP tools have been loaded and are available for use.",
                                }
                            ],
                        }
                    )

                else:
                    # Regular text response or other output types
                    print(f"=== Tool call output ===")
                    print(f"Assistant response: {output}")
                    conversation_history.append(
                        {
                            "role": "assistant",
                            "content": [{"type": "output_text", "text": str(output)}],
                        }
                    )

        except KeyboardInterrupt:
            print("\nSession interrupted by user")
        except Exception as e:
            print(f"Error running application: {str(e)}")
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
