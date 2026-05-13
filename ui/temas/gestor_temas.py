# ui/temas/gestor_temas.py
# Gestión de temas visuales claro y oscuro mediante hojas de estilo Qt (QSS)

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core.constantes import Tema


def _iconos_dir() -> Path:
    """Devuelve el directorio de iconos compatible con entorno dev y exe compilado."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "assets" / "iconos"
    return Path(__file__).parent.parent.parent / "assets" / "iconos"


_ICONOS = _iconos_dir()


def _url(nombre: str) -> str:
    """Devuelve una ruta forward-slash compatible con url() en QSS."""
    return str(_ICONOS / nombre).replace("\\", "/")


def _qss_oscuro() -> str:
    au  = _url("arrow-up-light.svg")
    ad  = _url("arrow-down-light.svg")
    bco = _url("branch-closed-oscuro.svg")
    boo = _url("branch-open-oscuro.svg")
    return f"""
QMainWindow, QDialog {{
    background-color: #282C34;
    color: #ABB2BF;
}}

QWidget {{
    background-color: #282C34;
    color: #ABB2BF;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}}

/* ── Barra de menú ─────────────────────────────────────────────────── */
QMenuBar {{
    background-color: #21252B;
    color: #ABB2BF;
    border-bottom: 1px solid #181A1F;
    padding: 2px;
}}
QMenuBar::item:selected {{
    background-color: #3E4451;
    border-radius: 3px;
}}
QMenu {{
    background-color: #21252B;
    color: #ABB2BF;
    border: 1px solid #181A1F;
    padding: 4px;
}}
QMenu::item:selected {{
    background-color: #528BFF;
    color: #FFFFFF;
    border-radius: 3px;
}}
QMenu::separator {{
    height: 1px;
    background: #3E4451;
    margin: 4px 8px;
}}

/* ── Barra de herramientas ─────────────────────────────────────────── */
QToolBar {{
    background-color: #21252B;
    border-bottom: 1px solid #181A1F;
    spacing: 2px;
    padding: 3px 6px;
}}
QToolButton {{
    background-color: transparent;
    color: #ABB2BF;
    border: 1px solid transparent;
    border-radius: 3px;
    padding: 3px 5px;
}}
QToolButton:hover {{
    background-color: #3E4451;
    border-color: #528BFF;
}}
QToolButton:pressed {{
    background-color: #528BFF;
    color: #FFFFFF;
}}

/* ── Barra herramientas de formato (widget personalizado) ─────────── */
QWidget#BarraHerramientas {{
    background-color: #21252B;
    border-bottom: 1px solid #181A1F;
}}
QFrame#SeparadorBarraFormato {{
    background-color: #181A1F;
    border: none;
    min-height: 1px;
    max-height: 1px;
}}

