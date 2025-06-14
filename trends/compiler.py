"""Main trends compiler orchestrator."""
import asyncio
import base64
from typing import List, Tuple, Dict, Any
from common.local_playwright import LocalPlaywrightComputer
from .config import TrendsConfig
from .ai_client import TrendsAIClient
from .action_handler import ComputerActionHandler
from .parsers import CoordinateParser, ResponseParser


class TrendsCompiler:
    """Main orchestrator for trends compilation workflow."""
    
    def __init__(self, config: TrendsConfig):
        self.config = config
        self.ai_client = TrendsAIClient(config)
        self.coordinate_parser = CoordinateParser()
        self.response_parser = ResponseParser()
    
    async def compile_trends(self, user_query: str) -> List[Dict[str, Any]]:
        """Main entry point for trends compilation."""
        print(f"Starting trends compilation for query: '{user_query}'")
        
        async with LocalPlaywrightComputer() as computer:
            self.action_handler = ComputerActionHandler(computer)
            
            # Initialize workflow state
            state = {"trends_compiled": False}
            image_center_coordinates = []
            step = 0
            
            while not state["trends_compiled"]:
                try:
                    if step == 0:
                        await self._launch_pinterest(computer)
                        step += 1
                    elif step == 1:
                        image_center_coordinates = await self._search_and_get_coordinates(
                            computer, user_query
                        )
                        if image_center_coordinates:
                            step += 1
                        else:
                            print("No coordinates found, ending compilation")
                            state["trends_compiled"] = True
                    elif step == 2:
                        await self._process_image_results(computer, image_center_coordinates)
                        state["trends_compiled"] = True
                    else:
                        state["trends_compiled"] = True
                        
                except Exception as e:
                    print(f"Error in step {step}: {e}")
                    state["trends_compiled"] = True
            
            # Final confirmation
            await self._final_confirmation()
            
            return []  # Return conversation history if needed
    
    async def _launch_pinterest(self, computer) -> None:
        """Step 1: Launch Pinterest."""
        print("Step 1: Launching Pinterest...")
        await computer.goto(url=self.config.web_crawl_url)
        screenshot_bytes = await computer.screenshot()
        print("Pinterest landing page launched. Screenshot captured.")
    
    async def _search_and_get_coordinates(self, computer, user_query: str) -> List[Tuple[int, int]]:
        """Step 2: Search and get image coordinates."""
        print("Step 2: Using CUA model to locate and click on the search box...")
        
        try:
            # Click on search box
            await self._click_search_box(computer)
            
            # Type query and search
            await self._perform_search(computer, user_query)
            
            # Wait for and detect search results
            coordinates = await self._detect_search_results(computer)
            
            if coordinates:
                centers = self.coordinate_parser.calculate_centers(coordinates)
                print(f"Stored {len(centers)} center coordinates for clicking")
                return centers
            
        except Exception as e:
            print(f"Error in search and coordinate detection: {e}")
        
        return []
    
    async def _click_search_box(self, computer) -> None:
        """Click on the search box using AI."""
        screenshot_bytes = await computer.screenshot()
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        
        message = self.ai_client.create_message(
            "Please click on the search box on this page so I can type a search query.",
            screenshot_base64
        )
        
        response = await self.ai_client.get_response([message])
        print(f"CUA Response: {response.output}")
        
        # Process the response to perform the click
        if hasattr(response, "output") and response.output:
            for item in response.output:
                await self.action_handler.handle_item(item)
        
        await asyncio.sleep(1)
    
    async def _perform_search(self, computer, user_query: str) -> None:
        """Type search query and press Enter."""
        print(f"Typing user query: {user_query}")
        await computer.type(text=user_query)
        await asyncio.sleep(1)
        await computer.press(key="Enter")
        print("Search initiated, waiting for the results to appear...")
        await asyncio.sleep(2)
    
    async def _detect_search_results(self, computer) -> List[Tuple[int, int, int, int]]:
        """Detect search results and extract coordinates."""
        search_prompt = """Have the search results appeared in this screenshot? 

Please respond with:
1. 'yes' or 'no' to indicate if search results are visible
2. If yes, provide the rectangle coordinates for each image shown in the search results in the format: [x1,y1,x2,y2] where (x1,y1) is top-left and (x2,y2) is bottom-right

Format your response as:
Answer: yes/no
Image coordinates: [[x1,y1,x2,y2], [x1,y1,x2,y2], ...]

If no search results are visible, just respond with 'no'."""
        
        max_checks = 10
        
        for i in range(max_checks):
            screenshot_bytes = await computer.screenshot()
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            
            message = self.ai_client.create_message(search_prompt, screenshot_base64)
            response = await self.ai_client.get_response([message])
            
            print("CUA Response for search results present check:", response.output)
            
            # Extract response text
            full_response = ""
            if hasattr(response, "output") and response.output:
                for item in response.output:
                    text = self.response_parser.extract_text_content(item)
                    if text:
                        full_response = text.strip()
                        break
            
            if not full_response:
                print("No text response found, continuing...")
                continue
            
            print(f"Full response: {full_response}")
            
            if self.response_parser.check_for_search_results(full_response):
                print("CUA detected search results are visible.")
                coordinates = self.coordinate_parser.extract_coordinates(full_response)
                
                if coordinates:
                    print(f"Found {len(coordinates)} image coordinates:")
                    return coordinates
                else:
                    print("No valid coordinates found in response")
                
                await asyncio.sleep(2)
                break
            else:
                print(f"Check {i+1}/{max_checks}: Search results not visible. Waiting...")
                await asyncio.sleep(1)
        
        print("Unable to get the search results in time.")
        return []
    
    async def _process_image_results(self, computer, image_center_coordinates: List[Tuple[int, int]]) -> None:
        """Step 3: Process image results."""
        print("Step 3: Clicking upon the images in the search results now and navigating to the individual pages for trends...")
        
        if not image_center_coordinates:
            print("No image coordinates found from previous step. Cannot proceed with clicking.")
            return
        
        # Limit processing to configured maximum
        num_images_to_process = min(
            self.config.max_pages_for_crawling, 
            len(image_center_coordinates)
        )
        print(f"Processing {num_images_to_process} images using stored coordinates")
        
        try:
            for i in range(num_images_to_process):
                await self._process_single_image(computer, image_center_coordinates[i], i + 1)
            
            print("All image pages processed successfully!")
            
        except Exception as e:
            print(f"Error during image processing: {e}")
    
    async def _process_single_image(self, computer, coordinates: Tuple[int, int], image_num: int) -> None:
        """Process a single image result."""
        center_x, center_y = coordinates
        print(f"Clicking on image {image_num} at coordinates ({center_x}, {center_y})")
        
        # Click on the image
        await computer.click(center_x, center_y)
        
        # Wait for page to load
        print(f"Waiting for image {image_num} page to load...")
        await asyncio.sleep(3)
        
        # Take screenshot and get description
        screenshot_bytes = await computer.screenshot()
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        print(f"Screenshot captured for image {image_num} page")
        
        # Get page description
        description = await self._get_page_description(screenshot_base64, image_num)
        print(f"Page {image_num} description: {description}")
        
        # Go back to search results
        await self._go_back_to_search_results(computer, image_num)
    
    async def _get_page_description(self, screenshot_base64: str, image_num: int) -> str:
        """Get AI description of the current page."""
        message = self.ai_client.create_message(
            "Please describe the content of this page in a concise manner, focusing on the trends and fashion elements visible.",
            screenshot_base64
        )
        
        response = await self.ai_client.get_response([message])
        print(f"Description response for image {image_num}: {response.output}")
        
        # Extract description from response
        if hasattr(response, "output") and response.output:
            for item in response.output:
                description = self.response_parser.extract_text_content(item)
                if description:
                    return description
        
        return "No description available"
    
    async def _go_back_to_search_results(self, computer, image_num: int) -> None:
        """Navigate back to search results."""
        print(f"Going back to search results from image {image_num}...")
        
        try:
            await computer.go_back()
            print("Browser back action completed")
        except Exception as back_error:
            print(f"Browser back action failed: {back_error}")
            print("Using Alt+Left fallback...")
            await computer.press(key="Alt+Left")
        
        await asyncio.sleep(2)
    
    async def _final_confirmation(self) -> None:
        """Handle final user confirmation."""
        print("All steps completed. GitHub Copilot Chat panel is active and 'Agent' is selected.")
        confirm = input(
            "Is there anything else to do? Ok to close the browser and complete? (y/n): "
        ).strip().lower()
        
        if confirm == "y":
            print("Closing browser and completing activity.")
        else:
            print("Browser will remain open for further actions.")
