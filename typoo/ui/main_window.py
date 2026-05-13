"""
Main application window.
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QFileDialog, QMessageBox, QInputDialog, QDialog,
                               QLabel, QLineEdit, QFormLayout, QPushButton)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QAction, QKeySequence
from pathlib import Path
from typing import Optional

from typoo.config import Config
from typoo.logger import Logger
from typoo.models import Project, Document, DocumentType, ExportFormat
from typoo.core import StorageManager
from typoo.services import ExportService, SearchService
from typoo.ui.styles import StyleManager
from typoo.widgets import ProjectExplorer, EditorWidget, StatusBar, FormatToolbar
from typoo.utils import MarkdownUtils

logger = Logger.get()


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.project: Optional[Project] = None
        self.current_document: Optional[Document] = None
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._on_autosave)
        
        self.setup_ui()
        self.setup_menus()
        self.setup_connections()
        self.setWindowTitle(Config.APP_NAME)
        self.setGeometry(100, 100, Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
        
        # Apply default theme
        StyleManager.apply_dark_theme(self.get_app())
        
        # Start autosave
        if Config.AUTOSAVE_ENABLED:
            self.auto_save_timer.start(Config.AUTOSAVE_INTERVAL * 1000)
        
        logger.info("Main window initialized")
    
    def setup_ui(self) -> None:
        """Setup user interface."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Format toolbar
        self.format_toolbar = FormatToolbar()
        self.addToolBar(self.format_toolbar)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Project explorer
        self.project_explorer = ProjectExplorer()
        content_layout.addWidget(self.project_explorer)
        
        # Editor widget
        self.editor_widget = EditorWidget()
        content_layout.addWidget(self.editor_widget)
        
        main_layout.addLayout(content_layout)
        
        # Status bar
        self.status_bar_widget = StatusBar()
        self.setStatusBar(self.status_bar_widget)
        
        # Connect toolbar signals
        self.format_toolbar.bold_clicked.connect(lambda: self._insert_formatting("**", "**"))
        self.format_toolbar.italic_clicked.connect(lambda: self._insert_formatting("*", "*"))
        self.format_toolbar.underline_clicked.connect(lambda: self._insert_formatting("<u>", "</u>"))
        self.format_toolbar.strikethrough_clicked.connect(lambda: self._insert_formatting("~~", "~~"))
        self.format_toolbar.heading_clicked.connect(self._insert_heading)
        self.format_toolbar.list_clicked.connect(self._insert_list)
        self.format_toolbar.quote_clicked.connect(self._insert_quote)
        self.format_toolbar.code_clicked.connect(self._insert_code_block)
        self.format_toolbar.link_clicked.connect(self._insert_link)
    
    def setup_menus(self) -> None:
        """Setup application menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_project_action = QAction("New Project", self)
        new_project_action.setShortcut(QKeySequence.New)
        new_project_action.triggered.connect(self.new_project)
        file_menu.addAction(new_project_action)
        
        open_project_action = QAction("Open Project", self)
        open_project_action.setShortcut(QKeySequence.Open)
        open_project_action.triggered.connect(self.open_project)
        file_menu.addAction(open_project_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_current)
        file_menu.addAction(save_action)
        
        save_all_action = QAction("Save All", self)
        save_all_action.setShortcut(QKeySequence.SaveAll)
        save_all_action.triggered.connect(self.save_all)
        file_menu.addAction(save_all_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Export Project", self)
        export_action.triggered.connect(self.export_project)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence.Redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction("Cut", self)
        cut_action.setShortcut(QKeySequence.Cut)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("Copy", self)
        copy_action.setShortcut(QKeySequence.Copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("Paste", self)
        paste_action.setShortcut(QKeySequence.Paste)
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        find_action = QAction("Find", self)
        find_action.setShortcut(QKeySequence.Find)
        find_action.triggered.connect(self.find_in_document)
        edit_menu.addAction(find_action)
        
        find_replace_action = QAction("Find and Replace", self)
        find_replace_action.setShortcut(QKeySequence.Replace)
        find_replace_action.triggered.connect(self.find_replace)
        edit_menu.addAction(find_replace_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        toggle_left_action = QAction("Show Left Panel", self)
        toggle_left_action.setCheckable(True)
        toggle_left_action.triggered.connect(lambda checked: self.editor_widget.toggle_left_panel(checked))
        view_menu.addAction(toggle_left_action)
        
        toggle_right_action = QAction("Show Right Panel", self)
        toggle_right_action.setCheckable(True)
        toggle_right_action.triggered.connect(lambda checked: self.editor_widget.toggle_right_panel(checked))
        view_menu.addAction(toggle_right_action)
        
        view_menu.addSeparator()
        
        dark_theme_action = QAction("Dark Theme", self)
        dark_theme_action.triggered.connect(self._apply_dark_theme)
        view_menu.addAction(dark_theme_action)
        
        light_theme_action = QAction("Light Theme", self)
        light_theme_action.triggered.connect(self._apply_light_theme)
        view_menu.addAction(light_theme_action)
        
        view_menu.addSeparator()
        
        fullscreen_action = QAction("Fullscreen", self)
        fullscreen_action.setShortcut(QKeySequence.FullScreen)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Project menu
        project_menu = menubar.addMenu("Project")
        
        new_chapter_action = QAction("New Chapter", self)
        new_chapter_action.triggered.connect(lambda: self._create_document(DocumentType.CHAPTER))
        project_menu.addAction(new_chapter_action)
        
        new_scene_action = QAction("New Scene", self)
        new_scene_action.triggered.connect(lambda: self._create_document(DocumentType.SCENE))
        project_menu.addAction(new_scene_action)
        
        new_note_action = QAction("New Note", self)
        new_note_action.triggered.connect(lambda: self._create_document(DocumentType.NOTE))
        project_menu.addAction(new_note_action)
    
    def setup_connections(self) -> None:
        """Setup signal connections."""
        self.project_explorer.document_selected.connect(self._on_document_selected)
        self.project_explorer.document_double_clicked.connect(self._on_document_double_clicked)
        self.editor_widget.get_main_panel().tab_changed.connect(self._on_tab_changed)
    
    def new_project(self) -> None:
        """Create new project."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Project")
        
        layout = QFormLayout(dialog)
        
        name_input = QLineEdit()
        author_input = QLineEdit()
        
        layout.addRow("Project Name:", name_input)
        layout.addRow("Author:", author_input)
        
        button_layout = QHBoxLayout()
        ok_button = QPushButton("Create")
        cancel_button = QPushButton("Cancel")
        
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)
        
        if dialog.exec() == QDialog.Accepted:
            name = name_input.text().strip()
            author = author_input.text().strip()
            
            if name:
                path = QFileDialog.getExistingDirectory(self, "Select Project Location")
                if path:
                    project_path = Path(path) / name
                    try:
                        self.project = StorageManager.create_project(project_path, name, author)
                        self.project_explorer.load_project(self.project)
                        self.status_bar_widget.set_message(f"Project created: {name}", 3000)
                        logger.info(f"New project created: {name}")
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to create project: {str(e)}")
                        logger.error(f"Project creation failed: {str(e)}")
    
    def open_project(self) -> None:
        """Open existing project."""
        path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if path:
            try:
                self.project = StorageManager.open_project(Path(path))
                if self.project:
                    self.project_explorer.load_project(self.project)
                    self.status_bar_widget.set_message(f"Project opened: {self.project.name}", 3000)
                    logger.info(f"Project opened: {self.project.name}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to open project")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open project: {str(e)}")
                logger.error(f"Project open failed: {str(e)}")
    
    def save_current(self) -> None:
        """Save current document."""
        if self.current_document:
            panel = self.editor_widget.get_main_panel()
            current_index = panel.currentIndex()
            if current_index >= 0:
                panel.save_document(current_index)
                StorageManager.save_document(self.current_document)
                self.status_bar_widget.set_message("Document saved", 2000)
                logger.debug(f"Document saved: {self.current_document.name}")
    
    def save_all(self) -> None:
        """Save all open documents."""
        try:
            self.editor_widget.save_all()
            if self.project:
                for document in self.project.documents:
                    self._save_document_recursive(document)
            self.status_bar_widget.set_message("All documents saved", 2000)
            logger.info("All documents saved")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save documents: {str(e)}")
            logger.error(f"Save all failed: {str(e)}")
    
    def export_project(self) -> None:
        """Export project to various formats."""
        if not self.project:
            QMessageBox.warning(self, "Warning", "No project is currently open")
            return
        
        formats = {
            "Word Documents (*.docx)": ExportFormat.DOCX,
            "PDF Documents (*.pdf)": ExportFormat.PDF,
            "Text Files (*.txt)": ExportFormat.TXT,
            "Markdown Files (*.md)": ExportFormat.MARKDOWN,
        }
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Export Project", "",
            ";;".join(formats.keys())
        )
        
        if file_path:
            # Determine format from filter
            fmt = formats.get(selected_filter)
            if fmt:
                try:
                    success = ExportService.export_project(
                        self.project, Path(file_path), fmt
                    )
                    if success:
                        QMessageBox.information(self, "Success", f"Project exported to {file_path}")
                        logger.info(f"Project exported: {file_path}")
                    else:
                        QMessageBox.warning(self, "Error", "Export failed")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
                    logger.error(f"Export failed: {str(e)}")
    
    def find_in_document(self) -> None:
        """Open find dialog."""
        if not self.current_document:
            return
        
        text, ok = QInputDialog.getText(self, "Find", "Search for:")
        if ok and text:
            results = SearchService.search_in_document(self.current_document, text)
            if results:
                msg = f"Found {len(results)} occurrences"
                self.status_bar_widget.set_message(msg, 3000)
                logger.debug(msg)
            else:
                self.status_bar_widget.set_message("No occurrences found", 3000)
    
    def find_replace(self) -> None:
        """Open find and replace dialog."""
        if not self.current_document:
            return
        
        # Simple implementation - could be enhanced with a dedicated dialog
        search_text, ok = QInputDialog.getText(self, "Find and Replace", "Find:")
        if ok and search_text:
            replace_text, ok = QInputDialog.getText(self, "Find and Replace", "Replace with:")
            if ok:
                SearchService.replace_in_document(self.current_document, search_text, replace_text)
                self.status_bar_widget.set_message("Replacement complete", 2000)
    
    def _create_document(self, doc_type: DocumentType) -> None:
        """Create new document of specified type."""
        if not self.project:
            QMessageBox.warning(self, "Warning", "No project is open")
            return
        
        name, ok = QInputDialog.getText(self, "New Document", f"Enter {doc_type.value} name:")
        if ok and name:
            new_doc = Document(
                name=name,
                path=self.project.path / f"{name}.md",
                doc_type=doc_type
            )
            self.project.add_document(new_doc)
            self.project_explorer.load_project(self.project)
            logger.debug(f"New {doc_type.value} created: {name}")
    
    def _on_document_selected(self, document: Document) -> None:
        """Handle document selection."""
        self.current_document = document
    
    def _on_document_double_clicked(self, document: Document) -> None:
        """Handle document double click."""
        editor = self.editor_widget.get_main_panel().open_document(document)
        self.current_document = document
        self._update_status()
    
    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change."""
        panel = self.editor_widget.get_main_panel()
        self.current_document = panel.get_current_document()
        self._update_status()
    
    def _update_status(self) -> None:
        """Update status bar with current document stats."""
        if self.current_document:
            stats = MarkdownUtils.get_markdown_stats(self.current_document.content)
            self.status_bar_widget.update_stats(
                stats['words'],
                stats['characters'],
                stats['lines']
            )
    
    def _insert_formatting(self, prefix: str, suffix: str = "") -> None:
        """Insert formatting in current editor."""
        editor = self.editor_widget.get_main_panel().get_current_editor()
        if editor:
            editor.insert_formatting(prefix, suffix)
    
    def _insert_heading(self, level: int) -> None:
        """Insert heading in current editor."""
        editor = self.editor_widget.get_main_panel().get_current_editor()
        if editor and level > 0:
            editor.insert_heading(level)
    
    def _insert_list(self, ordered: bool) -> None:
        """Insert list in current editor."""
        editor = self.editor_widget.get_main_panel().get_current_editor()
        if editor:
            editor.insert_list(ordered)
    
    def _insert_quote(self) -> None:
        """Insert quote in current editor."""
        editor = self.editor_widget.get_main_panel().get_current_editor()
        if editor:
            editor.insert_quote()
    
    def _insert_code_block(self) -> None:
        """Insert code block in current editor."""
        editor = self.editor_widget.get_main_panel().get_current_editor()
        if editor:
            editor.insert_code_block()
    
    def _insert_link(self) -> None:
        """Insert link in current editor."""
        url, ok = QInputDialog.getText(self, "Insert Link", "URL:")
        if ok and url:
            editor = self.editor_widget.get_main_panel().get_current_editor()
            if editor:
                editor.insert_link(url)
    
    def _on_autosave(self) -> None:
        """Autosave timer callback."""
        try:
            self.save_all()
        except Exception as e:
            logger.error(f"Autosave failed: {str(e)}")
    
    def _save_document_recursive(self, document: Document) -> None:
        """Recursively save document and children."""
        StorageManager.save_document(document)
        for child in document.children:
            self._save_document_recursive(child)
    
    def _apply_dark_theme(self) -> None:
        """Apply dark theme."""
        StyleManager.apply_dark_theme(self.get_app())
    
    def _apply_light_theme(self) -> None:
        """Apply light theme."""
        StyleManager.apply_light_theme(self.get_app())
    
    def toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    @staticmethod
    def get_app():
        """Get QApplication instance."""
        from PySide6.QtWidgets import QApplication
        return QApplication.instance()
    
    def closeEvent(self, event) -> None:
        """Handle window close."""
        try:
            # Check for unsaved changes
            panel = self.editor_widget.get_main_panel()
            unsaved = any(panel.unsaved_changes.values())
            
            if unsaved:
                reply = QMessageBox.question(
                    self, "Unsaved Changes",
                    "There are unsaved changes. Save before closing?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )
                
                if reply == QMessageBox.Cancel:
                    event.ignore()
                    return
                elif reply == QMessageBox.Save:
                    self.save_all()
            
            # Stop timers
            self.auto_save_timer.stop()
            
            event.accept()
            logger.info("Application closing")
        except Exception as e:
            logger.error(f"Error during close: {str(e)}")
            event.accept()
