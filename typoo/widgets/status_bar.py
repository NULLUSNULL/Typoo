"""
Status bar widget.
"""

from PySide6.QtWidgets import QStatusBar, QLabel
from PySide6.QtCore import Qt


class StatusBar(QStatusBar):
    """Custom status bar with word count and more."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup status bar elements."""
        # Word count label
        self.word_count_label = QLabel("Words: 0")
        self.addWidget(self.word_count_label)
        
        # Character count label
        self.char_count_label = QLabel("Characters: 0")
        self.addPermanentWidget(self.char_count_label)
        
        # Line count label
        self.line_count_label = QLabel("Lines: 0")
        self.addPermanentWidget(self.line_count_label)
    
    def update_stats(self, word_count: int, char_count: int, line_count: int) -> None:
        """Update statistics display."""
        self.word_count_label.setText(f"Words: {word_count}")
        self.char_count_label.setText(f"Characters: {char_count}")
        self.line_count_label.setText(f"Lines: {line_count}")
    
    def set_message(self, message: str, timeout: int = 0) -> None:
        """Show a temporary message."""
        self.showMessage(message, timeout)
