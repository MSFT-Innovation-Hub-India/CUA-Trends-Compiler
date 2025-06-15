"""Main trends compiler orchestrator."""

import asyncio
import base64
from typing import List, Tuple, Dict, Any
from datetime import datetime
import os
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
        self.response_parser = ResponseParser()  # Storage for collected image data
        self.image_analyses = []

    async def compile_trends(self, user_query: str) -> str:
        """Main entry point for trends compilation."""
        print(f"Starting trends compilation for query: '{user_query}'")

        async with LocalPlaywrightComputer() as computer:
            self.action_handler = ComputerActionHandler(computer)
            # Initialize workflow state
            state = {"trends_compiled": False}
            image_center_coordinates = []
            step = 0
            markdown_report = ""

            while not state["trends_compiled"]:
                try:
                    if step == 0:
                        await self._launch_pinterest(computer)
                        step += 1
                    elif step == 1:
                        image_center_coordinates = (
                            await self._search_and_get_coordinates(computer, user_query)
                        )
                        if image_center_coordinates:
                            step += 1
                        else:
                            print("No coordinates found, ending compilation")
                            state["trends_compiled"] = True
                    elif step == 2:
                        await self._process_image_results(
                            computer, image_center_coordinates, user_query
                        )
                        # Generate consolidated markdown report
                        markdown_report = await self._generate_markdown_report(
                            user_query
                        )
                        print(f"Trends analysis report generated successfully")
                        state["trends_compiled"] = True
                    else:
                        state["trends_compiled"] = True

                except Exception as e:
                    print(f"Error in step {step}: {e}")
                    state["trends_compiled"] = True

            # Final confirmation
            # await self._final_confirmation()

            return markdown_report

    async def _launch_pinterest(self, computer) -> None:
        """Step 1: Launch Pinterest."""
        print("Step 1: Launching Pinterest...")
        await computer.goto(url=self.config.web_crawl_url)
        screenshot_bytes = await computer.screenshot()
        print("Pinterest landing page launched. Screenshot captured.")

    async def _search_and_get_coordinates(
        self, computer, user_query: str
    ) -> List[Tuple[int, int]]:
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
            screenshot_base64,
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
                print(
                    f"Check {i+1}/{max_checks}: Search results not visible. Waiting..."
                )
                await asyncio.sleep(1)

        print("Unable to get the search results in time.")
        return []

    async def _process_image_results(
        self, computer, image_center_coordinates: List[Tuple[int, int]], user_query: str
    ) -> None:
        """Step 3: Process image results."""
        print(
            "Step 3: Clicking upon the images in the search results now and navigating to the individual pages for trends..."
        )

        if not image_center_coordinates:
            print(
                "No image coordinates found from previous step. Cannot proceed with clicking."
            )
            return

        # Limit processing to configured maximum
        num_images_to_process = min(
            self.config.max_pages_for_crawling, len(image_center_coordinates)
        )
        print(f"Processing {num_images_to_process} images using stored coordinates")

        try:
            for i in range(num_images_to_process):
                await self._process_single_image(
                    computer, image_center_coordinates[i], i + 1, user_query
                )

            print("All image pages processed successfully!")

        except Exception as e:
            print(f"Error during image processing: {e}")

    async def _process_single_image(
        self, computer, coordinates: Tuple[int, int], image_num: int, user_query: str
    ) -> None:
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
        print(f"Screenshot captured for image {image_num} page")  # Get page description
        description = await self._get_page_description(
            screenshot_base64, image_num, user_query
        )
        print(
            f"Page {image_num} description: {description}"
        )  # Go back to search results
        await self._go_back_to_search_results(computer, image_num)

        # Store the image analysis for report generation
        self.image_analyses.append(description)

    async def _get_page_description(
        self, screenshot_base64: str, image_num: int, user_query: str
    ) -> str:
        """Get AI description of the current page using GPT-4o."""
        message = self.ai_client.create_message(
            f"Please provide a title for the fashion trend observed in this image, followed by a detailed description. "
            f"Start your response with 'Title: [trend name]' then describe the content of this page in a concise manner, "
            f"focusing on the trends and fashion elements visible. "
            f"The user is specifically looking for trends related to: '{user_query}'. "
            f"Please highlight any elements that are relevant to this search query.",
            screenshot_base64,
        )

        response = await self.ai_client.get_gpt4o_response([message])
        print(f"Description response for image {image_num}: {response}")

        # Extract description from response - GPT-4o responses have different structure
        if hasattr(response, "choices") and response.choices:
            # Handle standard OpenAI response format
            choice = response.choices[0]
            if hasattr(choice, "message") and hasattr(choice.message, "content"):
                return choice.message.content
        elif hasattr(response, "output") and response.output:
            # Handle responses API format if it returns output
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


    async def _get_detailed_image_analysis(
        self, screenshot_base64: str, trend_statement: str, image_num: int
    ) -> str:
        """Get detailed 500-word analysis of the image using GPT-4o vision model."""

        # Create a detailed prompt for comprehensive analysis
        analysis_prompt = f"""You are a fashion and trends expert. Please provide a comprehensive 500-word analysis of this image in relation to the trend statement: "{trend_statement}".

Your analysis should include:

1. **Visual Description**: Provide a vivid, detailed description of what you observe in the image - colors, patterns, textures, styling elements, composition, and overall aesthetic.

2. **Trend Analysis**: Analyze how the visual elements in this image relate to and exemplify the stated trend. Identify specific design elements, color schemes, styling choices, or cultural references that align with current fashion movements.

3. **Reasoning**: Explain your reasoning for how this image represents or interprets the trend statement. Consider factors like:
   - Design philosophy and aesthetic choices
   - Cultural or social influences visible in the image
   - Target audience and market positioning
   - Seasonal or temporal relevance
   - Innovation or traditional elements

4. **Context and Significance**: Discuss the broader context of this trend within current fashion, lifestyle, or design movements. How does this image contribute to or reflect larger cultural shifts?

Please write in an engaging, professional tone suitable for a fashion industry report. Be specific about visual elements and provide insightful commentary on the trend's significance."""

        try:
            # Create message for vision model
            message = {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": analysis_prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{screenshot_base64}",
                    },
                ],
            }

            # Use vision model for detailed analysis
            response = await self._get_vision_response([message])

            if hasattr(response, "output") and response.output:
                for item in response.output:
                    analysis = self.response_parser.extract_text_content(item)
                    if analysis:
                        print(f"\n{'='*80}")
                        print(f"DETAILED ANALYSIS FOR IMAGE {image_num}")
                        print(f"Trend Statement: {trend_statement}")
                        print(f"{'='*80}")
                        print(analysis)
                        print(f"{'='*80}\n")
                        return analysis

            return f"Unable to generate detailed analysis for image {image_num}"

        except Exception as e:
            print(f"Error getting detailed image analysis: {e}")
            return f"Error analyzing image {image_num}: {str(e)}"

    async def _get_vision_response(self, messages: List[Dict[str, Any]]) -> Any:
        """Get response from Azure OpenAI vision model for image analysis."""
        try:
            response = self._client.responses.create(
                model=self.config.vision_model_name,  # Use vision model from config
                input=messages,
            )
            return response
        except Exception as e:
            print(f"Error getting vision response: {e}")
            raise

    async def _generate_markdown_report(self, user_query: str) -> str:
        """Generate a comprehensive markdown report from collected image analyses."""
        print("Generating comprehensive markdown report...")

        if not self.image_analyses:
            return "# Trends Analysis Report\n\nNo trends data collected."

        # Create markdown content
        markdown_content = f"""# Trends Analysis Report

## Search Query: {user_query}
**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
Based on the analysis of {len(self.image_analyses)} trending images, here are the key findings:

"""

        # Add detailed analysis for each image
        for i, analysis in enumerate(self.image_analyses, 1):
            markdown_content += f"""## Image {i} Analysis

**Detailed Analysis:**
{analysis}

---

"""

        # Add consolidated insights
        markdown_content += """## Key Trend Insights

"""

        # Extract common themes and trends from all analyses
        all_analysis_text = " ".join(self.image_analyses)

        # Generate consolidated insights using AI
        try:
            consolidation_prompt = f"""
Based on the following individual image analyses for the query "{user_query}", provide a consolidated summary of the key trends, patterns, and insights:

{all_analysis_text}

Please identify:
1. Common themes and patterns
2. Emerging trends
3. Color palettes and design elements
4. Style directions
5. Key recommendations

Format your response as clear, actionable insights.
"""

            insights_response = await self.ai_client.get_response(
                [{"role": "user", "content": consolidation_prompt}]
            )

            if insights_response and hasattr(insights_response, "content"):
                insights = (
                    insights_response.content[0].text
                    if hasattr(insights_response.content[0], "text")
                    else str(insights_response.content[0])
                )
                markdown_content += insights
            else:
                markdown_content += (
                    "Unable to generate consolidated insights at this time."
                )

        except Exception as e:
            print(f"Error generating consolidated insights: {e}")
            markdown_content += (
                "Unable to generate consolidated insights due to an error."
            )

        markdown_content += f"""

## Report Metadata
- **Total Images Analyzed:** {len(self.image_analyses)}
- **Search Query:** {user_query}
- **Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Tool:** Trends Compiler CUA MCP

---
*Report generated by Trends Compiler using Computer Use Agent and MCP*
"""

        return markdown_content
