"""
Data models for Typoo.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from typoo.models.enums import DocumentType, DocumentStatus


@dataclass
class Metadata:
    """Metadata for a document."""
    
    title: str
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    author: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    status: DocumentStatus = DocumentStatus.DRAFT
    word_count: int = 0
    custom_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """Represents a document (file) in the project."""
    
    name: str
    path: Path
    doc_type: DocumentType
    content: str = ""
    metadata: Metadata = field(default_factory=lambda: Metadata(""))
    children: List["Document"] = field(default_factory=list)
    parent: Optional["Document"] = None
    
    def add_child(self, child: "Document") -> None:
        """Add a child document."""
        child.parent = self
        self.children.append(child)
    
    def remove_child(self, child: "Document") -> None:
        """Remove a child document."""
        if child in self.children:
            self.children.remove(child)
            child.parent = None
    
    def get_full_path(self) -> Path:
        """Get full path to this document."""
        return self.path
    
    def is_leaf(self) -> bool:
        """Check if document is a leaf node."""
        return len(self.children) == 0


@dataclass
class ProjectMetadata:
    """Metadata for a project."""
    
    name: str
    author: str = ""
    description: str = ""
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Project:
    """Represents a Typoo project."""
    
    name: str
    path: Path
    metadata: ProjectMetadata = field(default_factory=lambda: ProjectMetadata(""))
    root_document: Optional[Document] = None
    documents: List[Document] = field(default_factory=list)
    
    def add_document(self, document: Document) -> None:
        """Add a document to the project."""
        self.documents.append(document)
    
    def remove_document(self, document: Document) -> None:
        """Remove a document from the project."""
        if document in self.documents:
            self.documents.remove(document)
    
    def find_document(self, path: Path) -> Optional[Document]:
        """Find a document by path."""
        for doc in self.documents:
            if doc.path == path:
                return doc
        return None
