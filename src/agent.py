"""
Main AI Web Scraper Agent orchestrator.

This module coordinates all components to execute document collection workflows
based on natural language instructions.
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

from .models import ExecutionResult, ExecutionStatus, ErrorRecord, ProgressUpdate
from .parser import InstructionParser
from .navigator import WebNavigator
from .document_manager import DocumentManager
from .config import get_config
from .logging_config import LoggerMixin


class WebScraperAgent(LoggerMixin):
    """Main orchestrator for the AI Web Scraper Agent."""
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """Initialize the web scraper agent.
        
        Args:
            config_override: Optional configuration overrides
        """
        self.config = get_config()
        
        # Apply configuration overrides
        if config_override:
            for key, value in config_override.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
        
        # Initialize components
        self.parser = InstructionParser(self.config)
        self.navigator = WebNavigator(self.config)
        self.document_manager = DocumentManager(self.config.output_dir)
        
        # Execution state
        self.current_execution = None
        self.is_running = False
        
        self.logger.info("web_scraper_agent_initialized", 
                        output_dir=str(self.config.output_dir))
    
    async def execute_instruction(
        self, 
        instruction: str,
        progress_callback: Optional[Callable[[ProgressUpdate], None]] = None
    ) -> ExecutionResult:
        """Execute a natural language instruction.
        
        Args:
            instruction: Natural language instruction
            progress_callback: Optional callback for progress updates
            
        Returns:
            ExecutionResult with execution details
        """
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = time.time()
        
        self.logger.info("execution_started", 
                        execution_id=execution_id,
                        instruction=instruction[:100])
        
        # Initialize result
        result = ExecutionResult(
            plan_id=execution_id,
            status=ExecutionStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        self.current_execution = result
        self.is_running = True
        
        try:
            # Step 1: Parse instruction
            if progress_callback:
                progress_callback(ProgressUpdate(
                    job_id=execution_id,
                    current_step="parsing",
                    progress_percentage=10,
                    message="Parsing instruction..."
                ))
            
            execution_plan = self.parser.parse_instruction(instruction)
            
            # Step 2: Initialize browser
            if progress_callback:
                progress_callback(ProgressUpdate(
                    job_id=execution_id,
                    current_step="initializing",
                    progress_percentage=20,
                    message="Initializing browser..."
                ))
            
            await self.navigator.initialize()
            
            # Step 3: Execute workflow steps
            total_steps = len(execution_plan.workflow_steps)
            completed_steps = []
            failed_steps = []
            documents_collected = []
            errors = []
            
            for i, step in enumerate(execution_plan.workflow_steps):
                if not self.is_running:
                    break
                
                step_progress = 20 + (70 * (i + 1) / total_steps)
                
                if progress_callback:
                    progress_callback(ProgressUpdate(
                        job_id=execution_id,
                        current_step=step.step_type.value,
                        progress_percentage=step_progress,
                        message=f"Executing {step.step_type.value}: {step.expected_outcome}"
                    ))
                
                try:
                    step_result = await self._execute_workflow_step(step, execution_plan)
                    
                    if step_result.get('success', False):
                        completed_steps.append(step.step_id)
                        
                        # Collect documents if this step produced any
                        if 'documents' in step_result:
                            documents_collected.extend(step_result['documents'])
                    else:
                        failed_steps.append(step.step_id)
                        if 'error' in step_result:
                            errors.append(ErrorRecord(
                                error_type="StepExecutionError",
                                error_message=step_result['error'],
                                step_id=step.step_id
                            ))
                
                except Exception as e:
                    failed_steps.append(step.step_id)
                    errors.append(ErrorRecord(
                        error_type=type(e).__name__,
                        error_message=str(e),
                        step_id=step.step_id
                    ))
                    
                    self.logger.error("step_execution_failed", 
                                    step_id=step.step_id,
                                    error=str(e))
            
            # Step 4: Finalize
            if progress_callback:
                progress_callback(ProgressUpdate(
                    job_id=execution_id,
                    current_step="finalizing",
                    progress_percentage=95,
                    message="Finalizing execution..."
                ))
            
            # Determine final status
            if len(failed_steps) == 0:
                final_status = ExecutionStatus.SUCCESS
            elif len(completed_steps) > 0:
                final_status = ExecutionStatus.PARTIAL
            else:
                final_status = ExecutionStatus.FAILED
            
            # Update result
            execution_time = time.time() - start_time
            result.status = final_status
            result.completed_steps = completed_steps
            result.failed_steps = failed_steps
            result.documents_collected = documents_collected
            result.errors = errors
            result.execution_time = execution_time
            result.completed_at = datetime.now()
            result.metrics = {
                "total_steps": total_steps,
                "success_rate": len(completed_steps) / total_steps if total_steps > 0 else 0,
                "documents_count": len(documents_collected),
                "county": execution_plan.county.value,
                "tms_count": len(execution_plan.tms_numbers)
            }
            
            # Create execution summary
            try:
                summary_file = self.document_manager.create_execution_summary(
                    execution_id, result.metrics, documents_collected
                )
                self.logger.info("execution_summary_created", summary_file=str(summary_file))
            except Exception as e:
                self.logger.warning("summary_creation_failed", error=str(e))
            
            if progress_callback:
                progress_callback(ProgressUpdate(
                    job_id=execution_id,
                    current_step="completed",
                    progress_percentage=100,
                    message=f"Execution completed: {final_status.value}"
                ))
            
            self.logger.info("execution_completed",
                           execution_id=execution_id,
                           status=final_status.value,
                           execution_time=execution_time,
                           documents_collected=len(documents_collected))
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            error_record = ErrorRecord(
                error_type=type(e).__name__,
                error_message=str(e),
                context={"instruction": instruction}
            )
            
            result.status = ExecutionStatus.FAILED
            result.errors = [error_record]
            result.execution_time = execution_time
            result.completed_at = datetime.now()
            
            self.logger.error("execution_failed",
                            execution_id=execution_id,
                            error=str(e),
                            execution_time=execution_time)
            
            return result
            
        finally:
            self.is_running = False
            self.current_execution = None
            
            # Cleanup browser
            try:
                await self.navigator.cleanup()
            except Exception as e:
                self.logger.warning("cleanup_failed", error=str(e))
    
    async def _execute_workflow_step(self, step, execution_plan) -> Dict[str, Any]:
        """Execute a single workflow step.
        
        Args:
            step: WorkflowStep to execute
            execution_plan: Complete execution plan for context
            
        Returns:
            Dictionary with execution results
        """
        self.logger.info("executing_step", 
                        step_id=step.step_id,
                        step_type=step.step_type.value)
        
        try:
            if step.step_type.value == "navigate":
                return await self._execute_navigate_step(step, execution_plan)
            elif step.step_type.value == "search":
                return await self._execute_search_step(step, execution_plan)
            elif step.step_type.value == "extract":
                return await self._execute_extract_step(step, execution_plan)
            elif step.step_type.value == "download":
                return await self._execute_download_step(step, execution_plan)
            elif step.step_type.value == "organize":
                return await self._execute_organize_step(step, execution_plan)
            else:
                return {"success": False, "error": f"Unknown step type: {step.step_type.value}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_navigate_step(self, step, execution_plan) -> Dict[str, Any]:
        """Execute navigation step."""
        success = await self.navigator.navigate_to(
            step.target_url, 
            execution_plan.county.value
        )
        return {"success": success}
    
    async def _execute_search_step(self, step, execution_plan) -> Dict[str, Any]:
        """Execute search step."""
        tms_number = step.parameters.get("tms_number", "")
        
        # Fill search form
        form_data = {}
        if "tms_input" in step.selectors:
            form_data[step.selectors["tms_input"]] = tms_number
        elif "search_input" in step.selectors:
            form_data[step.selectors["search_input"]] = tms_number
        
        success = await self.navigator.fill_form(form_data, submit=True)
        return {"success": success}
    
    async def _execute_extract_step(self, step, execution_plan) -> Dict[str, Any]:
        """Execute data extraction step."""
        extracted_data = await self.navigator.extract_data(step.selectors)
        return {"success": True, "data": extracted_data}
    
    async def _execute_download_step(self, step, execution_plan) -> Dict[str, Any]:
        """Execute document download step."""
        # This is a placeholder - in real implementation, this would:
        # 1. Find download links on the page
        # 2. Download documents using navigator.download_file()
        # 3. Save documents using document_manager.save_document()
        
        # For now, return success without actual download
        return {"success": True, "documents": []}
    
    async def _execute_organize_step(self, step, execution_plan) -> Dict[str, Any]:
        """Execute document organization step."""
        # Clean up empty folders
        removed_count = self.document_manager.cleanup_empty_folders()
        return {"success": True, "folders_cleaned": removed_count}
    
    def cancel_execution(self) -> None:
        """Cancel the current execution."""
        if self.is_running:
            self.is_running = False
            if self.current_execution:
                self.current_execution.status = ExecutionStatus.CANCELLED
            
            self.logger.info("execution_cancelled")
    
    def get_execution_status(self) -> Optional[ExecutionResult]:
        """Get the current execution status.
        
        Returns:
            Current ExecutionResult or None if not running
        """
        return self.current_execution
