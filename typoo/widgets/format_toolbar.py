"""
Format toolbar for text formatting options.
"""

from PySide6.QtWidgets import QToolBar, QSpinBox, QComboBox, QLabel
from PySide6.QtGui import QAction, QFont, QIcon
from PySide6.QtCore import Signal as pyqtSignal

from typoo.logger import Logger

logger = Logger.get()


class FormatToolbar(QToolBar):
    """Toolbar for formatting options."""
    
    # Signals
    bold_clicked = pyqtSignal()
    italic_clicked = pyqtSignal()
    underline_clicked = pyqtSignal()
    strikethrough_clicked = pyqtSignal()
    heading_clicked = pyqtSignal(int)
    list_clicked = pyqtSignal(bool)  # True for ordered, False for unordered
    quote_clicked = pyqtSignal()
    code_clicked = pyqtSignal()
    link_clicked = pyqtSignal()
    table_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__("Format", parent)
        self.setup_toolbar()
    
    def setup_toolbar(self) -> None:
        """Setup toolbar items."""
        # Bold
        bold_action = QAction("B", self)
        bold_action.setCheckable(True)
        bold_action.setToolTip("Bold (Ctrl+B)")
        bold_action.triggered.connect(self.bold_clicked.emit)
        self.addAction(bold_action)
        
        # Italic
        italic_action = QAction("I", self)
        italic_action.setCheckable(True)
        italic_action.setToolTip("Italic (Ctrl+I)")
        italic_action.triggered.connect(self.italic_clicked.emit)
        self.addAction(italic_action)
        
        # Underline
        underline_action = QAction("U", self)
        underline_action.setCheckable(True)
        underline_action.setToolTip("Underline (Ctrl+U)")
        underline_action.triggered.connect(self.underline_clicked.emit)
        self.addAction(underline_action)
        
        # Strikethrough
        strike_action = QAction("S", self)
        strike_action.setToolTip("Strikethrough")
        strike_action.triggered.connect(self.strikethrough_clicked.emit)
        self.addAction(strike_action)
        
        self.addSeparator()
        
        # Heading dropdown
        heading_label = QLabel("Heading: ")
        self.addWidget(heading_label)
        heading_combo = QComboBox()
        heading_combo.addItems(["None", "H1", "H2", "H3", "H4", "H5", "H6"])
        heading_combo.currentIndexChanged.connect(
            lambda idx: self.heading_clicked.emit(idx) if idx > 0 else None
        )
        self.addWidget(heading_combo)
        
        self.addSeparator()
        
        # Unordered list
        ul_action = QAction("• List", self)
        ul_action.setToolTip("Unordered List")
        ul_action.triggered.connect(lambda: self.list_clicked.emit(False))
        self.addAction(ul_action)
        
        # Ordered list
        ol_action = QAction("1. List", self)
        ol_action.setToolTip("Ordered List")
        ol_action.triggered.connect(lambda: self.list_clicked.emit(True))
        self.addAction(ol_action)
        
        self.addSeparator()
        
        # Quote
        quote_action = QAction("> Quote", self)
        quote_action.setToolTip("Blockquote")
        quote_action.triggered.connect(self.quote_clicked.emit)
        self.addAction(quote_action)
        
        self.addSeparator()
        
        # Code
        code_action = QAction("` Code", self)
        code_action.setToolTip("Code Block")
        code_action.triggered.connect(self.code_clicked.emit)
        self.addAction(code_action)
        
        self.addSeparator()
        
        # Link
        link_action = QAction("🔗 Link", self)
        link_action.setToolTip("Insert Link")
        link_action.triggered.connect(self.link_clicked.emit)
        self.addAction(link_action)
