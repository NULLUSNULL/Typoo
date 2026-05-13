"""
Core models and enumerations for Typoo.
"""

from enum import Enum
from typing import Optional


class DocumentType(str, Enum):
    """Types of documents in a project."""
    
    CHAPTER = "chapter"
    SCENE = "scene"
    NOTE = "note"
    CHARACTER = "character"
    LOCATION = "location"
    DOCUMENT = "document"


class DocumentStatus(str, Enum):
    """Status of a document."""
    
    DRAFT = "draft"
    REVISION = "revision"
    FINAL = "final"


class ExportFormat(str, Enum):
    """Supported export formats."""
    
    MARKDOWN = "md"
    DOCX = "docx"
    PDF = "pdf"
    TXT = "txt"
    HTML = "html"
