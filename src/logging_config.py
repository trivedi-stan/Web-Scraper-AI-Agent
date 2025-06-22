"""
Logging configuration for the AI Web Scraper Agent.

This module sets up structured logging using structlog with rich console output
and JSON file logging for production use.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    structlog = None
    STRUCTLOG_AVAILABLE = False

try:
    from rich.console import Console
    from rich.logging import RichHandler
    RICH_AVAILABLE = True
except ImportError:
    Console = None
    RichHandler = None
    RICH_AVAILABLE = False


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    enable_json_logs: bool = True,
    enable_console_logs: bool = True,
) -> None:
    """Set up structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (creates if doesn't exist)
        enable_json_logs: Whether to enable JSON file logging
        enable_console_logs: Whether to enable console logging
    """
    # Create log directory if specified
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Set up handlers
    handlers = []
    
    if enable_console_logs:
        if RICH_AVAILABLE:
            # Rich console handler for beautiful terminal output
            console = Console(stderr=True)
            rich_handler = RichHandler(
                console=console,
                show_time=True,
                show_path=True,
                markup=True,
                rich_tracebacks=True,
            )
            handlers.append(rich_handler)
        else:
            # Fallback to standard console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            handlers.append(console_handler)
    
    if enable_json_logs and log_dir:
        # JSON file handler for structured logs
        json_handler = logging.FileHandler(log_dir / "agent.json")
        if STRUCTLOG_AVAILABLE:
            json_handler.setFormatter(
                structlog.stdlib.ProcessorFormatter(
                    processor=structlog.dev.ConsoleRenderer(colors=False),
                )
            )
        else:
            json_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
        handlers.append(json_handler)
    
    # Configure structlog if available
    if STRUCTLOG_AVAILABLE:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    for handler in handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))


def get_logger(name: str):
    """Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger (structlog if available, otherwise standard logger)
    """
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self):
        """Get logger for this class."""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger
    
    def log_method_entry(self, method_name: str, **kwargs: Any) -> None:
        """Log method entry with parameters."""
        if STRUCTLOG_AVAILABLE:
            self.logger.debug(
                "method_entry",
                method=method_name,
                class_name=self.__class__.__name__,
                **kwargs
            )
        else:
            self.logger.debug(f"Entering {method_name} in {self.__class__.__name__}")
    
    def log_method_exit(self, method_name: str, **kwargs: Any) -> None:
        """Log method exit with results."""
        if STRUCTLOG_AVAILABLE:
            self.logger.debug(
                "method_exit",
                method=method_name,
                class_name=self.__class__.__name__,
                **kwargs
            )
        else:
            self.logger.debug(f"Exiting {method_name} in {self.__class__.__name__}")
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an error with context."""
        if STRUCTLOG_AVAILABLE:
            self.logger.error(
                "error_occurred",
                error_type=type(error).__name__,
                error_message=str(error),
                class_name=self.__class__.__name__,
                context=context or {},
                exc_info=True,
            )
        else:
            self.logger.error(f"Error in {self.__class__.__name__}: {str(error)}", exc_info=True)
    
    def log_performance(self, operation: str, duration: float, **kwargs: Any) -> None:
        """Log performance metrics."""
        if STRUCTLOG_AVAILABLE:
            self.logger.info(
                "performance_metric",
                operation=operation,
                duration_seconds=duration,
                class_name=self.__class__.__name__,
                **kwargs
            )
        else:
            self.logger.info(f"Performance: {operation} took {duration:.2f}s")


def log_workflow_step(
    step_id: str,
    step_type: str,
    status: str,
    duration: Optional[float] = None,
    **kwargs: Any
) -> None:
    """Log workflow step execution."""
    logger = get_logger("workflow")
    if STRUCTLOG_AVAILABLE:
        logger.info(
            "workflow_step",
            step_id=step_id,
            step_type=step_type,
            status=status,
            duration_seconds=duration,
            **kwargs
        )
    else:
        logger.info(f"Workflow step {step_id} ({step_type}): {status}")


def log_document_collection(
    tms_number: str,
    county: str,
    document_type: str,
    status: str,
    file_path: Optional[str] = None,
    **kwargs: Any
) -> None:
    """Log document collection events."""
    logger = get_logger("documents")
    if STRUCTLOG_AVAILABLE:
        logger.info(
            "document_collection",
            tms_number=tms_number,
            county=county,
            document_type=document_type,
            status=status,
            file_path=file_path,
            **kwargs
        )
    else:
        logger.info(f"Document collection: {document_type} for TMS {tms_number} - {status}")


def log_error_recovery(
    error_type: str,
    recovery_action: str,
    success: bool,
    attempt_number: int,
    **kwargs: Any
) -> None:
    """Log error recovery attempts."""
    logger = get_logger("recovery")
    if STRUCTLOG_AVAILABLE:
        logger.info(
            "error_recovery",
            error_type=error_type,
            recovery_action=recovery_action,
            success=success,
            attempt_number=attempt_number,
            **kwargs
        )
    else:
        logger.info(f"Error recovery: {recovery_action} for {error_type} - {'Success' if success else 'Failed'}")


def log_rate_limit(
    county: str,
    action: str,
    delay_seconds: float,
    **kwargs: Any
) -> None:
    """Log rate limiting actions."""
    logger = get_logger("rate_limit")
    if STRUCTLOG_AVAILABLE:
        logger.debug(
            "rate_limit_applied",
            county=county,
            action=action,
            delay_seconds=delay_seconds,
            **kwargs
        )
    else:
        logger.debug(f"Rate limit: {action} for {county} - waiting {delay_seconds}s")


def log_instruction_parsing(
    instruction: str,
    parsed_county: str,
    tms_count: int,
    document_types: list,
    success: bool,
    **kwargs: Any
) -> None:
    """Log instruction parsing results."""
    logger = get_logger("parser")
    if STRUCTLOG_AVAILABLE:
        logger.info(
            "instruction_parsed",
            instruction_length=len(instruction),
            parsed_county=parsed_county,
            tms_count=tms_count,
            document_types=document_types,
            success=success,
            **kwargs
        )
    else:
        logger.info(f"Instruction parsing: {parsed_county} county, {tms_count} TMS - {'Success' if success else 'Failed'}")
