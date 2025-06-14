import os
import asyncio
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
import base64
import json

# Import required modules
from common.local_playwright import LocalPlaywrightComputer
from common.computer import Computer
from common.utils import check_blocklisted_url

# Load environment variables
load_dotenv()

AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
MODEL = os.getenv("MODEL_NAME")
DISPLAY_WIDTH = 1024
DISPLAY_HEIGHT = 768
API_VERSION = os.getenv("AZURE_API_VERSION")

WEB_CRAWL_URL = os.getenv("web_crawl_url")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "gpt-4o")
max_pages_for_crawling = int(
    os.getenv("max_pages_for_crawling", "3")
)  # Default to 10 if not set

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)

client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    azure_ad_token_provider=token_provider,
    api_version=API_VERSION,
)


def acknowledge_safety_check_callback(message: str) -> bool:
    response = input(
        f"Safety Check Warning: {message}\nDo you want to acknowledge and proceed? (y/n): "
    ).lower()
    return response.strip() == "y"


async def async_handle_item(item, computer: Computer):
    """Handle each item; may cause a computer action + screenshot."""
    if hasattr(item, "type"):  # Handle new response format with attributes
        item_type = item.type
    elif isinstance(item, dict):  # Handle old response format with dict
        item_type = item.get("type")
    else:
        print(f"Unknown item format: {type(item)}")
        return []

    # Check if the model is asking about saving the form
    if item_type == "message":  # print messages
        if hasattr(item, "content") and hasattr(item.content[0], "text"):
            message_text = item.content[0].text.lower()
            print(message_text)

            # Check if the model is asking about saving the form
            if (
                "save" in message_text
                or "'save'" in message_text
                or '"save"' in message_text
            ):
                print("Automatically responding 'yes' to save the form")
                return [
                    {
                        "role": "user",
                        "content": "Yes, please save the form by clicking the save button",
                    }
                ]

        elif isinstance(item, dict) and "content" in item:
            message_text = (
                item["content"][0]["text"].lower()
                if isinstance(item["content"][0]["text"], str)
                else ""
            )
            print(message_text)

            # Check if the model is asking about saving the form
            if (
                "save" in message_text
                or "'save'" in message_text
                or '"save"' in message_text
            ):
                print("Automatically responding 'yes' to save the form")
                return [
                    {
                        "role": "user",
                        "content": "Yes, please save the form by clicking the save button",
                    }
                ]

    if item_type == "computer_call":  # perform computer actions
        if hasattr(item, "action"):
            action = item.action
            action_type = action.type
            action_args = {k: v for k, v in vars(action).items() if k != "type"}
        else:
            action = item["action"]
            action_type = action["type"]
            action_args = {k: v for k, v in action.items() if k != "type"}
        try:
            match action_type:
                case "click":
                    # Filter out 'button' parameter as LocalPlaywrightComputer.click() doesn't accept it
                    click_args = {k: v for k, v in action_args.items() if k != "button"}
                    await computer.click(**click_args)
                case "type":
                    await computer.type(**action_args)
                case "press":
                    await computer.press(**action_args)
                case "hover":
                    await computer.hover(**action_args)
                case "screenshot":
                    await computer.screenshot()
                case "goto":
                    url = action_args["url"]
                    check_blocklisted_url(url)
                    await computer.goto(url=url)
                case "scroll":
                    await computer.scroll(**action_args)
                case _:
                    raise ValueError(f"Unknown action type: {action_type}")
            result = await computer.screenshot()
            return []
        except Exception as e:
            print(f"Error performing action {action_type}: {e}")
            return []

    return []


