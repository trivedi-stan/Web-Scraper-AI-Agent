"""
Data models for the AI Web Scraper Agent.

This module defines the core data structures used throughout the application,
including execution plans, workflow steps, and results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class County(str, Enum):
    """Supported counties for document collection."""
    CHARLESTON = "charleston"
    BERKELEY = "berkeley"


class DocumentType(str, Enum):
    """Types of documents that can be collected."""
    PROPERTY_CARD = "property_card"
    TAX_INFO = "tax_info"
    TAX_BILL = "tax_bill"
    TAX_RECEIPT = "tax_receipt"
    DEED = "deed"


class WorkflowStepType(str, Enum):
    """Types of workflow steps."""
    NAVIGATE = "navigate"
    SEARCH = "search"
    EXTRACT = "extract"
    DOWNLOAD = "download"
    ORGANIZE = "organize"


class ExecutionStatus(str, Enum):
    """Execution status values."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""
    step_id: str
    step_type: WorkflowStepType
    target_url: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    selectors: Dict[str, str] = field(default_factory=dict)
    expected_outcome: str = ""
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 30000  # milliseconds
    
    def __post_init__(self):
        if isinstance(self.step_type, str):
            self.step_type = WorkflowStepType(self.step_type)


@dataclass
class ExecutionPlan:
    """Represents a complete execution plan for document collection."""
    instruction_id: str
    county: County
    tms_numbers: List[str]
    document_types: List[DocumentType]
    workflow_steps: List[WorkflowStep]
    estimated_duration: int = 0  # seconds
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if isinstance(self.county, str):
            self.county = County(self.county)
        
        self.document_types = [
            DocumentType(dt) if isinstance(dt, str) else dt 
            for dt in self.document_types
        ]


@dataclass
class ErrorRecord:
    """Represents an error that occurred during execution."""
    error_type: str
    error_message: str
    step_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    resolved: bool = False


@dataclass
class ExecutionResult:
    """Represents the result of executing a plan."""
    plan_id: str
    status: ExecutionStatus
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    documents_collected: List[Path] = field(default_factory=list)
    errors: List[ErrorRecord] = field(default_factory=list)
    execution_time: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = ExecutionStatus(self.status)


class BrowserConfig(BaseModel):
    """Configuration for browser automation."""
    headless: bool = True
    browser_type: str = "chromium"
    viewport_width: int = 1920
    viewport_height: int = 1080
    timeout: int = 30000
    user_agent: Optional[str] = None
    proxy: Optional[str] = None


class CountyConfig(BaseModel):
    """Configuration for a specific county's websites."""
    name: str
    base_url: str
    search_url: str
    deeds_url: Optional[str] = None
    tax_url: Optional[str] = None
    selectors: Dict[str, str] = Field(default_factory=dict)
    rate_limits: Dict[str, int] = Field(default_factory=dict)
    special_handling: Dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Main configuration for the web scraper agent."""
    openai_api_key: str
    model_name: str = "gpt-4-turbo-preview"
    output_dir: Path = Path("./output")
    log_level: str = "INFO"
    max_concurrent_jobs: int = 3
    browser_config: BrowserConfig = Field(default_factory=BrowserConfig)
    counties: Dict[str, CountyConfig] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True


@dataclass
class ValidationResult:
    """Result of document validation."""
    is_valid: bool
    file_type: str
    file_size: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ProgressUpdate:
    """Progress update for real-time tracking."""
    job_id: str
    current_step: str
    progress_percentage: float
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
