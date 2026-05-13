"""
Markdown syntax highlighter for Typoo.
"""

from PySide6.QtGui import QSyntaxHighlighter, QTextDocument, QTextCharFormat, QColor, QFont
from PySide6.QtCore import Qt
import re


class MarkdownHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Markdown documents."""
    
    def __init__(self, document: QTextDocument):
        super().__init__(document)
        self.setup_formats()
    
    def setup_formats(self) -> None:
        """Setup text formats for different Markdown elements."""
        # Headings
        self.heading_format = QTextCharFormat()
        self.heading_format.setForeground(QColor(31, 78, 121))
        self.heading_format.setFontWeight(QFont.Bold)
        self.heading_format.setFontPointSize(12)
        
        # Bold
        self.bold_format = QTextCharFormat()
        self.bold_format.setFontWeight(QFont.Bold)
        self.bold_format.setForeground(QColor(192, 0, 0))
        
        # Italic
        self.italic_format = QTextCharFormat()
        self.italic_format.setFontItalic(True)
        self.italic_format.setForeground(QColor(0, 112, 192))
        
        # Code
        self.code_format = QTextCharFormat()
        self.code_format.setForeground(QColor(163, 21, 21))
        self.code_format.setFontFamily("Courier New")
        
        # Links
        self.link_format = QTextCharFormat()
        self.link_format.setForeground(QColor(0, 0, 255))
        self.link_format.setFontUnderline(True)
        
        # Code blocks
        self.code_block_format = QTextCharFormat()
        self.code_block_format.setForeground(QColor(128, 128, 128))
        self.code_block_format.setFontFamily("Courier New")
        
        # Lists
        self.list_format = QTextCharFormat()
        self.list_format.setForeground(QColor(0, 100, 0))
        self.list_format.setFontWeight(QFont.Bold)
    
    def highlightBlock(self, text: str) -> None:
        """Highlight a block of text."""
        # Highlight headings
        heading_regex = re.compile(r'^#+\s+')
        for match in heading_regex.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.heading_format)
        
        # Highlight bold text
        for match in re.finditer(r'\*\*([^\*]+)\*\*', text):
            self.setFormat(match.start(), match.end() - match.start(), self.bold_format)
        
        for match in re.finditer(r'__([^_]+)__', text):
            self.setFormat(match.start(), match.end() - match.start(), self.bold_format)
        
        # Highlight italic text
        for match in re.finditer(r'\*([^\*]+)\*', text):
            self.setFormat(match.start(), match.end() - match.start(), self.italic_format)
        
        for match in re.finditer(r'_([^_]+)_', text):
            self.setFormat(match.start(), match.end() - match.start(), self.italic_format)
        
        # Highlight inline code
        for match in re.finditer(r'`([^`]+)`', text):
            self.setFormat(match.start(), match.end() - match.start(), self.code_format)
        
        # Highlight links
        for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', text):
            self.setFormat(match.start(), match.end() - match.start(), self.link_format)
        
        # Highlight lists
        list_regex = re.compile(r'^[\s]*[\*\-\+]\s+')
        for match in list_regex.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.list_format)
        
        # Check for code blocks (triple backticks)
        if text.strip().startswith('```'):
            self.setFormat(0, len(text), self.code_block_format)