async def compile_trends(user_query: str):
    """
    - Your task is to help the user with their query on the latest trends on a topic of their choice.
    - On the landing page of the browser, you will see a search bar. You can type in the search query from the user above and press enter to search.
    - For each of the first {max_pages_for_crawling} image links that appear in the search results page, perform the following actions.
        - click on the image link and wait for the resulting page to load.
        - describe the content of the page in a concise manner.
        - take a screenshot of the page and encode it to base64.
        - execute keystroke Alt+Left to go back to previous page, i.e., the search results page.
        - Click on the next image link and repeat the process, till you have clicked on the first {max_pages_for_crawling} image links.
    - Once you have completed the requested task you should stop running and pass back control to your human operator.
    """
    from common.local_playwright import LocalPlaywrightComputer
    import base64

    # Replace with your Codespace URL or pass as argument if needed
    trends_source_url = (
        os.getenv("WEB_CRAWL_URL") or "https://in.pinterest.com/ideas"
    )  # Placeholder

    async with LocalPlaywrightComputer() as computer:
        tools = [
            {
                "type": "computer-preview",
                "display_width": computer.dimensions[0],
                "display_height": computer.dimensions[1],
                "environment": computer.environment,
            }
        ]
        items = []
        state = {"trends compiled": False}
        step = 0

        while not state["trends compiled"]:
            if step == 0:
                print("Step 1: Launching Pinterest...")
                await computer.goto(url=trends_source_url)
                screenshot_bytes = await computer.screenshot()
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                print("Pinterest landing page launched. Screenshot captured.")
                step += 1
            elif step == 1:
                print(
                    "Step 2: Using CUA model to locate and click on the search box..."
                )
                try:
                    # First, use CUA model to locate and click on the search box
                    screenshot_bytes = await computer.screenshot()
                    screenshot_base64 = base64.b64encode(screenshot_bytes).decode(
                        "utf-8"
                    )

                    # Prepare input for CUA model to locate search box
                    search_box_items = []
                    search_box_items.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "input_text",
                                    "text": "Please click on the search box on this page so I can type a search query.",
                                },
                                {
                                    "type": "input_image",
                                    "image_url": f"data:image/png;base64,{screenshot_base64}",
                                },
                            ],
                        }
                    )
                    # Use CUA model to locate and click search box
                    response = client.responses.create(
                        model=MODEL,
                        input=search_box_items,
                        tools=tools,
                        truncation="auto",
                    )

                    # Access the output items directly from response.output
                    if not hasattr(response, "output") or not response.output:
                        raise ValueError("No output from CUA model")

                    print(f"CUA Response: {response.output}")

                    # Process each item in the output
                    for item in response.output:
                        # Process computer calls to capture screenshots and perform actions
                        if (hasattr(item, "type") and item.type == "computer_call") or (
                            isinstance(item, dict)
                            and item.get("type") == "computer_call"
                        ):
                            await async_handle_item(item, computer)

                    # Wait a moment for the click to register
                    await asyncio.sleep(1)

                    # Now type the user query
                    print(f"Typing user query: {user_query}")
                    await computer.type(text=user_query)
                    await asyncio.sleep(1)
                    await computer.press(key="Enter")
                    print("Search initiated, waiting for the results to appear...")
                    await asyncio.sleep(2)
                    # CUA-based loop to detect 'Keep' button
                    max_checks = 10
                    user_input = f"Have the search results appeared in this screenshot? Reply only 'yes' or 'no'."

                    for i in range(max_checks):
                        items = []
                        screenshot_bytes = await computer.screenshot()
                        screenshot_base64 = base64.b64encode(screenshot_bytes).decode(
                            "utf-8"
                        )

                        items.append(
                            {
                                "role": "user",
                                "content": [
                                    {"type": "input_text", "text": user_input},
                                    {
                                        "type": "input_image",
                                        "image_url": f"data:image/png;base64,{screenshot_base64}",
                                    },
                                ],
                            }
                        )  # Use the model to analyze the screenshot
                        response = client.responses.create(
                            model=MODEL,
                            input=items,
                            tools=tools,
                            truncation="auto",
                        )

                        # Access the output from response.output (Responses API format)
                        if not hasattr(response, "output") or not response.output:
                            print("No output from model, continuing...")
                            continue

                        # Extract the text answer from the response output
                        answer = ""
                        for item in response.output:
                            if hasattr(item, "type") and item.type == "message":
                                if hasattr(item, "content") and item.content:
                                    for content_item in item.content:
                                        if hasattr(content_item, "text"):
                                            answer = content_item.text.strip().lower()
                                            break
                            elif (
                                isinstance(item, dict) and item.get("type") == "message"
                            ):
                                if "content" in item and item["content"]:
                                    for content_item in item["content"]:
                                        if "text" in content_item:
                                            answer = (
                                                content_item["text"].strip().lower()
                                            )
                                            break

                        if not answer:
                            print(
                                "No text response found in model output, continuing..."
                            )
                            continue
                        if "yes" in answer:
                            print(
                                "CUA detected search results are visible. Proceeding to click on the first image link."
                            )
                            step += 1
                            await asyncio.sleep(2)
                            break
                        else:
                            print(
                                f"Check {i+1}/{max_checks}: Search results not visible. Waiting..."
                            )
                            await asyncio.sleep(1)
                    else:
                        print("Unable to get the search results in time.")
                except Exception as e:
                    print(
                        f"Error typing prompt, waiting for Copilot response, or clicking 'Keep': {e}"
                    )
            elif step == 2:
                print(
                    "Step 3: Clicking upon the images in the search results now and navigating to the individual pages for trends..."
                )
                # i want to perform the following actions for each image link in the search results, upto the first {max_pages_for_crawling} links:
                try:  # Loop through the first max_pages_for_crawling image links
                    for i in range(max_pages_for_crawling):
                        items = []
                        user_input = f"I need to click on the {i+1}th image in the Pinterest search results grid. Please identify the exact coordinates (x, y) where I should click. Respond with just the coordinates in format 'x,y' (for example: '400,300')."

                        # Get current screenshot for CUA analysis
                        screenshot_bytes = await computer.screenshot()
                        screenshot_base64 = base64.b64encode(screenshot_bytes).decode(
                            "utf-8"
                        )
                        items.append(
                            {
                                "role": "user",
                                "content": [
                                    {"type": "input_text", "text": user_input},
                                    {
                                        "type": "input_image",
                                        "image_url": f"data:image/png;base64,{screenshot_base64}",
                                    },
                                ],
                            }
                        )                        # Ask CUA to identify the coordinates of the next image link
                        response = client.responses.create(
                            model=MODEL,
                            input=items,
                            tools=tools,
                            truncation="auto",
                        )
                        
                        # Extract coordinates from the response and perform click action
                        if not hasattr(response, 'output') or not response.output:
                            print(f"No output from CUA model for image {i+1}")
                            continue
                        
                        print(f"CUA Response for image {i+1}: {response.output}")
                        
                        # Process each item in the output to find click actions
                        clicked = False
                        for item in response.output:
                            # Process computer calls to perform click actions
                            if (hasattr(item, 'type') and item.type == "computer_call") or \
                               (isinstance(item, dict) and item.get("type") == "computer_call"):
                                print(f"Clicking on image {i+1}...")
                                await async_handle_item(item, computer)
                                clicked = True
                                break
                        
                        if not clicked:
                            print(f"No click action found for image {i+1}, skipping...")
                            continue
                        
                        # Wait for the page to load
                        print(f"Waiting for image {i+1} page to load...")
                        await asyncio.sleep(3)
                        
                        # Take a screenshot of the loaded page
                        screenshot_bytes = await computer.screenshot()
                        screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                        print(f"Screenshot captured for image {i+1} page")
                        
                        # Describe the content of the page
                        describe_items = []
                        describe_items.append(
                            {
                                "role": "user",
                                "content": [
                                    {"type": "input_text", "text": "Please describe the content of this page in a concise manner, focusing on the trends and fashion elements visible."},
                                    {
                                        "type": "input_image",
                                        "image_url": f"data:image/png;base64,{screenshot_base64}",
                                    },
                                ],
                            }
                        )
                        
                        # Get description from CUA model
                        describe_response = client.responses.create(
                            model=MODEL,
                            input=describe_items,
                            tools=tools,
                            truncation="auto",
                        )
                        
                        print(f"Description response for image {i+1}: {describe_response.output}")
                        
                        # Extract description from response
                        description = ""
                        if hasattr(describe_response, 'output') and describe_response.output:
                            for desc_item in describe_response.output:
                                if hasattr(desc_item, 'type') and desc_item.type == "message":
                                    if hasattr(desc_item, 'content') and desc_item.content:
                                        for content_item in desc_item.content:
                                            if hasattr(content_item, 'text'):
                                                description = content_item.text
                                                break
                                elif isinstance(desc_item, dict) and desc_item.get("type") == "message":
                                    if "content" in desc_item and desc_item["content"]:
                                        for content_item in desc_item["content"]:
                                            if "text" in content_item:
                                                description = content_item["text"]
                                                break
                        
                        print(f"Page {i+1} description: {description}")
                        
                        # Go back to search results page
                        print(f"Going back to search results from image {i+1}...")

                        
                        # implement a call to the cua model to click on the back button in the browser to go back to the search results page
                    
                    
                    print(f"Completed analyzing {max_pages_for_crawling} image links")
                    step += 1  # Move to next step
                except Exception as e:
                    print(f"Error processing image links: {e}")
                    step += 1  # Move to next step even if there's an error

        # Final confirmation
        print(
            "All steps completed. GitHub Copilot Chat panel is active and 'Agent' is selected."
        )
        confirm = (
            input(
                "Is there anything else to do? Ok to close the browser and complete? (y/n): "
            )
            .strip()
            .lower()
        )
        if confirm == "y":
            print("Closing browser and completing activity.")
        else:
            print("Browser will remain open for further actions.")
