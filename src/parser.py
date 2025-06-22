"""
Instruction parser for the AI Web Scraper Agent.

This module handles parsing natural language instructions into structured execution plans
using LLM integration (OpenAI GPT-4) with fallback to regex-based parsing.
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime

from .models import ExecutionPlan, WorkflowStep, WorkflowStepType, County, DocumentType
from .logging_config import LoggerMixin


class InstructionParser(LoggerMixin):
    """Parses natural language instructions into structured execution plans."""
    
    def __init__(self, config=None):
        """Initialize the instruction parser.
        
        Args:
            config: Configuration object with LLM settings
        """
        self.config = config
        self.llm_available = self._check_llm_availability()
        self.logger.info("instruction_parser_initialized", llm_available=self.llm_available)
    
    def _check_llm_availability(self) -> bool:
        """Check if LLM integration is available."""
        try:
            # Check for OpenAI API key and library
            import os
            from openai import OpenAI
            
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key and api_key != "your_openai_api_key_here":
                return True
            return False
        except ImportError:
            return False
    
    def parse_instruction(self, instruction: str) -> ExecutionPlan:
        """Parse natural language instruction into execution plan.
        
        Args:
            instruction: Natural language instruction
            
        Returns:
            ExecutionPlan with parsed workflow steps
        """
        self.logger.info("parsing_instruction", 
                        instruction_length=len(instruction),
                        llm_available=self.llm_available)
        
        if self.llm_available:
            try:
                return self._parse_with_llm(instruction)
            except Exception as e:
                self.logger.warning("llm_parsing_failed", error=str(e))
                return self._parse_with_regex(instruction)
        else:
            return self._parse_with_regex(instruction)
    
    def _parse_with_llm(self, instruction: str) -> ExecutionPlan:
        """Parse instruction using LLM (OpenAI GPT-4).
        
        Args:
            instruction: Natural language instruction
            
        Returns:
            ExecutionPlan with LLM-generated workflow
        """
        # This would contain the actual LLM integration
        # For now, fall back to regex parsing
        self.logger.info("using_llm_parsing")
        
        # TODO: Implement actual LLM parsing with OpenAI API
        # This is a placeholder that falls back to regex parsing
        return self._parse_with_regex(instruction)
    
    def _parse_with_regex(self, instruction: str) -> ExecutionPlan:
        """Parse instruction using regex patterns (fallback method).
        
        Args:
            instruction: Natural language instruction
            
        Returns:
            ExecutionPlan with regex-parsed workflow
        """
        self.logger.info("using_regex_parsing")
        
        # Extract county information
        county = self._extract_county(instruction)
        
        # Extract TMS numbers
        tms_numbers = self._extract_tms_numbers(instruction)
        
        # Extract document types
        document_types = self._extract_document_types(instruction)
        
        # Generate workflow steps
        workflow_steps = self._generate_workflow_steps(county, tms_numbers, document_types)
        
        # Create execution plan
        plan = ExecutionPlan(
            instruction_id=f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            county=county,
            tms_numbers=tms_numbers,
            document_types=document_types,
            workflow_steps=workflow_steps,
            estimated_duration=len(tms_numbers) * len(document_types) * 180,  # 3 minutes per doc
            priority=1
        )
        
        self.logger.info("instruction_parsed",
                        county=county.value,
                        tms_count=len(tms_numbers),
                        doc_types=[dt.value for dt in document_types],
                        workflow_steps=len(workflow_steps))
        
        return plan
    
    def _extract_county(self, instruction: str) -> County:
        """Extract county from instruction text."""
        instruction_lower = instruction.lower()
        
        if 'berkeley' in instruction_lower:
            return County.BERKELEY
        elif 'charleston' in instruction_lower:
            return County.CHARLESTON
        else:
            # Default to Charleston if not specified
            return County.CHARLESTON
    
    def _extract_tms_numbers(self, instruction: str) -> List[str]:
        """Extract TMS numbers from instruction text."""
        # Pattern for 10-digit TMS numbers
        tms_pattern = r'\b\d{10}\b'
        tms_numbers = re.findall(tms_pattern, instruction)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tms = []
        for tms in tms_numbers:
            if tms not in seen:
                seen.add(tms)
                unique_tms.append(tms)
        
        return unique_tms
    
    def _extract_document_types(self, instruction: str) -> List[DocumentType]:
        """Extract document types from instruction text."""
        instruction_lower = instruction.lower()
        document_types = []
        
        # Check for specific document types
        if re.search(r'property\s+card', instruction_lower):
            document_types.append(DocumentType.PROPERTY_CARD)
        
        if re.search(r'tax\s+info|tax\s+information', instruction_lower):
            document_types.append(DocumentType.TAX_INFO)
        
        if re.search(r'tax\s+bill', instruction_lower):
            document_types.append(DocumentType.TAX_BILL)
        
        if re.search(r'tax\s+receipt', instruction_lower):
            document_types.append(DocumentType.TAX_RECEIPT)
        
        if re.search(r'deed', instruction_lower):
            document_types.append(DocumentType.DEED)
        
        # If no specific types mentioned, default to common documents
        if not document_types:
            if 'all' in instruction_lower or 'documents' in instruction_lower:
                document_types = [
                    DocumentType.PROPERTY_CARD,
                    DocumentType.TAX_INFO,
                    DocumentType.DEED
                ]
            else:
                # Default to property card
                document_types = [DocumentType.PROPERTY_CARD]
        
        return document_types
    
    def _generate_workflow_steps(
        self, 
        county: County, 
        tms_numbers: List[str], 
        document_types: List[DocumentType]
    ) -> List[WorkflowStep]:
        """Generate workflow steps for the execution plan."""
        steps = []
        step_counter = 1
        
        from .config import get_county_config
        county_config = get_county_config(county.value)
        
        for tms_number in tms_numbers:
            for doc_type in document_types:
                # Navigation step
                nav_step = WorkflowStep(
                    step_id=f"step_{step_counter:03d}",
                    step_type=WorkflowStepType.NAVIGATE,
                    target_url=county_config.search_url,
                    parameters={"tms_number": tms_number, "document_type": doc_type.value},
                    expected_outcome=f"Navigate to {county.value} search page"
                )
                steps.append(nav_step)
                step_counter += 1
                
                # Search step
                search_step = WorkflowStep(
                    step_id=f"step_{step_counter:03d}",
                    step_type=WorkflowStepType.SEARCH,
                    target_url=county_config.search_url,
                    parameters={"tms_number": tms_number},
                    selectors=county_config.selectors,
                    expected_outcome=f"Search for TMS {tms_number}"
                )
                steps.append(search_step)
                step_counter += 1
                
                # Extract step
                extract_step = WorkflowStep(
                    step_id=f"step_{step_counter:03d}",
                    step_type=WorkflowStepType.EXTRACT,
                    target_url="",
                    parameters={"document_type": doc_type.value},
                    selectors=county_config.selectors,
                    expected_outcome=f"Extract {doc_type.value} information"
                )
                steps.append(extract_step)
                step_counter += 1
                
                # Download step
                download_step = WorkflowStep(
                    step_id=f"step_{step_counter:03d}",
                    step_type=WorkflowStepType.DOWNLOAD,
                    target_url="",
                    parameters={
                        "tms_number": tms_number,
                        "document_type": doc_type.value,
                        "county": county.value
                    },
                    expected_outcome=f"Download {doc_type.value} for TMS {tms_number}"
                )
                steps.append(download_step)
                step_counter += 1
        
        # Final organization step
        organize_step = WorkflowStep(
            step_id=f"step_{step_counter:03d}",
            step_type=WorkflowStepType.ORGANIZE,
            target_url="",
            parameters={"tms_numbers": tms_numbers},
            expected_outcome="Organize collected documents"
        )
        steps.append(organize_step)
        
        return steps
