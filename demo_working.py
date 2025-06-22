#!/usr/bin/env python3
"""
Working demonstration of the AI Web Scraper Agent.

This script demonstrates the complete functionality using mock implementations,
showing how the system works without requiring external dependencies.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def print_banner():
    """Print welcome banner."""
    print("🤖 AI Web Scraper Agent - Working Demo")
    print("=" * 50)
    print("Demonstrating complete functionality with mock implementations")
    print("=" * 50)


def print_section(title: str):
    """Print section header."""
    print(f"\n📋 {title}")
    print("-" * 40)


async def demo_instruction_parsing():
    """Demonstrate instruction parsing."""
    print_section("Instruction Parsing Demo")
    
    try:
        from src.mock_implementations import MockLLMParser
        
        parser = MockLLMParser()
        
        # Test various instructions
        instructions = [
            "Collect all documents for Charleston County TMS 5590200072",
            "Get property card and tax info for Berkeley County TMS 2590502005",
            "Visit Charleston County and collect property card, tax info, and deeds for TMS 5321500185"
        ]
        
        for i, instruction in enumerate(instructions, 1):
            print(f"\n{i}. Instruction: {instruction}")
            result = parser.parse_instruction(instruction)
            
            print(f"   County: {result['county']}")
            print(f"   TMS Numbers: {result['tms_numbers']}")
            print(f"   Document Types: {result['document_types']}")
            print(f"   Estimated Duration: {result['estimated_duration']} seconds")
        
        print("\n✅ Instruction parsing working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Instruction parsing failed: {str(e)}")
        return False


async def demo_document_management():
    """Demonstrate document management."""
    print_section("Document Management Demo")
    
    try:
        from src.document_manager import DocumentManager
        from src.models import DocumentType
        
        # Create document manager
        doc_manager = DocumentManager(Path("./demo_output"))
        
        # Create property folder
        tms_number = "5590200072"
        folder = doc_manager.create_property_folder(tms_number)
        print(f"✅ Created property folder: {folder}")
        
        # Save sample documents
        documents = [
            (DocumentType.PROPERTY_CARD, "Mock property card content for TMS 5590200072"),
            (DocumentType.TAX_INFO, "Mock tax information for TMS 5590200072"),
            (DocumentType.DEED, "Mock deed document for TMS 5590200072")
        ]
        
        saved_files = []
        for doc_type, content in documents:
            file_path = doc_manager.save_document(
                content=content.encode(),
                tms_number=tms_number,
                document_type=doc_type,
                county="charleston"
            )
            saved_files.append(file_path)
            print(f"✅ Saved {doc_type.value}: {file_path.name}")
        
        # Show storage stats
        stats = doc_manager.get_storage_stats()
        print(f"\n📊 Storage Statistics:")
        print(f"   Total Files: {stats['total_files']}")
        print(f"   Total Size: {stats['total_size_mb']} MB")
        print(f"   Base Directory: {stats['base_directory']}")
        
        print("\n✅ Document management working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Document management failed: {str(e)}")
        return False


async def demo_web_navigation():
    """Demonstrate web navigation (mock)."""
    print_section("Web Navigation Demo (Mock)")
    
    try:
        from src.mock_implementations import MockWebNavigator
        
        navigator = MockWebNavigator()
        
        # Initialize
        await navigator.initialize()
        print("✅ Browser initialized (mock)")
        
        # Navigate
        success = await navigator.navigate_to("https://charlestoncounty.org/search", "charleston")
        print(f"✅ Navigation successful: {success}")
        
        # Fill form
        form_data = {"#tms_input": "5590200072"}
        success = await navigator.fill_form(form_data)
        print(f"✅ Form filled successfully: {success}")
        
        # Extract data
        selectors = {
            "property_info": ".property-details",
            "tax_amount": ".tax-amount"
        }
        data = await navigator.extract_data(selectors)
        print(f"✅ Data extracted: {list(data.keys())}")
        
        # Cleanup
        await navigator.cleanup()
        print("✅ Browser cleanup completed")
        
        print("\n✅ Web navigation working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Web navigation failed: {str(e)}")
        return False


async def demo_complete_workflow():
    """Demonstrate complete end-to-end workflow."""
    print_section("Complete Workflow Demo")
    
    try:
        from src.mock_implementations import MockAgent
        from src.models import ProgressUpdate
        
        # Progress tracking
        progress_updates = []
        
        def progress_callback(update: ProgressUpdate):
            progress_updates.append(update)
            print(f"   [{update.progress_percentage:5.1f}%] {update.message}")
        
        # Create agent
        agent = MockAgent({'output_dir': Path('./demo_output')})
        
        # Execute instruction
        instruction = "Collect all documents for Charleston County TMS 5590200072"
        print(f"📝 Executing: {instruction}")
        
        result = await agent.execute_instruction(instruction, progress_callback)
        
        # Show results
        print(f"\n✅ Execution Results:")
        print(f"   Status: {result.status.value}")
        print(f"   Execution Time: {result.execution_time:.2f} seconds")
        print(f"   Documents Collected: {len(result.documents_collected)}")
        print(f"   Progress Updates: {len(progress_updates)}")
        
        if result.documents_collected:
            print(f"\n📄 Documents Created:")
            for doc in result.documents_collected:
                if doc.exists():
                    size = doc.stat().st_size
                    print(f"   - {doc.name} ({size} bytes)")
        
        print("\n✅ Complete workflow working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Complete workflow failed: {str(e)}")
        return False


async def demo_configuration():
    """Demonstrate configuration system."""
    print_section("Configuration System Demo")
    
    try:
        from src.config import get_config, get_county_config
        
        # Main configuration
        config = get_config()
        print(f"✅ Main configuration loaded")
        print(f"   Output Directory: {config.output_dir}")
        print(f"   Log Level: {config.log_level}")
        print(f"   Browser Type: {config.browser_config.browser_type}")
        
        # County configurations
        charleston_config = get_county_config('charleston')
        berkeley_config = get_county_config('berkeley')
        
        print(f"\n✅ County configurations:")
        print(f"   Charleston: {charleston_config.name}")
        print(f"   Berkeley: {berkeley_config.name}")
        
        print("\n✅ Configuration system working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration failed: {str(e)}")
        return False


async def main():
    """Run complete demonstration."""
    print_banner()
    
    # Run demonstrations
    demos = [
        ("Configuration System", demo_configuration),
        ("Instruction Parsing", demo_instruction_parsing),
        ("Document Management", demo_document_management),
        ("Web Navigation", demo_web_navigation),
        ("Complete Workflow", demo_complete_workflow),
    ]
    
    passed = 0
    total = len(demos)
    
    for demo_name, demo_func in demos:
        try:
            if await demo_func():
                passed += 1
        except Exception as e:
            print(f"❌ {demo_name} demo failed: {str(e)}")
    
    # Final summary
    print(f"\n{'='*50}")
    print(f"📊 Demo Results: {passed}/{total} demonstrations successful")
    print('='*50)
    
    if passed == total:
        print("🎉 ALL DEMONSTRATIONS SUCCESSFUL!")
        print("\nThe AI Web Scraper Agent is working correctly!")
        print("\n🚀 Next Steps:")
        print("1. Try the CLI: python -m src.cli test --mock-mode")
        print("2. Execute instructions: python -m src.cli execute 'your instruction' --mock-mode")
        print("3. Run comprehensive tests: python test_comprehensive.py")
        print("4. Install full dependencies for live mode: pip install -r requirements.txt")
        
        return 0
    else:
        print(f"⚠️  {total - passed} demonstrations failed.")
        print("Please check the errors above.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 Demo cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
