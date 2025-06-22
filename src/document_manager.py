"""
Document management system for the AI Web Scraper Agent.

This module handles document organization, validation, and storage with
intelligent naming conventions and folder structures.
"""

import hashlib
import json
import mimetypes
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from .models import DocumentType, ValidationResult
from .logging_config import LoggerMixin


class DocumentManager(LoggerMixin):
    """Manages document storage, organization, and validation."""
    
    def __init__(self, base_output_dir: Path):
        """Initialize document manager.
        
        Args:
            base_output_dir: Base directory for storing documents
        """
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logs directory
        self.logs_dir = self.base_output_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        self.logger.info("document_manager_initialized", base_dir=str(self.base_output_dir))
    
    def create_property_folder(self, tms_number: str) -> Path:
        """Create folder structure for a property.
        
        Args:
            tms_number: TMS number for the property
            
        Returns:
            Path to the property folder
        """
        property_folder = self.base_output_dir / tms_number
        property_folder.mkdir(exist_ok=True)
        
        # Create subfolders
        deeds_folder = property_folder / "Deeds"
        deeds_folder.mkdir(exist_ok=True)
        
        self.logger.info("property_folder_created", tms_number=tms_number, path=str(property_folder))
        return property_folder
    
    def get_document_filename(
        self, 
        document_type: Union[str, DocumentType], 
        county: str,
        additional_info: Optional[str] = None
    ) -> str:
        """Generate appropriate filename for document type.
        
        Args:
            document_type: Type of document
            county: County name
            additional_info: Additional information for filename
            
        Returns:
            Generated filename
        """
        if isinstance(document_type, str):
            document_type = DocumentType(document_type)
        
        # Base filename mapping
        filename_map = {
            DocumentType.PROPERTY_CARD: "Property Card",
            DocumentType.TAX_INFO: "Tax Info",
            DocumentType.TAX_BILL: "Tax Bill",
            DocumentType.TAX_RECEIPT: "Tax Receipt",
            DocumentType.DEED: "Deed"
        }
        
        base_name = filename_map.get(document_type, document_type.value.replace('_', ' ').title())
        
        # Add additional info if provided
        if additional_info:
            base_name += f" - {additional_info}"
        
        return f"{base_name}.pdf"
    
    def save_document(
        self,
        content: bytes,
        tms_number: str,
        document_type: Union[str, DocumentType],
        county: str,
        additional_info: Optional[str] = None,
        validate: bool = True
    ) -> Path:
        """Save document with proper organization.
        
        Args:
            content: Document content as bytes
            tms_number: TMS number for the property
            document_type: Type of document
            county: County name
            additional_info: Additional information for filename
            validate: Whether to validate the document
            
        Returns:
            Path to saved document
            
        Raises:
            ValueError: If validation fails and validate=True
        """
        if isinstance(document_type, str):
            document_type = DocumentType(document_type)
        
        # Create property folder
        property_folder = self.create_property_folder(tms_number)
        
        # Determine target folder
        if document_type == DocumentType.DEED:
            target_folder = property_folder / "Deeds"
        else:
            target_folder = property_folder
        
        target_folder.mkdir(exist_ok=True)
        
        # Generate filename
        filename = self.get_document_filename(document_type, county, additional_info)
        file_path = target_folder / filename
        
        # Save document
        try:
            with open(file_path, 'wb') as f:
                f.write(content)
            
            self.logger.info("document_saved", 
                           tms_number=tms_number,
                           document_type=document_type.value,
                           file_path=str(file_path),
                           file_size=len(content))
            
            # Validate if requested
            if validate:
                validation_result = self.validate_document(file_path)
                if not validation_result.is_valid:
                    self.logger.warning("document_validation_failed",
                                      file_path=str(file_path),
                                      errors=validation_result.errors)
                    if validation_result.errors:
                        raise ValueError(f"Document validation failed: {validation_result.errors}")
            
            return file_path
            
        except Exception as e:
            self.logger.error("document_save_failed", 
                            tms_number=tms_number,
                            error=str(e))
            raise
    
    def validate_document(self, file_path: Path) -> ValidationResult:
        """Validate a document file.
        
        Args:
            file_path: Path to document file
            
        Returns:
            ValidationResult with validation details
        """
        errors = []
        warnings = []
        
        try:
            if not file_path.exists():
                errors.append("File does not exist")
                return ValidationResult(
                    is_valid=False,
                    file_type="unknown",
                    file_size=0,
                    errors=errors
                )
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size == 0:
                errors.append("File is empty")
            elif file_size < 100:  # Very small files are suspicious
                warnings.append("File is very small, may be incomplete")
            
            # Check file type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            file_type = mime_type or "unknown"
            
            # Basic content validation for PDFs
            if file_path.suffix.lower() == '.pdf':
                try:
                    with open(file_path, 'rb') as f:
                        header = f.read(4)
                        if header != b'%PDF':
                            errors.append("Invalid PDF header")
                except Exception as e:
                    errors.append(f"Could not read PDF header: {str(e)}")
            
            is_valid = len(errors) == 0
            
            self.logger.info("document_validated",
                           file_path=str(file_path),
                           is_valid=is_valid,
                           file_size=file_size,
                           file_type=file_type)
            
            return ValidationResult(
                is_valid=is_valid,
                file_type=file_type,
                file_size=file_size,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            self.logger.error("document_validation_error", 
                            file_path=str(file_path),
                            error=str(e))
            return ValidationResult(
                is_valid=False,
                file_type="unknown",
                file_size=0,
                errors=[f"Validation error: {str(e)}"]
            )
    
    def get_document_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of document.
        
        Args:
            file_path: Path to document file
            
        Returns:
            SHA-256 hash as hex string
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.logger.error("hash_calculation_failed", 
                            file_path=str(file_path),
                            error=str(e))
            return ""
    
    def create_execution_summary(
        self,
        execution_id: str,
        results: Dict[str, Any],
        documents: List[Path]
    ) -> Path:
        """Create execution summary file.
        
        Args:
            execution_id: Unique execution identifier
            results: Execution results dictionary
            documents: List of collected document paths
            
        Returns:
            Path to summary file
        """
        summary_data = {
            "execution_id": execution_id,
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "documents": [
                {
                    "path": str(doc),
                    "filename": doc.name,
                    "size": doc.stat().st_size if doc.exists() else 0,
                    "hash": self.get_document_hash(doc) if doc.exists() else ""
                }
                for doc in documents
            ],
            "summary": {
                "total_documents": len(documents),
                "total_size": sum(doc.stat().st_size for doc in documents if doc.exists()),
                "success_rate": results.get("success_rate", 0.0)
            }
        }
        
        summary_file = self.logs_dir / f"execution_summary_{execution_id}.json"
        
        try:
            with open(summary_file, 'w') as f:
                json.dump(summary_data, f, indent=2)
            
            self.logger.info("execution_summary_created",
                           execution_id=execution_id,
                           summary_file=str(summary_file),
                           document_count=len(documents))
            
            return summary_file
            
        except Exception as e:
            self.logger.error("summary_creation_failed",
                            execution_id=execution_id,
                            error=str(e))
            raise
    
    def cleanup_empty_folders(self) -> int:
        """Remove empty folders from the output directory.
        
        Returns:
            Number of folders removed
        """
        removed_count = 0
        
        try:
            for folder in self.base_output_dir.rglob('*'):
                if folder.is_dir() and not any(folder.iterdir()):
                    folder.rmdir()
                    removed_count += 1
                    self.logger.info("empty_folder_removed", folder=str(folder))
            
            return removed_count
            
        except Exception as e:
            self.logger.error("cleanup_failed", error=str(e))
            return removed_count
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics for the output directory.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            total_files = 0
            total_size = 0
            file_types = {}
            
            for file_path in self.base_output_dir.rglob('*'):
                if file_path.is_file():
                    total_files += 1
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    
                    file_ext = file_path.suffix.lower()
                    file_types[file_ext] = file_types.get(file_ext, 0) + 1
            
            stats = {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types,
                "base_directory": str(self.base_output_dir)
            }
            
            self.logger.info("storage_stats_calculated", **stats)
            return stats
            
        except Exception as e:
            self.logger.error("stats_calculation_failed", error=str(e))
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0.0,
                "file_types": {},
                "base_directory": str(self.base_output_dir),
                "error": str(e)
            }
