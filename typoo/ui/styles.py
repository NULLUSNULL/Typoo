"""
Style and theme management.
"""

from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QApplication


class StyleManager:
    """Manages application styles and themes."""
    
    # Dark theme colors
    DARK_BG = "#2b2b2b"
    DARK_FG = "#ffffff"
    DARK_ACCENT = "#0d47a1"
    DARK_EDITOR_BG = "#1e1e1e"
    
    # Light theme colors
    LIGHT_BG = "#ffffff"
    LIGHT_FG = "#000000"
    LIGHT_ACCENT = "#1976d2"
    LIGHT_EDITOR_BG = "#f5f5f5"
    
    @staticmethod
    def apply_dark_theme(app: QApplication) -> None:
        """Apply dark theme to application."""
        stylesheet = """
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            
            QMenuBar {
                background-color: #2b2b2b;
                color: #ffffff;
                border-bottom: 1px solid #444444;
            }
            
            QMenuBar::item:selected {
                background-color: #0d47a1;
            }
            
            QMenu {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            
            QMenu::item:selected {
                background-color: #0d47a1;
            }
            
            QToolBar {
                background-color: #333333;
                color: #ffffff;
                border-bottom: 1px solid #444444;
            }
            
            QPushButton {
                background-color: #0d47a1;
                color: #ffffff;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            
            QPushButton:hover {
                background-color: #1565c0;
            }
            
            QPushButton:pressed {
                background-color: #0b3d91;
            }
            
            QTreeWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #444444;
            }
            
            QTreeWidget::item:selected {
                background-color: #0d47a1;
            }
            
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: none;
            }
            
            QStatusBar {
                background-color: #333333;
                color: #ffffff;
                border-top: 1px solid #444444;
            }
            
            QTabBar::tab {
                background-color: #333333;
                color: #ffffff;
                padding: 8px;
                border: 1px solid #444444;
            }
            
            QTabBar::tab:selected {
                background-color: #0d47a1;
            }
            
            QTabWidget::pane {
                border: 1px solid #444444;
            }
            
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            
            QLineEdit, QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #444444;
                padding: 5px;
                border-radius: 3px;
            }
            
            QComboBox {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #444444;
                padding: 5px;
            }
            
            QComboBox::drop-down {
                background-color: #0d47a1;
            }
            
            QSpinBox, QDoubleSpinBox {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #444444;
            }
        """
        app.setStyle("Fusion")
        app.setStyleSheet(stylesheet)
    
    @staticmethod
    def apply_light_theme(app: QApplication) -> None:
        """Apply light theme to application."""
        stylesheet = """
            QMainWindow {
                background-color: #ffffff;
                color: #000000;
            }
            
            QMenuBar {
                background-color: #f5f5f5;
                color: #000000;
                border-bottom: 1px solid #e0e0e0;
            }
            
            QMenuBar::item:selected {
                background-color: #1976d2;
                color: #ffffff;
            }
            
            QMenu {
                background-color: #ffffff;
                color: #000000;
            }
            
            QMenu::item:selected {
                background-color: #1976d2;
                color: #ffffff;
            }
            
            QToolBar {
                background-color: #fafafa;
                color: #000000;
                border-bottom: 1px solid #e0e0e0;
            }
            
            QPushButton {
                background-color: #1976d2;
                color: #ffffff;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            
            QPushButton:hover {
                background-color: #1565c0;
            }
            
            QTreeWidget {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #e0e0e0;
            }
            
            QTreeWidget::item:selected {
                background-color: #1976d2;
                color: #ffffff;
            }
            
            QStatusBar {
                background-color: #fafafa;
                color: #000000;
                border-top: 1px solid #e0e0e0;
            }
            
            QTabBar::tab {
                background-color: #f5f5f5;
                color: #000000;
                padding: 8px;
                border: 1px solid #e0e0e0;
            }
            
            QTabBar::tab:selected {
                background-color: #1976d2;
                color: #ffffff;
            }
            
            QDialog {
                background-color: #ffffff;
                color: #000000;
            }
            
            QLineEdit, QTextEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
                padding: 5px;
                border-radius: 3px;
            }
            
            QComboBox {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
                padding: 5px;
            }
        """
        app.setStyle("Fusion")
        app.setStyleSheet(stylesheet)
