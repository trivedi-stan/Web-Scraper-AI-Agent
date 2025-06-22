#!/usr/bin/env python3
"""
Installation validation script for the AI Web Scraper Agent.

This script validates that the installation is working correctly
and all components can be imported and initialized.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def check_python_version():
    """Check Python version compatibility."""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} (compatible)")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.9+)")
        return False


def check_basic_imports():
    """Check that basic Python modules can be imported."""
    print("\n📦 Checking basic imports...")
    
    basic_modules = [
        "json", "re", "pathlib", "datetime", "asyncio", 
        "typing", "dataclasses", "enum"
    ]
    
    failed_imports = []
    
    for module in basic_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError as e:
            print(f"   ❌ {module}: {e}")
            failed_imports.append(module)
    
    return len(failed_imports) == 0


def check_project_structure():
    """Check that project structure is correct."""
    print("\n📁 Checking project structure...")
    
    required_files = [
        "src/__init__.py",
        "src/models.py",
        "src/config.py",
        "src/logging_config.py",
        "src/document_manager.py",
        "src/parser.py",
        "src/navigator.py",
        "src/agent.py",
        "src/cli.py",
        "src/mock_implementations.py",
        "requirements.txt",
        "requirements-basic.txt",
        ".env.example",
        "README.md"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (missing)")
            missing_files.append(file_path)
    
    return len(missing_files) == 0


def check_core_imports():
    """Check that core project modules can be imported."""
    print("\n🔧 Checking core module imports...")
    
    modules_to_test = [
        ("src.models", "Data models"),
        ("src.config", "Configuration system"),
        ("src.logging_config", "Logging configuration"),
        ("src.document_manager", "Document manager"),
        ("src.mock_implementations", "Mock implementations"),
    ]
    
    failed_imports = []
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"   ✅ {description} ({module_name})")
        except ImportError as e:
            print(f"   ❌ {description} ({module_name}): {e}")
            failed_imports.append(module_name)
    
    return len(failed_imports) == 0


def check_optional_dependencies():
    """Check optional dependencies and report their status."""
    print("\n🔍 Checking optional dependencies...")
    
    optional_deps = [
        ("pydantic", "Data validation"),
        ("python-dotenv", "Environment variables"),
        ("pyyaml", "YAML configuration"),
        ("click", "CLI framework"),
        ("rich", "Rich console output"),
        ("langchain_openai", "LangChain OpenAI integration"),
        ("playwright", "Browser automation"),
        ("PyPDF2", "PDF processing"),
        ("PIL", "Image processing"),
    ]
    
    available = []
    missing = []
    
    for module_name, description in optional_deps:
        try:
            __import__(module_name)
            print(f"   ✅ {description} ({module_name})")
            available.append(module_name)
        except ImportError:
            print(f"   ⚠️  {description} ({module_name}) - not installed")
            missing.append(module_name)
    
    print(f"\n   📊 {len(available)} available, {len(missing)} missing")
    
    if missing:
        print(f"   💡 To install missing dependencies:")
        print(f"      pip install {' '.join(missing)}")
    
    return len(available) > 0


def check_environment_setup():
    """Check environment configuration."""
    print("\n⚙️ Checking environment setup...")
    
    # Check for .env file
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("   ✅ .env file exists")
        
        # Check for API key
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            if os.getenv("OPENAI_API_KEY"):
                print("   ✅ OPENAI_API_KEY is set")
            else:
                print("   ⚠️  OPENAI_API_KEY not set (required for LLM features)")
                
        except ImportError:
            print("   ⚠️  python-dotenv not available, cannot check environment variables")
            
    else:
        print("   ⚠️  .env file not found")
        if env_example.exists():
            print("   💡 Copy .env.example to .env and configure your settings")
        
    return True


def test_basic_functionality():
    """Test basic functionality without external dependencies."""
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Test models
        from src.models import County, DocumentType, ExecutionStatus
        charleston = County.CHARLESTON
        property_card = DocumentType.PROPERTY_CARD
        success = ExecutionStatus.SUCCESS
        print("   ✅ Data models working")
        
        # Test configuration
        from src.config import ConfigManager
        config_manager = ConfigManager()
        print("   ✅ Configuration system working")
        
        # Test document manager
        from src.document_manager import DocumentManager
        doc_manager = DocumentManager(Path("./test_output"))
        print("   ✅ Document manager working")
        
        # Test mock implementations
        from src.mock_implementations import MockLLMParser, MockAgent
        parser = MockLLMParser()
        agent = MockAgent()
        print("   ✅ Mock implementations working")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Basic functionality test failed: {e}")
        return False


def main():
    """Run all validation checks."""
    print("🔍 AI Web Scraper Agent - Installation Validation")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Basic Imports", check_basic_imports),
        ("Project Structure", check_project_structure),
        ("Core Imports", check_core_imports),
        ("Optional Dependencies", check_optional_dependencies),
        ("Environment Setup", check_environment_setup),
        ("Basic Functionality", test_basic_functionality),
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        try:
            if check_func():
                passed += 1
        except Exception as e:
            print(f"   ❌ {check_name} check failed with error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Validation Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 Installation validation successful!")
        print("\nYour AI Web Scraper Agent is ready to use!")
        print("\nNext steps:")
        print("1. Install optional dependencies: pip install -r requirements.txt")
        print("2. Set up .env file with your OpenAI API key")
        print("3. Run the demo: python run_demo.py")
        print("4. Run comprehensive tests: python test_comprehensive.py")
        print("5. Use the CLI: python -m src.cli --help")
        return 0
    else:
        print("⚠️  Some validation checks failed.")
        print("Please review the errors above and fix any issues.")
        
        if passed >= 4:  # Core functionality works
            print("\n💡 Core functionality appears to work.")
            print("You can still use the mock implementations for testing.")
            print("Run: python run_demo.py")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
