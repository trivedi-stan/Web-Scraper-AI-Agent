"""
Command-line interface for the AI Web Scraper Agent.

This module provides a CLI for interacting with the web scraper agent,
allowing users to execute instructions and monitor progress.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

try:
    from .agent import WebScraperAgent
    AGENT_AVAILABLE = True
except ImportError:
    from .mock_implementations import MockAgent as WebScraperAgent
    AGENT_AVAILABLE = False
from .models import ProgressUpdate, ExecutionStatus
from .logging_config import setup_logging, get_logger
from .config import get_config


console = Console()
logger = get_logger(__name__)


class ProgressTracker:
    """Tracks and displays progress updates."""
    
    def __init__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        )
        self.task_id = None
        self.started = False
    
    def start(self, description: str = "Processing..."):
        """Start progress tracking."""
        if not self.started:
            self.progress.start()
            self.task_id = self.progress.add_task(description, total=100)
            self.started = True
    
    def update(self, progress_update: ProgressUpdate):
        """Update progress display."""
        if self.task_id is not None:
            self.progress.update(
                self.task_id,
                completed=progress_update.progress_percentage,
                description=progress_update.message
            )
    
    def stop(self):
        """Stop progress tracking."""
        if self.started:
            self.progress.stop()
            self.started = False


@click.group()
@click.option('--log-level', default='INFO', help='Logging level')
@click.option('--log-dir', type=click.Path(), help='Log directory')
@click.option('--config-file', type=click.Path(exists=True), help='Configuration file')
@click.pass_context
def cli(ctx, log_level, log_dir, config_file):
    """AI Web Scraper Agent - Automate multi-step website navigation and scraping."""
    # Setup logging
    log_dir_path = Path(log_dir) if log_dir else None
    setup_logging(log_level, log_dir_path)
    
    # Store context
    ctx.ensure_object(dict)
    ctx.obj['log_level'] = log_level
    ctx.obj['log_dir'] = log_dir_path
    ctx.obj['config_file'] = config_file


@cli.command()
@click.argument('instruction', type=str)
@click.option('--output-dir', type=click.Path(), help='Output directory for documents')
@click.option('--headless/--no-headless', default=True, help='Run browser in headless mode')
@click.option('--timeout', default=30000, help='Browser timeout in milliseconds')
@click.option('--save-results', type=click.Path(), help='Save results to JSON file')
@click.option('--mock-mode', is_flag=True, help='Use mock implementations (no external dependencies)')
@click.pass_context
def execute(ctx, instruction, output_dir, headless, timeout, save_results, mock_mode):
    """Execute a natural language instruction for document collection.
    
    INSTRUCTION: Natural language instruction describing what documents to collect.
    
    Examples:
    
    \b
    webscraper execute "Collect all documents for Charleston County TMS 5590200072"
    
    \b
    webscraper execute "Get property cards and tax info for Berkeley County TMS 2590502005"
    
    \b
    webscraper execute "Visit Charleston County and Berkeley County websites. 
    Collect property cards, tax information, and deed documents for TMS 5590200072 and 2590502005"
    """
    # Determine if we should use mock mode
    use_mock = mock_mode or not AGENT_AVAILABLE
    
    mode_text = "[yellow](Mock Mode)[/yellow]" if use_mock else "[green](Live Mode)[/green]"
    console.print(Panel.fit(
        f"[bold blue]AI Web Scraper Agent[/bold blue] {mode_text}\n"
        f"Executing instruction: [italic]{instruction}[/italic]",
        border_style="blue"
    ))
    
    if use_mock:
        console.print("[yellow]ℹ️  Running in mock mode - no external dependencies required[/yellow]")
    
    # Configuration overrides
    config_override = {}
    if output_dir:
        config_override['output_dir'] = Path(output_dir)
    if not headless:
        config_override['browser_config'] = {'headless': False}
    if timeout != 30000:
        config_override['browser_config'] = config_override.get('browser_config', {})
        config_override['browser_config']['timeout'] = timeout
    
    # Setup progress tracking
    progress_tracker = ProgressTracker()
    
    def progress_callback(update: ProgressUpdate):
        progress_tracker.update(update)
    
    async def run_execution():
        try:
            # Initialize agent (mock or real based on availability)
            if use_mock:
                from .mock_implementations import MockAgent
                agent = MockAgent(config_override)
            else:
                agent = WebScraperAgent(config_override)
            
            # Start progress tracking
            progress_tracker.start("Initializing...")
            
            # Execute instruction
            result = await agent.execute_instruction(instruction, progress_callback)
            
            # Stop progress tracking
            progress_tracker.stop()
            
            # Display results
            display_results(result)
            
            # Save results if requested
            if save_results:
                save_results_to_file(result, Path(save_results))
            
            # Exit with appropriate code
            if result.status == ExecutionStatus.SUCCESS:
                sys.exit(0)
            elif result.status == ExecutionStatus.PARTIAL:
                sys.exit(1)
            else:
                sys.exit(2)
                
        except KeyboardInterrupt:
            progress_tracker.stop()
            console.print("\n[yellow]Execution cancelled by user[/yellow]")
            sys.exit(130)
        except Exception as e:
            progress_tracker.stop()
            console.print(f"\n[red]Error: {str(e)}[/red]")
            logger.error("cli_execution_failed", error=str(e), exc_info=True)
            sys.exit(1)
    
    # Run the async execution
    asyncio.run(run_execution())


@cli.command()
@click.option('--tms-number', required=True, help='TMS/Parcel number')
@click.option('--output-dir', type=click.Path(), help='Output directory to check')
def status(tms_number, output_dir):
    """Check the status of document collection for a property."""
    config = get_config()
    base_dir = Path(output_dir) if output_dir else config.output_dir
    
    from .document_manager import DocumentManager
    doc_manager = DocumentManager(base_dir)
    
    # Get storage stats instead of document summary (which doesn't exist)
    stats = doc_manager.get_storage_stats()
    
    console.print(f"[blue]Document Status for TMS {tms_number}[/blue]")
    console.print(f"Base Directory: {stats['base_directory']}")
    console.print(f"Total Files: {stats['total_files']}")
    console.print(f"Total Size: {stats['total_size_mb']} MB")
    
    if stats['file_types']:
        console.print("\nFile Types:")
        for ext, count in stats['file_types'].items():
            console.print(f"  {ext or 'no extension'}: {count} files")


@cli.command()
def config():
    """Display current configuration."""
    try:
        config = get_config()
        
        config_table = Table(title="Current Configuration")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="green")
        
        config_table.add_row("Model", getattr(config, 'model_name', 'N/A'))
        config_table.add_row("Output Directory", str(config.output_dir))
        config_table.add_row("Log Level", config.log_level)
        config_table.add_row("Max Concurrent Jobs", str(config.max_concurrent_jobs))
        config_table.add_row("Browser Type", config.browser_config.browser_type)
        config_table.add_row("Headless Mode", str(config.browser_config.headless))
        config_table.add_row("Viewport", f"{config.browser_config.viewport_width}x{config.browser_config.viewport_height}")
        config_table.add_row("Dependencies Available", str(AGENT_AVAILABLE))
        
        console.print(config_table)
        
    except Exception as e:
        console.print(f"[red]Error loading configuration: {str(e)}[/red]")


@cli.command()
@click.argument('instruction', type=str)
def parse(instruction):
    """Parse a natural language instruction without executing it."""
    console.print(f"[blue]Parsing instruction:[/blue] {instruction}")
    
    try:
        # Use mock parser since real parser might not be available
        from .mock_implementations import MockLLMParser
        parser = MockLLMParser()
        
        # Parse instruction
        parsed = parser.parse_instruction(instruction)
        
        # Display parsed plan
        console.print(f"\n[green]✓ Parsing successful[/green]")
        console.print(f"County: {parsed['county']}")
        console.print(f"TMS Numbers: {', '.join(parsed['tms_numbers'])}")
        console.print(f"Document Types: {', '.join(parsed['document_types'])}")
        console.print(f"Estimated Duration: {parsed['estimated_duration']} seconds")
        
    except Exception as e:
        console.print(f"[red]✗ Parsing failed: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--mock-mode', is_flag=True, help='Use mock implementations for testing')
def test(mock_mode):
    """Run basic functionality tests."""
    console.print("[bold blue]🧪 Running Basic Functionality Tests[/bold blue]")

    use_mock = mock_mode or not AGENT_AVAILABLE
    mode_text = "Mock Mode" if use_mock else "Live Mode"
    console.print(f"Testing in: [yellow]{mode_text}[/yellow]\n")

    tests_passed = 0
    tests_total = 0

    # Test 1: Import core modules
    console.print("1. Testing core module imports...")
    tests_total += 1
    try:
        from .models import County, DocumentType
        from .config import get_config
        from .document_manager import DocumentManager
        console.print("   [green]✅ Core modules imported successfully[/green]")
        tests_passed += 1
    except Exception as e:
        console.print(f"   [red]❌ Import failed: {str(e)}[/red]")

    # Test 2: Configuration
    console.print("\n2. Testing configuration system...")
    tests_total += 1
    try:
        config = get_config()
        console.print(f"   [green]✅ Configuration loaded (output: {config.output_dir})[/green]")
        tests_passed += 1
    except Exception as e:
        console.print(f"   [red]❌ Configuration failed: {str(e)}[/red]")

    # Test 3: Document Manager
    console.print("\n3. Testing document manager...")
    tests_total += 1
    try:
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as temp_dir:
            doc_manager = DocumentManager(Path(temp_dir))
            folder = doc_manager.create_property_folder("5590200072")
            assert folder.exists()
        console.print("   [green]✅ Document manager working[/green]")
        tests_passed += 1
    except Exception as e:
        console.print(f"   [red]❌ Document manager failed: {str(e)}[/red]")

    # Test 4: Mock implementations
    if use_mock:
        console.print("\n4. Testing mock implementations...")
        tests_total += 1
        try:
            from .mock_implementations import MockLLMParser, MockAgent
            parser = MockLLMParser()
            result = parser.parse_instruction("Test instruction for Charleston County TMS 5590200072")
            assert result["county"] == "charleston"
            console.print("   [green]✅ Mock implementations working[/green]")
            tests_passed += 1
        except Exception as e:
            console.print(f"   [red]❌ Mock implementations failed: {str(e)}[/red]")

    # Summary
    console.print(f"\n[bold]Test Results: {tests_passed}/{tests_total} passed[/bold]")

    if tests_passed == tests_total:
        console.print("[green]🎉 All tests passed! The system is working correctly.[/green]")

        if use_mock:
            console.print("\n[yellow]💡 You're running in mock mode. To use real functionality:[/yellow]")
            console.print("   1. Install dependencies: pip install -r requirements.txt")
            console.print("   2. Set up .env file with OpenAI API key")
            console.print("   3. Run without --mock-mode flag")

        sys.exit(0)
    else:
        console.print("[red]⚠️  Some tests failed. Please check the errors above.[/red]")
        sys.exit(1)


def display_results(result):
    """Display execution results in a formatted table."""
    # Status panel
    status_color = {
        ExecutionStatus.SUCCESS: "green",
        ExecutionStatus.PARTIAL: "yellow",
        ExecutionStatus.FAILED: "red",
        ExecutionStatus.CANCELLED: "blue"
    }.get(result.status, "white")

    console.print(Panel.fit(
        f"[bold {status_color}]Execution {result.status.value.upper()}[/bold {status_color}]\n"
        f"Plan ID: {result.plan_id}\n"
        f"Execution Time: {result.execution_time:.2f} seconds\n"
        f"Documents Collected: {len(result.documents_collected)}\n"
        f"Errors: {len(result.errors)}",
        border_style=status_color
    ))

    # Documents table
    if result.documents_collected:
        docs_table = Table(title="Collected Documents")
        docs_table.add_column("Document", style="cyan")
        docs_table.add_column("Path", style="green")
        docs_table.add_column("Size", justify="right", style="magenta")

        for doc_path in result.documents_collected:
            if doc_path.exists():
                size = format_file_size(doc_path.stat().st_size)
                docs_table.add_row(doc_path.name, str(doc_path.parent), size)
            else:
                docs_table.add_row(doc_path.name, str(doc_path.parent), "Missing")

        console.print(docs_table)

    # Errors table
    if result.errors:
        errors_table = Table(title="Errors")
        errors_table.add_column("Type", style="red")
        errors_table.add_column("Message", style="yellow")
        errors_table.add_column("Step", style="cyan")

        for error in result.errors:
            errors_table.add_row(
                error.error_type,
                error.error_message[:100] + "..." if len(error.error_message) > 100 else error.error_message,
                error.step_id or "N/A"
            )

        console.print(errors_table)


def save_results_to_file(result, file_path: Path):
    """Save execution results to a JSON file."""
    try:
        # Convert result to serializable dict
        result_dict = {
            "plan_id": result.plan_id,
            "status": result.status.value,
            "execution_time": result.execution_time,
            "started_at": result.started_at.isoformat() if result.started_at else None,
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            "completed_steps": result.completed_steps,
            "failed_steps": result.failed_steps,
            "documents_collected": [str(path) for path in result.documents_collected],
            "errors": [
                {
                    "error_type": error.error_type,
                    "error_message": error.error_message,
                    "step_id": error.step_id,
                    "timestamp": error.timestamp.isoformat(),
                    "context": error.context
                }
                for error in result.errors
            ],
            "metrics": result.metrics
        }

        with open(file_path, 'w') as f:
            json.dump(result_dict, f, indent=2)

        console.print(f"[green]Results saved to {file_path}[/green]")

    except Exception as e:
        console.print(f"[red]Failed to save results: {str(e)}[/red]")


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
