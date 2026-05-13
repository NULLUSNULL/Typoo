"""
Storage and persistence layer for Typoo projects.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from typoo.models import Project, Document, ProjectMetadata, Metadata, DocumentType
from typoo.logger import Logger

logger = Logger.get()


class StorageManager:
    """Manages project storage and file I/O."""
    
    METADATA_FILE = "project.json"
    
    @staticmethod
    def create_project(project_path: Path, name: str, author: str = "") -> Project:
        """
        Create a new project.
        
        Args:
            project_path: Directory where project will be created
            name: Project name
            author: Project author
            
        Returns:
            Created Project instance
        """
        project_path = Path(project_path)
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Create project metadata
        metadata = ProjectMetadata(
            name=name,
            author=author,
            created_at=datetime.now(),
            modified_at=datetime.now()
        )
        
        # Create project instance
        project = Project(
            name=name,
            path=project_path,
            metadata=metadata
        )
        
        # Save metadata
        StorageManager.save_project_metadata(project)
        
        logger.info(f"Project created: {name} at {project_path}")
        return project
    
    @staticmethod
    def open_project(project_path: Path) -> Optional[Project]:
        """
        Open an existing project.
        
        Args:
            project_path: Path to project directory
            
        Returns:
            Loaded Project instance or None if failed
        """
        project_path = Path(project_path)
        
        if not project_path.exists():
            logger.error(f"Project path not found: {project_path}")
            return None
        
        # Load metadata
        metadata_file = project_path / StorageManager.METADATA_FILE
        if metadata_file.exists():
            metadata = StorageManager._load_project_metadata(metadata_file)
        else:
            metadata = ProjectMetadata(name=project_path.name)
        
        project = Project(
            name=metadata.name,
            path=project_path,
            metadata=metadata
        )
        
        # Load project structure from directory
        StorageManager._load_project_structure(project, project_path)
        
        logger.info(f"Project opened: {project.name} from {project_path}")
        return project
    
    @staticmethod
    def save_project_metadata(project: Project) -> None:
        """Save project metadata to file."""
        metadata_file = project.path / StorageManager.METADATA_FILE
        
        data = {
            "name": project.metadata.name,
            "author": project.metadata.author,
            "description": project.metadata.description,
            "version": project.metadata.version,
            "created_at": project.metadata.created_at.isoformat(),
            "modified_at": datetime.now().isoformat(),
            "tags": project.metadata.tags,
            "custom_fields": project.metadata.custom_fields
        }
        
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Project metadata saved: {metadata_file}")
    
    @staticmethod
    def save_document(document: Document) -> None:
        """
        Save document content to file.
        
        Args:
            document: Document to save
        """
        document.path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save content
        with open(document.path, "w", encoding="utf-8") as f:
            f.write(document.content)
        
        logger.debug(f"Document saved: {document.path}")
    
    @staticmethod
    def load_document(doc_path: Path) -> Optional[str]:
        """
        Load document content from file.
        
        Args:
            doc_path: Path to document file
            
        Returns:
            Document content or None if failed
        """
        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load document: {doc_path} - {str(e)}")
            return None
    
    @staticmethod
    def _load_project_structure(project: Project, project_path: Path, parent: Optional[Document] = None) -> None:
        """Recursively load project structure from directory."""
        try:
            for item in project_path.iterdir():
                if item.is_file() and item.suffix == ".md":
                    # Create document from markdown file
                    doc_type = DocumentType.DOCUMENT
                    if "chapter" in item.stem.lower():
                        doc_type = DocumentType.CHAPTER
                    elif "scene" in item.stem.lower():
                        doc_type = DocumentType.SCENE
                    elif "note" in item.stem.lower():
                        doc_type = DocumentType.NOTE
                    elif "character" in item.stem.lower():
                        doc_type = DocumentType.CHARACTER
                    elif "location" in item.stem.lower():
                        doc_type = DocumentType.LOCATION
                    
                    # Load content
                    content = StorageManager.load_document(item)
                    if content is None:
                        continue
                    
                    metadata = Metadata(title=item.stem)
                    document = Document(
                        name=item.stem,
                        path=item,
                        doc_type=doc_type,
                        content=content,
                        metadata=metadata
                    )
                    
                    if parent:
                        parent.add_child(document)
                    else:
                        project.add_document(document)
                
                elif item.is_dir() and not item.name.startswith("."):
                    # Recursively load subdirectory
                    StorageManager._load_project_structure(project, item, parent)
        
        except Exception as e:
            logger.error(f"Error loading project structure: {str(e)}")
    
    @staticmethod
    def _load_project_metadata(metadata_file: Path) -> ProjectMetadata:
        """Load project metadata from file."""
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            return ProjectMetadata(
                name=data.get("name", ""),
                author=data.get("author", ""),
                description=data.get("description", ""),
                version=data.get("version", "1.0"),
                created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
                modified_at=datetime.fromisoformat(data.get("modified_at", datetime.now().isoformat())),
                tags=data.get("tags", []),
                custom_fields=data.get("custom_fields", {})
            )
        except Exception as e:
            logger.error(f"Failed to load project metadata: {str(e)}")
            return ProjectMetadata(name="Unknown Project")
