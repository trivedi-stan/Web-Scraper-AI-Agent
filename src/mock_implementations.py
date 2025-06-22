"""
Mock implementations for testing without external dependencies.

This module provides mock implementations of external services and libraries
to enable testing and development without requiring API keys or browser installations.
"""

import asyncio
import json
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from .models import ExecutionPlan, ExecutionResult, ExecutionStatus, ErrorRecord, ProgressUpdate
from .logging_config import LoggerMixin


class MockLLMParser(LoggerMixin):
    """Mock LLM parser for testing without OpenAI API."""
    
    def __init__(self):
        self.logger.info("mock_llm_parser_initialized")
    
    def parse_instruction(self, instruction: str) -> Dict[str, Any]:
        """Mock instruction parsing."""
        self.logger.info("mock_parsing_instruction", instruction_length=len(instruction))
        
        # Simple regex-based parsing
        import re
        
        # Extract county
        county = "charleston"
        if re.search(r'berkeley', instruction, re.IGNORECASE):
            county = "berkeley"
        
        # Extract TMS numbers
        tms_pattern = r'\b\d{10}\b'
        tms_numbers = re.findall(tms_pattern, instruction)
        
        # Extract document types
        doc_types = []
        if re.search(r'property\s+card', instruction, re.IGNORECASE):
            doc_types.append("property_card")
        if re.search(r'tax', instruction, re.IGNORECASE):
            doc_types.append("tax_info")
        if re.search(r'deed', instruction, re.IGNORECASE):
            doc_types.append("deed")
        
        if not doc_types:
            doc_types = ["property_card", "tax_info", "deed"]
        
        return {
            "county": county,
            "tms_numbers": tms_numbers,
            "document_types": doc_types,
            "workflow_description": f"Mock parsing for: {instruction[:50]}...",
            "priority": 1,
            "estimated_duration": len(tms_numbers) * 180 if tms_numbers else 180
        }