/* ── Árbol del explorador ─────────────────────────────────────────── */
QTreeWidget {{
    background-color: #21252B;
    color: #ABB2BF;
    border: none;
    font-size: 13px;
    outline: none;
}}
QTreeWidget::item {{
    padding: 3px 4px;
    border-radius: 3px;
}}
QTreeWidget::item:hover {{ background-color: #2C313A; }}
QTreeWidget::item:selected {{ background-color: #2C67E0; color: #FFFFFF; }}
QTreeWidget::branch {{
    background: transparent;
}}
QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {{
    border-image: none;
    image: url({bco});
}}
QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {{
    border-image: none;
    image: url({boo});
}}

/* ── Editor de texto ──────────────────────────────────────────────── */
QPlainTextEdit {{
    background-color: #1E2227;
    color: #ABB2BF;
    border: none;
    selection-background-color: #3E4451;
    selection-color: #DCDFE4;
    font-family: "Courier New", Consolas, monospace;
}}
QPlainTextEdit:focus {{ border: 1px solid #528BFF; }}

/* ── Panel de pestañas ────────────────────────────────────────────── */
QTabWidget::pane {{
    border: none;
    background-color: #1E2227;
}}
QTabBar {{
    background-color: #21252B;
}}
QTabBar::tab {{
    background-color: #21252B;
    color: #7F848E;
    padding: 6px 12px;
    border-bottom: 2px solid transparent;
    min-width: 80px;
}}
QTabBar::tab:selected {{
    color: #DCDFE4;
    border-bottom: 2px solid #528BFF;
    background-color: #282C34;
}}
QTabBar::tab:hover:!selected {{
    color: #ABB2BF;
    background-color: #2C313A;
}}
QTabBar::close-button {{
    subcontrol-position: right;
}}

/* ── Botón × de cierre de pestaña ────────────────────────────────── */
QPushButton#BotonCerrarPestana {{
    background-color: transparent;
    color: #7F848E;
    border: none;
    border-radius: 3px;
    font-size: 14px;
    font-weight: bold;
    padding: 0px;
}}
QPushButton#BotonCerrarPestana:hover {{
    background-color: #C0392B;
    color: #FFFFFF;
}}
QPushButton#BotonCerrarPestana:pressed {{
    background-color: #992D22;
    color: #FFFFFF;
}}

/* ── Barra de estado ──────────────────────────────────────────────── */
QStatusBar {{
    background-color: #21252B;
    color: #7F848E;
    border-top: 1px solid #181A1F;
    font-size: 12px;
}}
QStatusBar::item {{ border: none; }}

/* ── Splitter ─────────────────────────────────────────────────────── */
QSplitter::handle {{
    background-color: #181A1F;
    width: 2px;
    height: 2px;
}}
QSplitter::handle:hover {{ background-color: #528BFF; }}

/* ── Cabeceras de paneles ─────────────────────────────────────────── */
QLabel#CabeceraPanel {{
    background-color: #21252B;
    color: #7F848E;
    border-bottom: 1px solid #181A1F;
    font-size: 11px;
    padding-left: 6px;
}}

