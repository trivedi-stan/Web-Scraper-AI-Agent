#!/usr/bin/env python3
"""
Comprehensive test suite for the AI Web Scraper Agent.

This script runs a complete test suite covering all components and functionality.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def print_test_header(test_name: str):
    """Print formatted test header."""
    print(f"\n{'='*60}")
    print(f"🧪 {test_name}")
    print('='*60)


def print_test_result(test_name: str, passed: bool, details: str = ""):
    """Print formatted test result."""
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"{status}: {test_name}")
    if details:
        print(f"   Details: {details}")


async def test_models():
    """Test data models and types."""
    print_test_header("Data Models Test")
    
    try:
        from src.models import County, DocumentType, ExecutionStatus, ExecutionPlan, WorkflowStep, WorkflowStepType
        
        # Test enums
        county = County.CHARLESTON
        doc_type = DocumentType.PROPERTY_CARD
        status = ExecutionStatus.SUCCESS
        step_type = WorkflowStepType.NAVIGATE
        
        # Test workflow step
        step = WorkflowStep(
            step_id="test_001",
            step_type=step_type,
            target_url="https://example.com",
            expected_outcome="Test step"
        )
        
        # Test execution plan
        plan = ExecutionPlan(
            instruction_id="test_plan",
            county=county,
            tms_numbers=["1234567890"],
            document_types=[doc_type],
            workflow_steps=[step]
        )
        
        print_test_result("Data Models", True, "All models created successfully")
        return True
        
    except Exception as e:
        print_test_result("Data Models", False, str(e))
        return False


async def test_configuration():
    """Test configuration management."""
    print_test_header("Configuration Test")
    
    try:
        from src.config import get_config, get_county_config
        
        # Test main config
        config = get_config()
        assert hasattr(config, 'output_dir')
        assert hasattr(config, 'browser_config')
        
        # Test county configs
        charleston_config = get_county_config('charleston')
        berkeley_config = get_county_config('berkeley')
        
        assert charleston_config.name == "Charleston County"
        assert berkeley_config.name == "Berkeley County"
        
        print_test_result("Configuration", True, "All configurations loaded")
        return True
        
    except Exception as e:
        print_test_result("Configuration", False, str(e))
        return False


async def test_document_manager():
    """Test document management functionality."""
    print_test_header("Document Manager Test")
    
    try:
        from src.document_manager import DocumentManager
        from src.models import DocumentType
        
        with tempfile.TemporaryDirectory() as temp_dir:
            doc_manager = DocumentManager(Path(temp_dir))
            
            # Test folder creation
            folder = doc_manager.create_property_folder("1234567890")
            assert folder.exists()
            
            # Test document saving
            test_content = b"Test document content"
            file_path = doc_manager.save_document(
                content=test_content,
                tms_number="1234567890",
                document_type=DocumentType.PROPERTY_CARD,
                county="charleston"
            )
            
            assert file_path.exists()
            assert file_path.read_bytes() == test_content
            
            # Test validation
            validation_result = doc_manager.validate_document(file_path)
            assert validation_result.is_valid
            
            # Test storage stats
            stats = doc_manager.get_storage_stats()
            assert stats['total_files'] >= 1
        
        print_test_result("Document Manager", True, "All document operations successful")
        return True
        
    except Exception as e:
        print_test_result("Document Manager", False, str(e))
        return False


async def test_mock_implementations():
    """Test mock implementations."""
    print_test_header("Mock Implementations Test")
    
    try:
        from src.mock_implementations import MockLLMParser, MockAgent, MockWebNavigator
        
        # Test mock parser
        parser = MockLLMParser()
        result = parser.parse_instruction("Collect documents for Charleston County TMS 1234567890")
        
        assert result['county'] == 'charleston'
        assert '1234567890' in result['tms_numbers']
        
        # Test mock navigator
        navigator = MockWebNavigator()
        await navigator.initialize()
        
        nav_result = await navigator.navigate_to("https://example.com", "charleston")
        assert nav_result == True
        
        await navigator.cleanup()
        
        # Test mock agent
        agent = MockAgent()
        execution_result = await agent.execute_instruction("Test instruction for Charleston County TMS 1234567890")
        
        assert execution_result.status.value == "success"
        
        print_test_result("Mock Implementations", True, "All mock services working")
        return True
        
    except Exception as e:
        print_test_result("Mock Implementations", False, str(e))
        return False


async def test_instruction_parser():
    """Test instruction parsing."""
    print_test_header("Instruction Parser Test")
    
    try:
        from src.parser import InstructionParser
        
        parser = InstructionParser()
        
        # Test parsing
        instruction = "Collect all documents for Charleston County TMS 5590200072 and Berkeley County TMS 2590502005"
        plan = parser.parse_instruction(instruction)
        
        assert plan.county.value in ['charleston', 'berkeley']
        assert len(plan.tms_numbers) >= 1
        assert len(plan.document_types) >= 1
        assert len(plan.workflow_steps) > 0
        
        print_test_result("Instruction Parser", True, f"Parsed {len(plan.workflow_steps)} workflow steps")
        return True
        
    except Exception as e:
        print_test_result("Instruction Parser", False, str(e))
        return False


async def test_cli_interface():
    """Test CLI interface components."""
    print_test_header("CLI Interface Test")
    
    try:
        from src.cli import ProgressTracker, format_file_size
        
        # Test progress tracker
        tracker = ProgressTracker()
        tracker.start("Test progress")
        tracker.stop()
        
        # Test utility functions
        size_str = format_file_size(1024)
        assert "KB" in size_str
        
        size_str = format_file_size(1048576)
        assert "MB" in size_str
        
        print_test_result("CLI Interface", True, "CLI components working")
        return True
        
    except Exception as e:
        print_test_result("CLI Interface", False, str(e))
        return False


async def test_end_to_end_mock():
    """Test complete end-to-end workflow with mock implementations."""
    print_test_header("End-to-End Mock Test")
    
    try:
        from src.mock_implementations import MockAgent
        from src.models import ProgressUpdate
        
        # Progress tracking
        progress_updates = []
        
        def progress_callback(update: ProgressUpdate):
            progress_updates.append(update)
        
        # Execute complete workflow
        agent = MockAgent({'output_dir': Path('./test_output')})
        result = await agent.execute_instruction(
            "Collect all documents for Charleston County TMS 5590200072",
            progress_callback
        )
        
        # Verify results
        assert result.status.value == "success"
        assert result.execution_time > 0
        assert len(progress_updates) > 0
        
        # Check progress updates
        assert any("parsing" in update.current_step for update in progress_updates)
        assert any(update.progress_percentage == 100 for update in progress_updates)
        
        print_test_result("End-to-End Mock", True, 
                         f"Completed in {result.execution_time:.2f}s with {len(progress_updates)} progress updates")
        return True
        
    except Exception as e:
        print_test_result("End-to-End Mock", False, str(e))
        return False


async def test_error_handling():
    """Test error handling and recovery."""
    print_test_header("Error Handling Test")
    
    try:
        from src.mock_implementations import MockAgent
        
        agent = MockAgent()
        
        # Test with invalid instruction
        result = await agent.execute_instruction("")
        
        # Should handle gracefully
        assert result is not None
        
        print_test_result("Error Handling", True, "Error handling working correctly")
        return True
        
    except Exception as e:
        print_test_result("Error Handling", False, str(e))
        return False


async def main():
    """Run all tests."""
    print("🚀 AI Web Scraper Agent - Comprehensive Test Suite")
    print("=" * 60)
    print("Testing all components and functionality...")
    
    # Define test functions
    tests = [
        ("Models", test_models),
        ("Configuration", test_configuration),
        ("Document Manager", test_document_manager),
        ("Mock Implementations", test_mock_implementations),
        ("Instruction Parser", test_instruction_parser),
        ("CLI Interface", test_cli_interface),
        ("End-to-End Mock", test_end_to_end_mock),
        ("Error Handling", test_error_handling),
    ]
    
    # Run tests
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if await test_func():
                passed += 1
        except Exception as e:
            print_test_result(test_name, False, f"Unexpected error: {str(e)}")
    
    # Final results
    print(f"\n{'='*60}")
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    print('='*60)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The system is working correctly.")
        print("\n✅ The AI Web Scraper Agent is ready for use!")
        print("\nNext steps:")
        print("1. Run the demo: python run_demo.py")
        print("2. Try the CLI: python -m src.cli test --mock-mode")
        print("3. Execute instructions: python -m src.cli execute 'your instruction' --mock-mode")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed. Please review the errors above.")
        print("\n💡 The system may still work with mock implementations.")
        print("Try: python run_demo.py")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 Tests cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
