"""
Project explorer widget for file tree navigation.
"""

from PySide6.QtWidgets import (QTreeWidget, QTreeWidgetItem, QMenu, QInputDialog,
                               QMessageBox, QFileDialog, QAbstractItemView)
from PySide6.QtCore import Qt, Signal as pyqtSignal
from PySide6.QtGui import QIcon, QAction
from pathlib import Path
from typing import Optional, List

from typoo.models import Project, Document, DocumentType
from typoo.logger import Logger

logger = Logger.get()


class ProjectExplorer(QTreeWidget):
    """Widget for exploring project structure."""
    
    # Signals
    document_selected = pyqtSignal(Document)
    document_double_clicked = pyqtSignal(Document)
    document_context_menu = pyqtSignal(Document, QMenu)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project: Optional[Project] = None
        self.item_to_document: dict = {}
        self.document_to_item: dict = {}
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup UI elements."""
        self.setHeaderLabel("Project")
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAnimatedCollapse(True)
        self.customContextMenuRequested.connect(self._on_context_menu)
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
    
    def load_project(self, project: Project) -> None:
        """Load project into explorer."""
        self.project = project
        self.clear()
        self.item_to_document.clear()
        self.document_to_item.clear()
        
        # Add project root
        root_item = QTreeWidgetItem()
        root_item.setText(0, project.name)
        root_item.setData(0, Qt.UserRole, "project_root")
        self.addTopLevelItem(root_item)
        
        # Add documents
        for document in project.documents:
            self._add_document_to_tree(root_item, document)
        
        root_item.setExpanded(True)
        logger.debug(f"Project explorer loaded: {project.name}")
    
    def _add_document_to_tree(self, parent_item: QTreeWidgetItem, document: Document) -> None:
        """Recursively add document to tree."""
        item = QTreeWidgetItem(parent_item)
        item.setText(0, document.name)
        item.setData(0, Qt.UserRole, "document")
        
        # Store mappings
        self.item_to_document[id(item)] = document
        self.document_to_item[id(document)] = item
        
        # Set icon based on type
        icon_text = self._get_icon_for_type(document.doc_type)
        if icon_text:
            item.setText(0, f"{icon_text} {document.name}")
        
        # Add children recursively
        for child in document.children:
            self._add_document_to_tree(item, child)
    
    def _get_icon_for_type(self, doc_type: DocumentType) -> str:
        """Get icon text for document type."""
        icons = {
            DocumentType.CHAPTER: "📕",
            DocumentType.SCENE: "📄",
            DocumentType.NOTE: "📝",
            DocumentType.CHARACTER: "👤",
            DocumentType.LOCATION: "🗺️",
            DocumentType.DOCUMENT: "📃",
        }
        return icons.get(doc_type, "")
    
    def _on_selection_changed(self) -> None:
        """Handle selection change."""
        items = self.selectedItems()
        if items:
            item = items[0]
            document = self.item_to_document.get(id(item))
            if document:
                self.document_selected.emit(document)
    
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double click on item."""
        document = self.item_to_document.get(id(item))
        if document:
            self.document_double_clicked.emit(document)
    
    def _on_context_menu(self, position) -> None:
        """Handle context menu."""
        item = self.itemAt(position)
        if not item:
            return
        
        document = self.item_to_document.get(id(item))
        if not document:
            return
        
        menu = QMenu(self)
        
        # Add actions
        new_action = QAction("New Document", menu)
        new_action.triggered.connect(lambda: self._add_new_document(document))
        menu.addAction(new_action)
        
        rename_action = QAction("Rename", menu)
        rename_action.triggered.connect(lambda: self._rename_document(document, item))
        menu.addAction(rename_action)
        
        menu.addSeparator()
        
        delete_action = QAction("Delete", menu)
        delete_action.triggered.connect(lambda: self._delete_document(document))
        menu.addAction(delete_action)
        
        # Emit signal for custom menu items
        self.document_context_menu.emit(document, menu)
        
        menu.exec(self.mapToGlobal(position))
    
    def _add_new_document(self, parent: Document) -> None:
        """Add new document."""
        name, ok = QInputDialog.getText(self, "New Document", "Enter document name:")
        if ok and name:
            # This would typically trigger a signal to main window
            logger.debug(f"Create new document: {name} under {parent.name}")
    
    def _rename_document(self, document: Document, item: QTreeWidgetItem) -> None:
        """Rename document."""
        name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", 
                                       text=document.name)
        if ok and name:
            document.name = name
            item.setText(0, f"{self._get_icon_for_type(document.doc_type)} {name}")
            logger.debug(f"Document renamed: {name}")
    
    def _delete_document(self, document: Document) -> None:
        """Delete document."""
        reply = QMessageBox.question(self, "Delete", 
                                    f"Delete '{document.name}' and all its children?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            logger.debug(f"Document deleted: {document.name}")
