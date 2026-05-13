"""
Tab widget for managing multiple open documents.
"""

from PySide6.QtWidgets import QTabWidget, QMessageBox
from PySide6.QtCore import Qt, Signal as pyqtSignal
from typing import Dict, Optional

from typoo.models import Document
from typoo.editors import MarkdownEditor
from typoo.logger import Logger

logger = Logger.get()


class TabWidget(QTabWidget):
    """Tab widget for managing multiple documents."""
    
    tab_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_map: Dict[int, Document] = {}
        self.unsaved_changes: Dict[int, bool] = {}
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self._on_tab_close)
        self.currentChanged.connect(self._on_current_changed)
        self.setStyleSheet("""
            QTabBar::tab {
                padding: 8px 20px;
            }
        """)
    
    def open_document(self, document: Document) -> MarkdownEditor:
        """
        Open a document in a new tab.
        
        Returns:
            Editor widget for the document
        """
        # Check if already open
        for tab_index in range(self.count()):
            if self.tab_map.get(tab_index) == document:
                self.setCurrentIndex(tab_index)
                return self.widget(tab_index)
        
        # Create new tab
        editor = MarkdownEditor()
        editor.set_content(document.content)
        editor.content_changed.connect(lambda: self._on_editor_changed(editor))
        
        tab_index = self.addTab(editor, self._get_tab_title(document))
        self.tab_map[tab_index] = document
        self.unsaved_changes[tab_index] = False
        self.setCurrentIndex(tab_index)
        
        logger.debug(f"Document opened in tab: {document.name}")
        return editor
    
    def close_document(self, tab_index: int) -> bool:
        """
        Close a document tab.
        
        Returns:
            True if closed, False if cancelled
        """
        document = self.tab_map.get(tab_index)
        if not document:
            return False
        
        # Check for unsaved changes
        if self.unsaved_changes.get(tab_index, False):
            editor = self.widget(tab_index)
            if isinstance(editor, MarkdownEditor):
                reply = QMessageBox.question(
                    self, "Unsaved Changes",
                    f"Close '{document.name}' without saving?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )
                
                if reply == QMessageBox.Cancel:
                    return False
                elif reply == QMessageBox.Save:
                    self.save_document(tab_index)
        
        # Close tab
        self.removeTab(tab_index)
        del self.tab_map[tab_index]
        del self.unsaved_changes[tab_index]
        logger.debug(f"Document tab closed: {document.name}")
        return True
    
    def save_document(self, tab_index: int) -> None:
        """Save document at tab index."""
        document = self.tab_map.get(tab_index)
        editor = self.widget(tab_index)
        
        if document and isinstance(editor, MarkdownEditor):
            document.content = editor.get_content()
            self.unsaved_changes[tab_index] = False
            self._update_tab_title(tab_index)
            logger.debug(f"Document saved: {document.name}")
    
    def get_current_document(self) -> Optional[Document]:
        """Get currently active document."""
        current_index = self.currentIndex()
        return self.tab_map.get(current_index)
    
    def get_current_editor(self) -> Optional[MarkdownEditor]:
        """Get currently active editor."""
        current_index = self.currentIndex()
        editor = self.widget(current_index)
        if isinstance(editor, MarkdownEditor):
            return editor
        return None
    
    def _on_tab_close(self, tab_index: int) -> None:
        """Handle tab close button."""
        self.close_document(tab_index)
    
    def _on_current_changed(self, index: int) -> None:
        """Handle current tab change."""
        self.tab_changed.emit(index)
    
    def _on_editor_changed(self, editor: MarkdownEditor) -> None:
        """Handle editor content change."""
        # Find which tab this editor belongs to
        for tab_index in range(self.count()):
            if self.widget(tab_index) == editor:
                self.unsaved_changes[tab_index] = True
                self._update_tab_title(tab_index)
                break
    
    def _get_tab_title(self, document: Document) -> str:
        """Get tab title for document."""
        return document.name
    
    def _update_tab_title(self, tab_index: int) -> None:
        """Update tab title with unsaved indicator."""
        document = self.tab_map.get(tab_index)
        if document:
            title = document.name
            if self.unsaved_changes.get(tab_index, False):
                title = f"• {title}"
            self.setTabText(tab_index, title)
