"""
Web navigation engine for the AI Web Scraper Agent.

This module handles browser automation using Playwright for multi-step website navigation,
form filling, and document extraction from government websites.
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin

from .models import WorkflowStep, County
from .logging_config import LoggerMixin


class WebNavigator(LoggerMixin):
    """Handles web navigation and automation using Playwright."""
    
    def __init__(self, config=None):
        """Initialize the web navigator.
        
        Args:
            config: Configuration object with browser settings
        """
        self.config = config
        self.browser = None
        self.context = None
        self.page = None
        self.playwright_available = self._check_playwright_availability()
        self.logger.info("web_navigator_initialized", playwright_available=self.playwright_available)
    
    def _check_playwright_availability(self) -> bool:
        """Check if Playwright is available."""
        try:
            import playwright
            return True
        except ImportError:
            return False
    
    async def initialize(self) -> None:
        """Initialize browser and context."""
        if not self.playwright_available:
            raise RuntimeError("Playwright not available. Install with: pip install playwright && playwright install")
        
        try:
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            
            # Browser configuration
            browser_type = getattr(self.config.browser_config, 'browser_type', 'chromium')
            headless = getattr(self.config.browser_config, 'headless', True)
            
            if browser_type == 'chromium':
                self.browser = await self.playwright.chromium.launch(headless=headless)
            elif browser_type == 'firefox':
                self.browser = await self.playwright.firefox.launch(headless=headless)
            elif browser_type == 'webkit':
                self.browser = await self.playwright.webkit.launch(headless=headless)
            else:
                self.browser = await self.playwright.chromium.launch(headless=headless)
            
            # Create context with viewport settings
            viewport_width = getattr(self.config.browser_config, 'viewport_width', 1920)
            viewport_height = getattr(self.config.browser_config, 'viewport_height', 1080)
            user_agent = getattr(self.config.browser_config, 'user_agent', None)
            
            context_options = {
                'viewport': {'width': viewport_width, 'height': viewport_height}
            }
            
            if user_agent:
                context_options['user_agent'] = user_agent
            
            self.context = await self.browser.new_context(**context_options)
            self.page = await self.context.new_page()
            
            self.logger.info("browser_initialized", 
                           browser_type=browser_type,
                           headless=headless,
                           viewport=f"{viewport_width}x{viewport_height}")
            
        except Exception as e:
            self.logger.error("browser_initialization_failed", error=str(e))
            raise
    
    async def navigate_to(self, url: str, county: str = "unknown") -> bool:
        """Navigate to a specific URL.
        
        Args:
            url: Target URL
            county: County name for rate limiting
            
        Returns:
            True if navigation successful
        """
        try:
            # Apply rate limiting based on county
            await self._apply_rate_limit(county)
            
            # Navigate to URL
            timeout = getattr(self.config.browser_config, 'timeout', 30000)
            await self.page.goto(url, timeout=timeout)
            
            # Wait for page to load
            await self.page.wait_for_load_state('networkidle')
            
            self.logger.info("navigation_successful", url=url, county=county)
            return True
            
        except Exception as e:
            self.logger.error("navigation_failed", url=url, error=str(e))
            return False
    
    async def fill_form(self, form_data: Dict[str, str], submit: bool = True) -> bool:
        """Fill and optionally submit a form.
        
        Args:
            form_data: Dictionary of field selectors and values
            submit: Whether to submit the form after filling
            
        Returns:
            True if form filling successful
        """
        try:
            for selector, value in form_data.items():
                # Wait for element to be available
                await self.page.wait_for_selector(selector, timeout=10000)
                
                # Clear and fill the field
                await self.page.fill(selector, value)
                
                self.logger.debug("form_field_filled", selector=selector, value=value[:10] + "...")
            
            if submit:
                # Look for submit button
                submit_selectors = [
                    'input[type="submit"]',
                    'button[type="submit"]',
                    'button:has-text("Search")',
                    'input[value*="Search"]'
                ]
                
                for submit_selector in submit_selectors:
                    try:
                        await self.page.click(submit_selector)
                        await self.page.wait_for_load_state('networkidle')
                        break
                    except:
                        continue
            
            self.logger.info("form_filled_successfully", fields=list(form_data.keys()))
            return True
            
        except Exception as e:
            self.logger.error("form_filling_failed", error=str(e))
            return False
    
    async def extract_data(self, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extract data from the current page using CSS selectors.
        
        Args:
            selectors: Dictionary of data keys and CSS selectors
            
        Returns:
            Dictionary of extracted data
        """
        extracted_data = {}
        
        try:
            for key, selector in selectors.items():
                try:
                    # Wait for element
                    await self.page.wait_for_selector(selector, timeout=5000)
                    
                    # Extract text content
                    element = await self.page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        extracted_data[key] = text.strip() if text else ""
                    else:
                        extracted_data[key] = ""
                        
                except Exception as e:
                    self.logger.warning("data_extraction_failed", key=key, selector=selector, error=str(e))
                    extracted_data[key] = ""
            
            self.logger.info("data_extracted", keys=list(extracted_data.keys()))
            return extracted_data
            
        except Exception as e:
            self.logger.error("extraction_failed", error=str(e))
            return {}
    
    async def download_file(self, url: str, file_path: Path, county: str = "unknown") -> bool:
        """Download a file from a URL.
        
        Args:
            url: File URL
            file_path: Local path to save the file
            county: County name for rate limiting
            
        Returns:
            True if download successful
        """
        try:
            # Apply rate limiting
            await self._apply_rate_limit(county)
            
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Start download
            async with self.page.expect_download() as download_info:
                await self.page.goto(url)
            
            download = await download_info.value
            
            # Save the file
            await download.save_as(file_path)
            
            self.logger.info("file_downloaded", url=url, file_path=str(file_path))
            return True
            
        except Exception as e:
            self.logger.error("download_failed", url=url, error=str(e))
            return False
    
    async def take_screenshot(self, file_path: Path) -> bool:
        """Take a screenshot of the current page.
        
        Args:
            file_path: Path to save the screenshot
            
        Returns:
            True if screenshot successful
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            await self.page.screenshot(path=str(file_path))
            
            self.logger.info("screenshot_taken", file_path=str(file_path))
            return True
            
        except Exception as e:
            self.logger.error("screenshot_failed", error=str(e))
            return False
    
    async def get_page_source(self) -> str:
        """Get the HTML source of the current page.
        
        Returns:
            HTML source code
        """
        try:
            content = await self.page.content()
            self.logger.debug("page_source_retrieved", length=len(content))
            return content
            
        except Exception as e:
            self.logger.error("page_source_failed", error=str(e))
            return ""
    
    async def _apply_rate_limit(self, county: str) -> None:
        """Apply rate limiting based on county configuration.
        
        Args:
            county: County name
        """
        try:
            from .config import get_county_config
            
            county_config = get_county_config(county)
            delay = county_config.rate_limits.get('delay_between_requests', 2)
            
            if delay > 0:
                await asyncio.sleep(delay)
                self.logger.debug("rate_limit_applied", county=county, delay=delay)
                
        except Exception as e:
            # Default delay if configuration fails
            await asyncio.sleep(2)
            self.logger.warning("rate_limit_fallback", error=str(e))
    
    async def cleanup(self) -> None:
        """Clean up browser resources."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            
            self.logger.info("browser_cleanup_completed")
            
        except Exception as e:
            self.logger.error("cleanup_failed", error=str(e))
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