/* ── Cuadros de texto ─────────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: #2C313A;
    color: #ABB2BF;
    border: 1px solid #3E4451;
    border-radius: 4px;
    padding: 4px 6px;
}}
QLineEdit:focus, QTextEdit:focus {{ border-color: #528BFF; }}

/* ── Botones ──────────────────────────────────────────────────────── */
QPushButton {{
    background-color: #3E4451;
    color: #ABB2BF;
    border: 1px solid #4B5263;
    border-radius: 4px;
    padding: 5px 14px;
}}
QPushButton:hover {{
    background-color: #528BFF;
    color: #FFFFFF;
    border-color: #528BFF;
}}
QPushButton:pressed {{ background-color: #4070C8; }}
QPushButton:default {{ border-color: #528BFF; }}

/* ── ComboBox ─────────────────────────────────────────────────────── */
QComboBox {{
    background-color: #2C313A;
    color: #ABB2BF;
    border: 1px solid #3E4451;
    border-radius: 4px;
    padding: 3px 6px;
}}
QComboBox QAbstractItemView {{
    background-color: #21252B;
    color: #ABB2BF;
    selection-background-color: #528BFF;
}}

/* ── Spinbox ──────────────────────────────────────────────────────── */
QSpinBox {{
    background-color: #2C313A;
    color: #ABB2BF;
    border: 1px solid #3E4451;
    border-radius: 4px;
    padding: 3px 22px 3px 6px;
}}
QSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    background-color: #3E4451;
    border-left: 1px solid #4B5263;
    border-top-right-radius: 3px;
}}
QSpinBox::up-button:hover {{ background-color: #528BFF; }}
QSpinBox::up-button:pressed {{ background-color: #4070C8; }}
QSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    background-color: #3E4451;
    border-left: 1px solid #4B5263;
    border-bottom-right-radius: 3px;
}}
QSpinBox::down-button:hover {{ background-color: #528BFF; }}
QSpinBox::down-button:pressed {{ background-color: #4070C8; }}
QSpinBox::up-arrow {{
    image: url({au});
    width: 10px;
    height: 6px;
}}
QSpinBox::down-arrow {{
    image: url({ad});
    width: 10px;
    height: 6px;
}}

/* ── ScrollBar ────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background-color: #21252B;
    width: 8px;
}}
QScrollBar::handle:vertical {{
    background-color: #4B5263;
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background-color: #528BFF; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{
    background-color: #21252B;
    height: 8px;
}}
QScrollBar::handle:horizontal {{
    background-color: #4B5263;
    border-radius: 4px;
    min-width: 30px;
}}

/* ── Diálogos ─────────────────────────────────────────────────────── */
QDialogButtonBox QPushButton {{ min-width: 90px; }}
QGroupBox {{
    color: #ABB2BF;
    border: 1px solid #3E4451;
    border-radius: 5px;
    margin-top: 8px;
    padding-top: 6px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: #7F848E;
}}

/* ── CheckBox ─────────────────────────────────────────────────────── */
QCheckBox {{
    spacing: 6px;
    color: #ABB2BF;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid #4B5263;
    border-radius: 3px;
    background-color: #2C313A;
}}
QCheckBox::indicator:checked {{
    background-color: #528BFF;
    border-color: #528BFF;
}}

/* ── RadioButton ──────────────────────────────────────────────────── */
QRadioButton {{
    spacing: 6px;
    color: #ABB2BF;
}}
QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid #4B5263;
    border-radius: 8px;
    background-color: #2C313A;
}}
QRadioButton::indicator:checked {{
    border: 4px solid #528BFF;
    background-color: #ABB2BF;
    border-radius: 8px;
}}
QRadioButton::indicator:hover {{
    border-color: #528BFF;
}}
"""


def _qss_claro() -> str:
    """Tema inspirado en macOS: grises neutros, blanco puro en editor, azul sistema."""
    au  = _url("arrow-up-dark.svg")
    ad  = _url("arrow-down-dark.svg")
    bcc = _url("branch-closed-claro.svg")
    boc = _url("branch-open-claro.svg")
    return f"""
QMainWindow, QDialog {{
    background-color: #F5F5F7;
    color: #1D1D1F;
}}
QWidget {{
    background-color: #F5F5F7;
    color: #1D1D1F;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}}

/* ── Barra de menú ─────────────────────────────────────────────────── */
QMenuBar {{
    background-color: #EBEBF0;
    color: #1D1D1F;
    border-bottom: 1px solid #D1D1D6;
    padding: 2px;
}}
QMenuBar::item:selected {{ background-color: #D4E4FF; border-radius: 3px; }}
QMenu {{
    background-color: #FFFFFF;
    color: #1D1D1F;
    border: 1px solid #D1D1D6;
    padding: 4px;
}}
QMenu::item:selected {{ background-color: #007AFF; color: #FFFFFF; border-radius: 3px; }}
QMenu::separator {{ height: 1px; background: #D1D1D6; margin: 4px 8px; }}

/* ── Barra de herramientas ─────────────────────────────────────────── */
QToolBar {{
    background-color: #EBEBF0;
    border-bottom: 1px solid #D1D1D6;
    spacing: 2px;
    padding: 3px 6px;
}}
QToolButton {{
    background-color: transparent;
    color: #1D1D1F;
    border: 1px solid transparent;
    border-radius: 3px;
    padding: 3px 5px;
}}
QToolButton:hover {{ background-color: #D4E4FF; border-color: #007AFF; }}
QToolButton:pressed {{ background-color: #007AFF; color: #FFFFFF; }}

/* ── Barra herramientas de formato ────────────────────────────────── */
QWidget#BarraHerramientas {{ background-color: #EBEBF0; }}
QFrame#SeparadorBarraFormato {{
    background-color: #D1D1D6;
    border: none;
    min-height: 1px;
    max-height: 1px;
}}

/* ── Árbol del explorador ─────────────────────────────────────────── */
QTreeWidget {{
    background-color: #E8E8ED;
    color: #1D1D1F;
    border: none;
    outline: none;
}}
QTreeWidget::item {{ padding: 3px 4px; border-radius: 3px; }}
QTreeWidget::item:hover {{ background-color: #D8D8DE; }}
QTreeWidget::item:selected {{ background-color: #007AFF; color: #FFFFFF; }}
QTreeWidget::branch {{
    background: transparent;
}}
QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {{
    border-image: none;
    image: url({bcc});
}}
QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {{
    border-image: none;
    image: url({boc});
}}

/* ── Editor de texto ──────────────────────────────────────────────── */
QPlainTextEdit {{
    background-color: #FFFFFF;
    color: #1D1D1F;
    border: none;
    selection-background-color: #CCE0FF;
    selection-color: #1D1D1F;
    font-family: "Courier New", Consolas, monospace;
}}
QPlainTextEdit:focus {{ border: 1px solid #007AFF; }}

/* ── Panel de pestañas ────────────────────────────────────────────── */
QTabWidget::pane {{ border: none; background-color: #FFFFFF; }}
QTabBar {{ background-color: #E8E8ED; }}
QTabBar::tab {{
    background-color: #E8E8ED;
    color: #6E6E73;
    padding: 6px 12px;
    border-bottom: 2px solid transparent;
    min-width: 80px;
}}
QTabBar::tab:selected {{
    color: #1D1D1F;
    border-bottom: 2px solid #007AFF;
    background-color: #FFFFFF;
}}
QTabBar::tab:hover:!selected {{ color: #3A3A3C; background-color: #DCDCE4; }}
QTabBar::close-button {{ subcontrol-position: right; }}

/* ── Botón × de cierre de pestaña ────────────────────────────────── */
QPushButton#BotonCerrarPestana {{
    background-color: transparent;
    color: #8E8E93;
    border: none;
    border-radius: 3px;
    font-size: 14px;
    font-weight: bold;
    padding: 0px;
}}
QPushButton#BotonCerrarPestana:hover {{ background-color: #FF3B30; color: #FFFFFF; }}
QPushButton#BotonCerrarPestana:pressed {{ background-color: #C0392B; color: #FFFFFF; }}

/* ── Barra de estado ──────────────────────────────────────────────── */
QStatusBar {{
    background-color: #EBEBF0;
    color: #6E6E73;
    border-top: 1px solid #D1D1D6;
    font-size: 12px;
}}
QStatusBar::item {{ border: none; }}

/* ── Splitter ─────────────────────────────────────────────────────── */
QSplitter::handle {{ background-color: #D1D1D6; width: 2px; height: 2px; }}
QSplitter::handle:hover {{ background-color: #007AFF; }}
QLabel#CabeceraPanel {{
    background-color: #E8E8ED;
    color: #6E6E73;
    border-bottom: 1px solid #D1D1D6;
    font-size: 11px;
    padding-left: 6px;
}}

/* ── Cuadros de texto ─────────────────────────────────────────────── */
QLineEdit, QTextEdit {{
    background-color: #FFFFFF;
    color: #1D1D1F;
    border: 1px solid #D1D1D6;
    border-radius: 4px;
    padding: 4px 6px;
}}
QLineEdit:focus, QTextEdit:focus {{ border-color: #007AFF; }}

/* ── Botones ──────────────────────────────────────────────────────── */
QPushButton {{
    background-color: #EBEBF0;
    color: #1D1D1F;
    border: 1px solid #D1D1D6;
    border-radius: 4px;
    padding: 5px 14px;
}}
QPushButton:hover {{ background-color: #007AFF; color: #FFFFFF; border-color: #007AFF; }}
QPushButton:pressed {{ background-color: #0062CC; color: #FFFFFF; }}
QPushButton:default {{ border-color: #007AFF; }}

/* ── ComboBox ─────────────────────────────────────────────────────── */
QComboBox {{
    background-color: #FFFFFF;
    color: #1D1D1F;
    border: 1px solid #D1D1D6;
    border-radius: 4px;
    padding: 3px 6px;
}}
QComboBox QAbstractItemView {{
    background-color: #FFFFFF;
    color: #1D1D1F;
    selection-background-color: #007AFF;
    selection-color: #FFFFFF;
}}

/* ── Spinbox ──────────────────────────────────────────────────────── */
QSpinBox {{
    background-color: #FFFFFF;
    color: #1D1D1F;
    border: 1px solid #D1D1D6;
    border-radius: 4px;
    padding: 3px 22px 3px 6px;
}}
QSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    background-color: #EBEBF0;
    border-left: 1px solid #D1D1D6;
    border-top-right-radius: 3px;
}}
QSpinBox::up-button:hover {{ background-color: #007AFF; }}
QSpinBox::up-button:pressed {{ background-color: #0062CC; }}
QSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    background-color: #EBEBF0;
    border-left: 1px solid #D1D1D6;
    border-bottom-right-radius: 3px;
}}
QSpinBox::down-button:hover {{ background-color: #007AFF; }}
QSpinBox::down-button:pressed {{ background-color: #0062CC; }}
QSpinBox::up-arrow {{
    image: url({au});
    width: 10px;
    height: 6px;
}}
QSpinBox::down-arrow {{
    image: url({ad});
    width: 10px;
    height: 6px;
}}

/* ── ScrollBar ────────────────────────────────────────────────────── */
QScrollBar:vertical {{ background-color: #F0F0F5; width: 8px; }}
QScrollBar::handle:vertical {{
    background-color: #C7C7CC;
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background-color: #007AFF; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{ background-color: #F0F0F5; height: 8px; }}
QScrollBar::handle:horizontal {{
    background-color: #C7C7CC;
    border-radius: 4px;
    min-width: 30px;
}}

/* ── Diálogos ─────────────────────────────────────────────────────── */
QDialogButtonBox QPushButton {{ min-width: 90px; }}
QGroupBox {{
    color: #1D1D1F;
    border: 1px solid #D1D1D6;
    border-radius: 5px;
    margin-top: 8px;
    padding-top: 6px;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #6E6E73; }}

/* ── CheckBox ─────────────────────────────────────────────────────── */
QCheckBox {{ spacing: 6px; color: #1D1D1F; }}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid #D1D1D6;
    border-radius: 3px;
    background-color: #FFFFFF;
}}
QCheckBox::indicator:checked {{ background-color: #007AFF; border-color: #007AFF; }}

/* ── RadioButton ──────────────────────────────────────────────────── */
QRadioButton {{ spacing: 6px; color: #1D1D1F; }}
QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid #D1D1D6;
    border-radius: 8px;
    background-color: #FFFFFF;
}}
QRadioButton::indicator:checked {{
    border: 4px solid #007AFF;
    background-color: #CCE0FF;
    border-radius: 8px;
}}
QRadioButton::indicator:hover {{ border-color: #007AFF; }}
"""


# ─── Gestor de temas ─────────────────────────────────────────────────────────

class GestorTemas:
    """Aplica el tema visual seleccionado a toda la aplicación Qt."""

    @staticmethod
    def aplicar(tema: Tema) -> None:
        app = QApplication.instance()
        if app is None:
            return
        if tema == Tema.OSCURO:
            app.setStyleSheet(_qss_oscuro())
        else:
            app.setStyleSheet(_qss_claro())

    @staticmethod
    def alternar(tema_actual: Tema) -> Tema:
        return Tema.CLARO if tema_actual == Tema.OSCURO else Tema.OSCURO
