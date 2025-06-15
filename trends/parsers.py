"""Coordinate parsing and image processing utilities."""

import re
from typing import List, Tuple, Optional


class CoordinateParser:
    """Handles parsing and processing of image coordinates from AI responses."""

    @staticmethod
    def extract_coordinates(response_text: str) -> List[Tuple[int, int, int, int]]:
        """Extract image coordinates from AI response text."""
        # Look for coordinate pattern in response
        coord_pattern = r"image coordinates:\s*(\[.*\])"
        coord_match = re.search(coord_pattern, response_text, re.IGNORECASE | re.DOTALL)

        if not coord_match:
            return []

        try:
            coord_text = coord_match.group(1)
            # Parse individual coordinate arrays [x1,y1,x2,y2]
            coord_arrays_pattern = r"\[(\d+),(\d+),(\d+),(\d+)\]"
            coordinates = re.findall(coord_arrays_pattern, coord_text)

            return [
                (int(x1), int(y1), int(x2), int(y2)) for x1, y1, x2, y2 in coordinates
            ]

        except Exception as e:
            print(f"Error parsing coordinates: {e}")
            return []

    @staticmethod
    def calculate_centers(
        coordinates: List[Tuple[int, int, int, int]],
    ) -> List[Tuple[int, int]]:
        """Calculate center points from rectangle coordinates."""
        centers = []
        for idx, (x1, y1, x2, y2) in enumerate(coordinates):
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            centers.append((center_x, center_y))
            print(
                f"  Image {idx+1}: Rectangle [{x1},{y1},{x2},{y2}] -> Center ({center_x},{center_y})"
            )

        return centers


class ResponseParser:
    """Handles parsing of various AI response formats."""

    @staticmethod
    def extract_text_content(item) -> str:
        """Extract text content from response item."""
        if hasattr(item, "content") and item.content:
            for content_item in item.content:
                if hasattr(content_item, "text"):
                    return content_item.text
        elif isinstance(item, dict) and "content" in item:
            for content_item in item["content"]:
                if isinstance(content_item, dict) and "text" in content_item:
                    return content_item["text"]
        return ""

    @staticmethod
    def check_for_search_results(response_text: str) -> bool:
        """Check if search results are visible in the response."""
        return "yes" in response_text.lower()

    @staticmethod
    def extract_coordinates_from_message(
        message_text: str,
    ) -> Optional[Tuple[int, int]]:
        """Extract click coordinates from message text if present."""
        coordinate_patterns = [
            r"'(\d+),(\d+)'",  # 'x,y' format
            r"(\d+),(\d+)",  # x,y format
            r"(\d+),\s*(\d+)",  # x, y format (with optional space)
            r"\((\d+),\s*(\d+)\)",  # (x, y) format
        ]

        for pattern in coordinate_patterns:
            match = re.search(pattern, message_text)
            if match:
                try:
                    x = int(match.group(1))
                    y = int(match.group(2))
                    return (x, y)
                except (ValueError, IndexError):
                    continue

        return None
