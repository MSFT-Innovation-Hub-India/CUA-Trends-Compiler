# filepath: c:\Users\sansri\ResponsesAPI Samples\codespace-cua-integration\common\local_playwright.py
from playwright.async_api import async_playwright, Browser, Page
import asyncio


class LocalPlaywrightComputer:
    """Launches a local Chromium instance using Playwright async API."""

    def __init__(self, headless: bool = False):
        self._playwright = None
        self._browser = None
        self._page = None
        self.headless = headless  # Default is non-headless for interactive use
        self.environment = "browser"
        self.dimensions = (1280, 800)  # Larger default viewport for VS Code

    async def __aenter__(self):
        # Start Playwright and get browser/page
        self._playwright = await async_playwright().start()
        await self._get_browser_and_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def _get_browser_and_page(self):
        width, height = self.dimensions
        launch_args = [
            f"--window-size={width + 100},{height + 100}",
            "--disable-extensions",
            "--disable-file-system",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-features=IsolateOrigins",
            "--disable-site-isolation-trials",
            "--ignore-certificate-errors",
            "--ignore-ssl-errors",
            "--ignore-certificate-errors-spki-list",
            "--disable-web-security",
            "--allow-running-insecure-content",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
        ]

        try:
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless, args=launch_args
            )

            # Create a persistent context with more permissive settings for GitHub authentication
            context = await self._browser.new_context(
                viewport={"width": width, "height": height},
                ignore_https_errors=True,
                accept_downloads=True,
            )

            # Add event listeners for page creation and closure
            context.on("page", self._handle_new_page)

            self._page = await context.new_page()
            self._page.on("close", self._handle_page_close)

            # Configure longer timeouts for VS Code which can be slow to load
            self._page.set_default_timeout(120000)  # 2 minute timeout
            self._page.set_default_navigation_timeout(120000)

            # Initialize with a blank page
            await self._page.goto("about:blank")

            # Enable console logging from the page for debugging (filter out common network errors)
            def handle_console_message(msg):
                if msg.type == "error":
                    error_text = msg.text.lower()
                    # Filter out common network errors that don't affect functionality
                    if any(
                        filter_term in error_text
                        for filter_term in [
                            "err_cert_verifier_changed",
                            "err_connection_closed",
                            "err_network_changed",
                            "failed to load resource",
                            "net::",
                        ]
                    ):
                        return  # Don't log these common network errors
                    print(f"BROWSER LOG: {msg.type}: {msg.text}")

            self._page.on("console", handle_console_message)

            return True
        except Exception as e:
            print(f"Failed to initialize browser: {str(e)}")
            return False

    def _handle_new_page(self, page):
        """Handle the creation of a new page."""
        print("New page created")
        self._page = page
        page.on("close", self._handle_page_close)

    def _handle_page_close(self, page):
        """Handle the closure of a page."""
        print("Page closed")
        if self._page == page:
            if (
                self._browser
                and self._browser.contexts
                and self._browser.contexts[0].pages
            ):
                self._page = self._browser.contexts[0].pages[-1]
            else:
                print("Warning: All pages have been closed.")
                self._page = None

    async def screenshot(self):
        """Capture screenshot of the current page."""
        if self._page:
            try:
                return await self._page.screenshot(full_page=False)
            except Exception as e:
                print(f"Screenshot failed: {e}")
                return None
        else:
            print("Cannot take screenshot, no active page")
            return None

    async def click(self, x, y, button="left"):
        """Click at the specified coordinates."""
        if not self._page:
            print("Cannot click, no active page")
            return False

        try:
            # Coordinate-based click
            await self._page.mouse.click(x, y, button=button)
            print(f"Clicked at coordinates ({x}, {y})")
            return True
        except Exception as e:
            print(f"Coordinate-based click failed at ({x}, {y}): {e}")
            return False

    async def click_selector(self, selector, button="left"):
        """Click on an element by selector."""
        if not self._page:
            print("Cannot click, no active page")
            return False

        try:
            # Selector-based click
            await self._page.wait_for_selector(selector, state="visible", timeout=10000)
            await self._page.click(selector)
            return True
        except Exception as e:
            print(f"Click failed for selector '{selector}': {e}")
            # Try clicking using JavaScript as fallback for selector-based clicks
            try:
                await self._page.evaluate(
                    f"""() => {{
                    const element = document.querySelector('{selector}');
                    if (element) {{
                        element.click();
                        return true;
                    }}
                    return false;
                }}"""
                )
                print(f"Click attempted using JavaScript fallback for '{selector}'")
                return True
            except Exception as js_error:
                print(f"JavaScript click fallback failed: {js_error}")
                return False

    async def type(self, text):
        """Type text into the currently focused element."""
        if not self._page:
            print("Cannot type, no active page")
            return False

        try:
            await self._page.keyboard.type(text, delay=50)
            return True
        except Exception as e:
            print(f"Type failed: {e}")
            return False

    async def press(self, key):
        """Press a keyboard key."""
        if not self._page:
            print("Cannot press key, no active page")
            return False

        try:
            await self._page.keyboard.press(key)
            return True
        except Exception as e:
            print(f"Key press failed for '{key}': {e}")
            return False

    async def hover(self, selector):
        """Hover over an element matching the selector."""
        if not self._page:
            print("Cannot hover, no active page")
            return False

        try:
            await self._page.hover(selector)
            return True
        except Exception as e:
            print(f"Hover failed for selector '{selector}': {e}")
            return False

    async def goto(self, url):
        """Navigate to a URL."""
        if not self._page:
            print("Cannot navigate, no active page")
            return False

        try:
            response = await self._page.goto(
                url, wait_until="networkidle", timeout=60000
            )
            print(f"[INFO] Page loaded successfully")
            return True
        except Exception as e:
            print(f"Navigation failed for URL '{url}': {e}")
            # Check if page still exists despite the error
            if self._page:
                current_url = self._page.url
                print(f"Current URL after navigation attempt: {current_url}")
            return False

    async def wait_for_load_state(self, state="networkidle", timeout=30000):
        """Wait for the page to reach a stable load state."""
        if not self._page:
            print("Cannot wait for load state, no active page")
            return False

        try:
            await self._page.wait_for_load_state(state, timeout=timeout)
            return True
        except Exception as e:
            print(f"Wait for load state '{state}' failed: {e}")
            return False

    async def evaluate(self, js_expression):
        """Execute JavaScript in the browser context."""
        if not self._page:
            print("Cannot evaluate JavaScript, no active page")
            return None

        try:
            return await self._page.evaluate(js_expression)
        except Exception as e:
            print(f"JavaScript evaluation failed: {e}")
            return None

    async def scroll(self, selector=None, x=0, y=200):
        """Scroll the page or a specific element."""
        if not self._page:
            print("Cannot scroll, no active page")
            return False

        try:
            if selector:
                await self._page.evaluate(
                    f"""(y) => {{
                    const element = document.querySelector('{selector}');
                    if (element) element.scrollBy(0, y);
                }}""",
                    y,
                )
            else:
                await self._page.evaluate(f"window.scrollBy({x}, {y})")
            return True
        except Exception as e:
            print(f"Scroll failed: {e}")
            return False

    async def get_current_url(self):
        """Get the current URL of the page."""
        if self._page:
            return self._page.url
        return None

    async def go_back(self):
        """Navigate back in browser history."""
        if not self._page:
            print("Cannot go back, no active page")
            return False

        try:
            await self._page.go_back(wait_until="networkidle", timeout=30000)
            print("[INFO] Browser back navigation completed")
            return True
        except Exception as e:
            print(f"Browser back navigation failed: {e}")
            return False
