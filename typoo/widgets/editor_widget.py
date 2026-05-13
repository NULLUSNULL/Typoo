"""
Main editor widget with multiple panels.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QMessageBox
from PySide6.QtCore import Qt, Signal as pyqtSignal

from typoo.widgets.tab_widget import TabWidget
from typoo.config import Config

class EditorWidget(QWidget):
    """Main editor area with multiple panels support."""
    
    document_saved = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup editor UI with splitters."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create main horizontal splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # Create tab widgets for each panel
        self.panels = []
        
        # Left panel
        left_panel = TabWidget()
        self.panels.append(left_panel)
        self.main_splitter.addWidget(left_panel)
        
        # Center panel (main)
        center_panel = TabWidget()
        self.panels.append(center_panel)
        self.main_splitter.addWidget(center_panel)
        
        # Right panel
        right_panel = TabWidget()
        self.panels.append(right_panel)
        self.main_splitter.addWidget(right_panel)
        
        # Set initial sizes
        self.main_splitter.setSizes(Config.DEFAULT_PANEL_WIDTHS)
        
        # Allow collapsing
        self.main_splitter.setCollapsible(0, True)
        self.main_splitter.setCollapsible(1, False)  # Main panel cannot collapse
        self.main_splitter.setCollapsible(2, True)
        
        layout.addWidget(self.main_splitter)
        
        # Hide side panels initially
        self.panels[0].hide()
        self.panels[2].hide()
    
    def get_main_panel(self) -> TabWidget:
        """Get main center panel."""
        return self.panels[1]
    
    def get_left_panel(self) -> TabWidget:
        """Get left side panel."""
        return self.panels[0]
    
    def get_right_panel(self) -> TabWidget:
        """Get right side panel."""
        return self.panels[2]
    
    def toggle_left_panel(self, visible: bool = None) -> None:
        """Toggle left panel visibility."""
        if visible is None:
            visible = not self.panels[0].isVisible()
        
        self.panels[0].setVisible(visible)
        if visible:
            self.main_splitter.setSizes([200, 600, 0])
    
    def toggle_right_panel(self, visible: bool = None) -> None:
        """Toggle right panel visibility."""
        if visible is None:
            visible = not self.panels[2].isVisible()
        
        self.panels[2].setVisible(visible)
        if visible:
            self.main_splitter.setSizes([0, 600, 200])
    
    def save_all(self) -> None:
        """Save all open documents."""
        for panel in self.panels:
            for i in range(panel.count()):
                panel.save_document(i)
    
    def close_all(self) -> bool:
        """Close all open documents."""
        for panel in self.panels:
            # Close tabs in reverse order to maintain indices
            for i in range(panel.count() - 1, -1, -1):
                if not panel.close_document(i):
                    return False
        return True
