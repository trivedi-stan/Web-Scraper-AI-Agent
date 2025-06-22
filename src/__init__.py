"""
AI Web Scraper Agent - Intelligent Document Collection System

This package provides an AI-powered agent for automating multi-step website navigation
and document collection from government websites, specifically designed for real estate
document collection from Charleston County and Berkeley County, South Carolina.

Key Features:
- Natural language instruction parsing using LLM
- Intelligent workflow generation and orchestration
- Multi-county support with county-specific configurations
- Robust error handling and recovery mechanisms
- Comprehensive document management and organization
- Real-time progress tracking and reporting

Main Components:
- agent: Main orchestrator that coordinates all components
- parser: LLM-powered instruction parsing and workflow generation
- navigator: Web automation using Playwright for browser control
- document_manager: Document handling, validation, and organization
- models: Data models and type definitions
- config: Configuration management system
- logging_config: Structured logging setup
- cli: Command-line interface for user interaction

Usage:
    # Import the main agent
    from src.agent import WebScraperAgent
    
    # Or use mock implementations for testing
    from src.mock_implementations import MockAgent
    
    # Initialize and use
    agent = WebScraperAgent()
    result = await agent.execute_instruction("your instruction here")

Author: AI Agent Development Team
Built for: Zitles Intern Software Engineer (AI Agent Builder) role
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "AI Agent Development Team"
__email__ = "ai-agents@zitles.com"

# Import main classes for easy access
try:
    from .agent import WebScraperAgent
    from .models import ExecutionResult, ExecutionStatus, ProgressUpdate
    from .config import get_config, get_county_config
    
    __all__ = [
        "WebScraperAgent",
        "ExecutionResult", 
        "ExecutionStatus",
        "ProgressUpdate",
        "get_config",
        "get_county_config",
    ]
    
except ImportError:
    # Fallback if dependencies are not available
    __all__ = []
