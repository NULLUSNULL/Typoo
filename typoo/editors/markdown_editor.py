"""
Main Markdown editor widget.
"""

from PySide6.QtWidgets import QPlainTextEdit, QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QFont, QKeySequence
from PySide6.QtCore import Qt, Signal as pyqtSignal

from typoo.editors.syntax_highlighter import MarkdownHighlighter
from typoo.config import Config
from typoo.logger import Logger

logger = Logger.get()


class MarkdownEditor(QPlainTextEdit):
    """Advanced Markdown editor widget."""
    
    content_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_editor()
        self.highlighter = MarkdownHighlighter(self.document())
        self.textChanged.connect(self._on_text_changed)
    
    def setup_editor(self) -> None:
        """Setup editor properties."""
        # Font
        font = QFont(Config.EDITOR_FONT_FAMILY)
        font.setPointSize(Config.EDITOR_FONT_SIZE)
        font.setFixedPitch(True)
        self.setFont(font)
        
        # Word wrap
        self.setWordWrapMode(Config.EDITOR_WRAP)
        
        # Tab size
        self.setTabStopDistance(Config.TAB_SIZE * 4)
        
        # Margins
        self.setMargins(10, 10, 10, 10)
        
        # Style
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #f5f5f5;
                color: #333333;
                border: none;
                border-radius: 0px;
            }
        """)
    
    def set_content(self, content: str) -> None:
        """Set editor content without triggering change signal."""
        self.blockSignals(True)
        self.setPlainText(content)
        self.blockSignals(False)
    
    def get_content(self) -> str:
        """Get editor content."""
        return self.toPlainText()
    
    def _on_text_changed(self) -> None:
        """Handle text change."""
        self.content_changed.emit(self.toPlainText())
    
    def insert_formatting(self, prefix: str, suffix: str = "", selected_text: str = "") -> None:
        """
        Insert formatting around selected text.
        
        Args:
            prefix: Text to insert before
            suffix: Text to insert after (default: prefix)
            selected_text: Text to wrap (uses current selection if empty)
        """
        if not suffix:
            suffix = prefix
        
        cursor = self.textCursor()
        
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
        
        if selected_text:
            formatted_text = f"{prefix}{selected_text}{suffix}"
            cursor.insertText(formatted_text)
        else:
            cursor.insertText(f"{prefix}{suffix}")
            # Move cursor to middle
            cursor.movePosition(cursor.MoveOperation.Left, cursor.MoveMode.MoveAnchor, len(suffix))
        
        self.setTextCursor(cursor)
    
    def insert_heading(self, level: int) -> None:
        """Insert heading of specified level."""
        prefix = "#" * min(level, 6) + " "
        self.insert_formatting(prefix)
    
    def insert_list(self, ordered: bool = False) -> None:
        """Insert list marker."""
        prefix = "1. " if ordered else "- "
        self.insert_formatting(prefix)
    
    def insert_quote(self) -> None:
        """Insert blockquote."""
        self.insert_formatting("> ")
    
    def insert_code_block(self) -> None:
        """Insert code block."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            code_block = f"```\n{selected_text}\n```"
            cursor.insertText(code_block)
        else:
            code_block = "```\n\n```"
            cursor.insertText(code_block)
            cursor.movePosition(cursor.MoveOperation.Up, cursor.MoveMode.MoveAnchor)
        
        self.setTextCursor(cursor)
    
    def insert_link(self, url: str = "", text: str = "") -> None:
        """Insert link."""
        if not text:
            text = "Link text"
        if not url:
            url = "https://example.com"
        
        self.insert_formatting(f"[{text}](", f"{url})")
    
    def get_word_count(self) -> int:
        """Get word count for editor content."""
        from typoo.utils import MarkdownUtils
        return MarkdownUtils.count_words(self.get_content())
    
    def get_stats(self) -> dict:
        """Get statistics about content."""
        from typoo.utils import MarkdownUtils
        return MarkdownUtils.get_markdown_stats(self.get_content())