class MockWebNavigator(LoggerMixin):
    """Mock web navigator for testing without browser."""
    
    def __init__(self, config=None):
        self.config = config
        self.current_url = ""
        self.mock_data = self._load_mock_data()
        self.logger.info("mock_navigator_initialized")
    
    def _load_mock_data(self) -> Dict[str, Any]:
        """Load mock data for different websites."""
        return {
            "charleston": {
                "5590200072": {
                    "property_card": "Mock Charleston Property Card for TMS 5590200072",
                    "tax_info": "Mock Charleston Tax Info for TMS 5590200072",
                    "deeds": ["Mock Deed Book 1234 Page 567", "Mock Deed Book 2345 Page 678"]
                },
                "5321500185": {
                    "property_card": "Mock Charleston Property Card for TMS 5321500185",
                    "tax_info": "Mock Charleston Tax Info for TMS 5321500185",
                    "deeds": ["Mock Deed Book 3456 Page 789"]
                }
            },
            "berkeley": {
                "2590502005": {
                    "property_card": "Mock Berkeley Property Card for TMS 2590502005",
                    "tax_bill": "Mock Berkeley Tax Bill for TMS 2590502005",
                    "tax_receipt": "Mock Berkeley Tax Receipt for TMS 2590502005",
                    "deeds": ["Mock Deed Book 4567 Page 890"]
                },
                "2340601038": {
                    "property_card": "Mock Berkeley Property Card for TMS 2340601038",
                    "tax_bill": "Mock Berkeley Tax Bill for TMS 2340601038",
                    "deeds": ["Mock Deed Book 5678 Page 901", "Mock Deed Book 6789 Page 012"]
                }
            }
        }
    
    async def initialize(self) -> None:
        """Mock browser initialization."""
        await asyncio.sleep(0.1)  # Simulate initialization time
        self.logger.info("mock_browser_initialized")
    
    async def navigate_to(self, url: str, county: str = "unknown") -> bool:
        """Mock navigation."""
        await asyncio.sleep(0.2)  # Simulate navigation time
        self.current_url = url
        self.logger.info("mock_navigation", url=url, county=county)
        return True
    
    async def fill_form(self, form_data: Dict[str, str], submit: bool = True) -> bool:
        """Mock form filling."""
        await asyncio.sleep(0.3)  # Simulate form filling time
        self.logger.info("mock_form_fill", form_data=list(form_data.keys()))
        return True
    
    async def extract_data(self, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Mock data extraction."""
        await asyncio.sleep(0.2)  # Simulate extraction time
        
        # Return mock data based on selectors
        extracted = {}
        for key, selector in selectors.items():
            extracted[key] = f"Mock data for {key} using selector {selector}"
        
        self.logger.info("mock_data_extracted", keys=list(extracted.keys()))
        return extracted
    
    async def download_file(self, url: str, file_path: Path, county: str = "unknown") -> bool:
        """Mock file download."""
        await asyncio.sleep(0.5)  # Simulate download time
        
        # Create mock file content
        mock_content = f"Mock document downloaded from {url}"
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(mock_content)
            
            self.logger.info("mock_file_downloaded", url=url, file_path=str(file_path))
            return True
        except Exception as e:
            self.logger.error("mock_download_failed", error=str(e))
            return False
    
    async def cleanup(self) -> None:
        """Mock cleanup."""
        self.logger.info("mock_browser_cleanup")
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()


class MockAgent(LoggerMixin):
    """Mock agent for complete workflow testing."""
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        self.config_override = config_override or {}
        self.parser = MockLLMParser()
        self.navigator = MockWebNavigator()
        self.current_execution = None
        self.logger.info("mock_agent_initialized")
    
    async def execute_instruction(
        self, 
        instruction: str,
        progress_callback: Optional[Any] = None
    ) -> ExecutionResult:
        """Execute instruction with mock implementation."""
        self.logger.info("mock_execution_started", instruction=instruction[:100])
        
        start_time = time.time()
        
        try:
            # Mock progress updates
            if progress_callback:
                progress_callback(ProgressUpdate(
                    job_id="mock_job_001",
                    current_step="parsing",
                    progress_percentage=10,
                    message="Parsing instruction..."
                ))
            
            # Parse instruction
            parsed = self.parser.parse_instruction(instruction)
            
            if progress_callback:
                progress_callback(ProgressUpdate(
                    job_id="mock_job_001",
                    current_step="initializing",
                    progress_percentage=20,
                    message="Initializing browser..."
                ))
            
            # Initialize navigator
            await self.navigator.initialize()
            
            # Mock document collection
            documents_collected = []
            tms_numbers = parsed.get("tms_numbers", [])
            county = parsed.get("county", "charleston")
            doc_types = parsed.get("document_types", ["property_card"])
            
            total_steps = len(tms_numbers) * len(doc_types)
            current_step = 0
            
            for tms in tms_numbers:
                for doc_type in doc_types:
                    current_step += 1
                    progress = 20 + (60 * current_step / total_steps)
                    
                    if progress_callback:
                        progress_callback(ProgressUpdate(
                            job_id="mock_job_001",
                            current_step=f"collecting_{doc_type}",
                            progress_percentage=progress,
                            message=f"Collecting {doc_type} for TMS {tms}..."
                        ))
                    
                    # Simulate document collection
                    await asyncio.sleep(0.2)
                    
                    # Create mock document
                    from .document_manager import DocumentManager
                    doc_manager = DocumentManager(Path("./mock_output"))
                    
                    mock_content = f"Mock {doc_type} document for TMS {tms} from {county} county".encode()
                    
                    try:
                        file_path = doc_manager.save_document(
                            content=mock_content,
                            tms_number=tms,
                            document_type=doc_type,
                            county=county
                        )
                        documents_collected.append(file_path)
                    except Exception as e:
                        self.logger.warning("mock_document_save_failed", error=str(e))
            
            if progress_callback:
                progress_callback(ProgressUpdate(
                    job_id="mock_job_001",
                    current_step="completed",
                    progress_percentage=100,
                    message="Execution completed successfully!"
                ))
            
            # Create result
            execution_time = time.time() - start_time
            
            result = ExecutionResult(
                plan_id="mock_plan_001",
                status=ExecutionStatus.SUCCESS,
                completed_steps=[f"step_{i:03d}" for i in range(1, total_steps + 1)],
                failed_steps=[],
                documents_collected=documents_collected,
                errors=[],
                execution_time=execution_time,
                metrics={
                    "tms_count": len(tms_numbers),
                    "document_count": len(documents_collected),
                    "county": county,
                    "mock_mode": True
                }
            )
            
            await self.navigator.cleanup()
            
            self.logger.info("mock_execution_completed", 
                           execution_time=execution_time,
                           documents_collected=len(documents_collected))
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            error_record = ErrorRecord(
                error_type=type(e).__name__,
                error_message=str(e),
                context={"instruction": instruction, "mock_mode": True}
            )
            
            result = ExecutionResult(
                plan_id="mock_plan_failed",
                status=ExecutionStatus.FAILED,
                errors=[error_record],
                execution_time=execution_time,
                metrics={"mock_mode": True}
            )
            
            self.logger.error("mock_execution_failed", error=str(e))
            return result


def create_mock_agent(config_override: Optional[Dict[str, Any]] = None) -> MockAgent:
    """Create a mock agent for testing."""
    return MockAgent(config_override)
