"""Computer action handler for trends analysis."""

import asyncio
import base64
from typing import Any, List, Dict
from common.computer import Computer
from common.utils import check_blocklisted_url
from .parsers import ResponseParser


class ComputerActionHandler:
    """Handles computer actions from AI responses."""

    def __init__(self, computer: Computer):
        self.computer = computer
        self.parser = ResponseParser()

    async def handle_item(self, item) -> List[Dict[str, Any]]:
        """Handle each item; may cause a computer action + screenshot."""
        if hasattr(item, "type"):
            item_type = item.type
        elif isinstance(item, dict):
            item_type = item.get("type")
        else:
            print(f"Unknown item format: {type(item)}")
            return []

        if item_type == "message":
            return await self._handle_message_item(item)
        elif item_type == "computer_call":
            return await self._handle_computer_call_item(item)

        return []

    async def _handle_message_item(self, item) -> List[Dict[str, Any]]:
        """Handle message type items."""
        message_text = self.parser.extract_text_content(item)
        if not message_text:
            return []

        print(f"Message: {message_text}")

        # Check for coordinate patterns and perform click
        coordinates = self.parser.extract_coordinates_from_message(message_text)
        if coordinates:
            x, y = coordinates
            print(f"Detected coordinates in message: ({x}, {y})")
            print(f"Performing click at coordinates ({x}, {y})...")

            await self.computer.click(x, y)
            await self.computer.screenshot()
            return []

        # Check if asking about saving form
        if self._is_save_request(message_text):
            print("Automatically responding 'yes' to save the form")
            return [
                {
                    "role": "user",
                    "content": "Yes, please save the form by clicking the save button",
                }
            ]

        return []

    async def _handle_computer_call_item(self, item) -> List[Dict[str, Any]]:
        """Handle computer call items."""
        if hasattr(item, "action"):
            action = item.action
            action_type = action.type
            action_args = {k: v for k, v in vars(action).items() if k != "type"}
        else:
            action = item["action"]
            action_type = action["type"]
            action_args = {k: v for k, v in action.items() if k != "type"}

        try:
            await self._execute_action(action_type, action_args)
            await self.computer.screenshot()
            return []
        except Exception as e:
            print(f"Error performing action {action_type}: {e}")
            return []

    async def _execute_action(
        self, action_type: str, action_args: Dict[str, Any]
    ) -> None:
        """Execute a specific computer action."""
        match action_type:
            case "click":
                x = action_args.get("x")
                y = action_args.get("y")
                if x is not None and y is not None:
                    await self.computer.click(x, y)
                else:
                    print(f"Click action missing coordinates: {action_args}")
            case "type":
                await self.computer.type(**action_args)
            case "press":
                await self.computer.press(**action_args)
            case "hover":
                await self.computer.hover(**action_args)
            case "screenshot":
                await self.computer.screenshot()
            case "goto":
                url = action_args["url"]
                check_blocklisted_url(url)
                await self.computer.goto(url=url)
            case "scroll":
                await self.computer.scroll(**action_args)
            case _:
                raise ValueError(f"Unknown action type: {action_type}")

    def _is_save_request(self, message_text: str) -> bool:
        """Check if message is asking about saving."""
        message_lower = message_text.lower()
        return any(keyword in message_lower for keyword in ["save", "'save'", '"save"'])
