"""
Configuration management for the AI Web Scraper Agent.

This module handles loading and managing configuration from environment variables,
YAML files, and default settings for different counties and browser configurations.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

from .models import AgentConfig, BrowserConfig, CountyConfig


class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self, config_file: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            config_file: Optional path to YAML configuration file
        """
        # Load environment variables
        if DOTENV_AVAILABLE:
            load_dotenv()
        
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> AgentConfig:
        """Load configuration from various sources."""
        # Start with default configuration
        config_data = self._get_default_config()
        
        # Override with YAML file if available
        if self.config_file and self.config_file.exists() and YAML_AVAILABLE:
            with open(self.config_file, 'r') as f:
                yaml_config = yaml.safe_load(f)
                config_data.update(yaml_config)
        
        # Override with environment variables
        env_config = self._get_env_config()
        config_data.update(env_config)
        
        # Create AgentConfig instance
        return AgentConfig(**config_data)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "openai_api_key": "",
            "model_name": "gpt-4-turbo-preview",
            "output_dir": Path("./output"),
            "log_level": "INFO",
            "max_concurrent_jobs": 3,
            "browser_config": {
                "headless": True,
                "browser_type": "chromium",
                "viewport_width": 1920,
                "viewport_height": 1080,
                "timeout": 30000,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            "counties": self._get_county_configs()
        }
    
    def _get_env_config(self) -> Dict[str, Any]:
        """Get configuration from environment variables."""
        config = {}
        
        # OpenAI configuration
        if os.getenv("OPENAI_API_KEY"):
            config["openai_api_key"] = os.getenv("OPENAI_API_KEY")
        
        if os.getenv("OPENAI_MODEL"):
            config["model_name"] = os.getenv("OPENAI_MODEL")
        
        # Application configuration
        if os.getenv("OUTPUT_DIR"):
            config["output_dir"] = Path(os.getenv("OUTPUT_DIR"))
        
        if os.getenv("LOG_LEVEL"):
            config["log_level"] = os.getenv("LOG_LEVEL")
        
        if os.getenv("MAX_CONCURRENT_JOBS"):
            config["max_concurrent_jobs"] = int(os.getenv("MAX_CONCURRENT_JOBS"))
        
        # Browser configuration
        browser_config = {}
        if os.getenv("HEADLESS_MODE"):
            browser_config["headless"] = os.getenv("HEADLESS_MODE").lower() == "true"
        
        if os.getenv("BROWSER_TYPE"):
            browser_config["browser_type"] = os.getenv("BROWSER_TYPE")
        
        if os.getenv("VIEWPORT_WIDTH"):
            browser_config["viewport_width"] = int(os.getenv("VIEWPORT_WIDTH"))
        
        if os.getenv("VIEWPORT_HEIGHT"):
            browser_config["viewport_height"] = int(os.getenv("VIEWPORT_HEIGHT"))
        
        if browser_config:
            config["browser_config"] = browser_config
        
        return config
    
    def _get_county_configs(self) -> Dict[str, CountyConfig]:
        """Get configuration for supported counties."""
        return {
            "charleston": CountyConfig(
                name="Charleston County",
                base_url="https://www.charlestoncounty.org",
                search_url="https://www.charlestoncounty.org/departments/prc/property-search.php",
                deeds_url="https://www.charlestoncounty.org/departments/prc/deeds.php",
                tax_url="https://www.charlestoncounty.org/departments/prc/tax-info.php",
                selectors={
                    "search_input": "#PIN",
                    "search_button": "input[type='submit']",
                    "property_link": "a[href*='property']",
                    "tax_link": "a[href*='tax']",
                    "deed_link": "a[href*='deed']",
                    "download_link": "a[href*='.pdf']"
                },
                rate_limits={
                    "requests_per_minute": 30,
                    "delay_between_requests": 2
                },
                special_handling={
                    "requires_captcha": False,
                    "session_timeout": 1800,
                    "max_concurrent_sessions": 3
                }
            ),
            "berkeley": CountyConfig(
                name="Berkeley County",
                base_url="https://www.berkeleycountysc.gov",
                search_url="https://www.berkeleycountysc.gov/departments/assessor/property-search",
                deeds_url="https://www.berkeleycountysc.gov/departments/clerk-of-court/deeds",
                tax_url="https://www.berkeleycountysc.gov/departments/treasurer/tax-bills",
                selectors={
                    "tms_input": "input[name='tms']",
                    "search_button": "button[type='submit']",
                    "property_card_link": "a:contains('Property Card')",
                    "tax_bill_link": "a:contains('Tax Bill')",
                    "tax_receipt_link": "a:contains('Tax Receipt')",
                    "deed_search_link": "a:contains('Deed Search')",
                    "pdf_download": "a[href$='.pdf']"
                },
                rate_limits={
                    "requests_per_minute": 20,
                    "delay_between_requests": 3
                },
                special_handling={
                    "requires_captcha": True,
                    "session_timeout": 900,
                    "max_concurrent_sessions": 2,
                    "date_cutoff": "2015-01-01",  # Different handling for pre/post 2015
                    "legacy_system": True
                }
            )
        }
    
    def get_county_config(self, county_name: str) -> CountyConfig:
        """Get configuration for a specific county.
        
        Args:
            county_name: Name of the county
            
        Returns:
            CountyConfig for the specified county
            
        Raises:
            ValueError: If county is not supported
        """
        if county_name not in self.config.counties:
            raise ValueError(f"Unsupported county: {county_name}")
        
        return self.config.counties[county_name]


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> AgentConfig:
    """Get the global configuration instance."""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager()
    
    return _config_manager.config


def get_county_config(county_name: str) -> CountyConfig:
    """Get configuration for a specific county."""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager()
    
    return _config_manager.get_county_config(county_name)


def reload_config(config_file: Optional[Path] = None) -> AgentConfig:
    """Reload configuration from sources."""
    global _config_manager
    
    _config_manager = ConfigManager(config_file)
    return _config_manager.config
