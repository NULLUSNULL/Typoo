# ui/temas/gestor_temas.py
# Gestión de temas visuales claro y oscuro mediante hojas de estilo Qt (QSS).
# Estética inspirada en macOS: superficies suaves, esquinas redondeadas,
# tipografía del sistema y el azul de acento de Apple.

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

# Pila tipográfica del sistema (SF en macOS, Segoe en Windows, etc.)
_FUENTE_UI = '"-apple-system", "SF Pro Text", "Segoe UI", "Helvetica Neue", "Inter", Arial, sans-serif'


def _url(nombre: str) -> str:
    """Devuelve una ruta forward-slash compatible con url() en QSS."""
    return str(_ICONOS / nombre).replace("\\", "/")


def _qss_oscuro() -> str:
    """Tema oscuro estilo macOS (Big Sur / Sonoma)."""
    au  = _url("arrow-up-light.svg")
    ad  = _url("arrow-down-light.svg")
    bco = _url("branch-closed-oscuro.svg")
    boo = _url("branch-open-oscuro.svg")

    # Paleta
    fondo       = "#1E1E20"   # ventana / contenido
    barra       = "#2A2A2C"   # barras, sidebar
    elevado     = "#3A3A3C"   # menús, inputs, controles
    elevado2    = "#48484A"   # bordes de control
    editor_bg   = "#1A1A1C"   # lienzo del editor
    borde       = "#36363A"   # separadores
    texto       = "#EBEBF0"   # texto principal
    texto2      = "#A0A0A6"   # texto secundario
    texto3      = "#6E6E73"   # texto terciario
    acento      = "#0A84FF"   # azul de sistema (modo oscuro)
    acento_hi   = "#3D9BFF"
    acento_lo   = "#0860C4"
    sel         = "#0A84FF"
    rojo        = "#FF453A"

    return _plantilla(
        fondo=fondo, barra=barra, elevado=elevado, elevado2=elevado2,
        editor_bg=editor_bg, borde=borde, texto=texto, texto2=texto2,
        texto3=texto3, acento=acento, acento_hi=acento_hi, acento_lo=acento_lo,
        sel=sel, rojo=rojo, au=au, ad=ad, bco=bco, boo=boo,
        hover="rgba(255, 255, 255, 0.07)",
    )


def _qss_claro() -> str:
    """Tema claro estilo macOS: grises neutros, blanco puro, azul de sistema."""
    au  = _url("arrow-up-dark.svg")
    ad  = _url("arrow-down-dark.svg")
    bcc = _url("branch-closed-claro.svg")
    boc = _url("branch-open-claro.svg")

    fondo       = "#ECECEE"
    barra       = "#F4F4F6"
    elevado     = "#FFFFFF"
    elevado2    = "#D4D4DA"
    editor_bg   = "#FFFFFF"
    borde       = "#D9D9DF"
    texto       = "#1D1D1F"
    texto2      = "#6E6E73"
    texto3      = "#8E8E93"
    acento      = "#007AFF"
    acento_hi   = "#3393FF"
    acento_lo   = "#0062CC"
    sel         = "#007AFF"
    rojo        = "#FF3B30"

    return _plantilla(
        fondo=fondo, barra=barra, elevado=elevado, elevado2=elevado2,
        editor_bg=editor_bg, borde=borde, texto=texto, texto2=texto2,
        texto3=texto3, acento=acento, acento_hi=acento_hi, acento_lo=acento_lo,
        sel=sel, rojo=rojo, au=au, ad=ad, bcc=bcc, boc=boc,
        hover="rgba(0, 0, 0, 0.05)",
    )


def _plantilla(
    *, fondo, barra, elevado, elevado2, editor_bg, borde, texto, texto2,
    texto3, acento, acento_hi, acento_lo, sel, rojo, hover,
    au, ad, bco=None, boo=None, bcc=None, boc=None,
) -> str:
    """Plantilla QSS común parametrizada por la paleta de cada tema."""
    cerrado = bco or bcc
    abierto = boo or boc

    return f"""
* {{
    font-family: {_FUENTE_UI};
}}

QMainWindow, QDialog {{
    background-color: {fondo};
    color: {texto};
}}
QWidget {{
    background-color: {fondo};
    color: {texto};
    font-size: 13px;
}}
/* Las etiquetas no pintan fondo: heredan el de su barra/panel y así se evita el
   efecto «parche» (recuadros de otro tono en la barra de estado, banner, etc.). */
QLabel {{ background: transparent; }}
QToolTip {{
    background-color: {elevado};
    color: {texto};
    border: 1px solid {borde};
    border-radius: 6px;
    padding: 4px 8px;
}}

/* ── Banner con el nombre de la aplicación ─────────────────────────── */
QWidget#BannerApp {{
    background-color: {barra};
    border-bottom: 1px solid {borde};
}}
QLabel#BannerTitulo {{
    color: {texto};
    letter-spacing: 0.5px;
}}

/* ── Barra de menú ─────────────────────────────────────────────────── */
QMenuBar {{
    background-color: {barra};
    color: {texto};
    border-bottom: 1px solid {borde};
    padding: 3px 6px;
}}
QMenuBar::item {{
    background: transparent;
    padding: 4px 10px;
    border-radius: 6px;
}}
QMenuBar::item:selected {{ background-color: {hover}; }}
QMenuBar::item:pressed  {{ background-color: {acento}; color: #FFFFFF; }}

QMenu {{
    background-color: {elevado};
    color: {texto};
    border: 1px solid {borde};
    border-radius: 8px;
    padding: 5px;
}}
QMenu::item {{
    padding: 6px 26px 6px 18px;
    border-radius: 6px;
}}
QMenu::item:selected {{ background-color: {acento}; color: #FFFFFF; }}
QMenu::separator {{ height: 1px; background: {borde}; margin: 5px 10px; }}
QMenu::indicator {{ width: 16px; height: 16px; left: 4px; }}

/* ── Barra de herramientas ─────────────────────────────────────────── */
QToolBar {{
    background-color: {barra};
    border: none;
    border-bottom: 1px solid {borde};
    spacing: 3px;
    padding: 4px 8px;
}}
QToolButton {{
    background-color: transparent;
    color: {texto};
    border: 1px solid transparent;
    border-radius: 7px;
    padding: 4px 7px;
}}
QToolButton:hover {{ background-color: {hover}; }}
QToolButton:pressed, QToolButton:checked {{
    background-color: {acento};
    color: #FFFFFF;
}}
QToolButton::menu-indicator {{ image: none; width: 0; }}

/* ── Barra de formato (widget personalizado) ──────────────────────── */
QWidget#BarraHerramientas {{
    background-color: {barra};
    border-bottom: 1px solid {borde};
}}
QFrame#SeparadorBarraFormato {{
    background-color: {borde};
    border: none;
    min-height: 1px;
    max-height: 1px;
}}

/* ── Árbol del explorador ─────────────────────────────────────────── */
QTreeWidget, QTreeView {{
    background-color: {barra};
    color: {texto};
    border: none;
    font-size: 13px;
    outline: none;
    show-decoration-selected: 0;
}}
QTreeWidget::item, QTreeView::item {{
    padding: 5px 4px;
    border-radius: 6px;
    margin: 1px 4px;
}}
QTreeWidget::item:hover, QTreeView::item:hover {{ background-color: {hover}; }}
QTreeWidget::item:selected, QTreeView::item:selected {{
    background-color: {acento};
    color: #FFFFFF;
}}
/* Fondo opaco de panel en la columna de ramas: así las flechas de despliegue
   quedan siempre sobre fondo neutro y la selección azul no las invade. */
QTreeWidget::branch {{ background-color: {barra}; }}
/* Ocultar las líneas guía por defecto de Qt (las «barras verticales») */
QTreeWidget::branch:has-siblings:!adjoins-item,
QTreeWidget::branch:has-siblings:adjoins-item,
QTreeWidget::branch:!has-children:!has-siblings:adjoins-item {{
    border-image: none;
    image: none;
}}
QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {{
    border-image: none;
    image: url({cerrado});
    background-color: {barra};
}}
QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {{
    border-image: none;
    image: url({abierto});
    background-color: {barra};
}}

/* ── Tablas (visor de tramas) ─────────────────────────────────────── */
QTableView {{
    background-color: {barra};
    alternate-background-color: {barra};
    color: {texto};
    gridline-color: {borde};
    border: none;
    selection-background-color: {acento};
    selection-color: #FFFFFF;
}}
QHeaderView::section {{
    background-color: {elevado};
    color: {texto};
    border: none;
    border-right: 1px solid {borde};
    border-bottom: 1px solid {borde};
    padding: 4px 6px;
}}
QTableCornerButton::section {{ background-color: {elevado}; border: none; }}

/* ── Editor de texto ──────────────────────────────────────────────── */
QPlainTextEdit#EditorMarkdown {{
    background-color: {editor_bg};
    color: {texto};
    border: none;
    selection-background-color: {sel};
    selection-color: #FFFFFF;
}}

/* ── Panel de pestañas ────────────────────────────────────────────── */
QTabWidget::pane {{ border: none; background-color: {editor_bg}; }}
QTabBar {{ background-color: {barra}; qproperty-drawBase: 0; }}
QTabBar::tab {{
    background-color: transparent;
    color: {texto2};
    padding: 7px 16px;
    margin: 4px 2px 0 2px;
    border: 1px solid transparent;
    border-radius: 7px;
    min-width: 70px;
}}
QTabBar::tab:selected {{
    color: {texto};
    background-color: {elevado};
    border: 1px solid {borde};
}}
QTabBar::tab:hover:!selected {{ color: {texto}; background-color: {hover}; }}
QTabBar::close-button {{ subcontrol-position: right; }}

/* ── Botón × de cierre de pestaña ─────────────────────────────────── */
QPushButton#BotonCerrarPestana {{
    background-color: transparent;
    color: {texto3};
    border: none;
    border-radius: 9px;
    padding: 0px;
    margin-right: 6px;
}}
QPushButton#BotonCerrarPestana:hover {{ background-color: {rojo}; color: #FFFFFF; }}
QPushButton#BotonCerrarPestana:pressed {{ background-color: {rojo}; color: #FFFFFF; }}

/* ── Barra de estado ──────────────────────────────────────────────── */
QStatusBar {{
    background-color: {barra};
    color: {texto2};
    border-top: 1px solid {borde};
    font-size: 12px;
}}
QStatusBar::item {{ border: none; }}
QStatusBar QLabel {{ color: {texto2}; }}

/* ── Splitter ─────────────────────────────────────────────────────── */
QSplitter::handle {{ background-color: transparent; width: 6px; height: 6px; }}
QSplitter::handle:hover {{ background-color: {acento}; }}

/* ── Cabeceras de paneles ─────────────────────────────────────────── */
QLabel#CabeceraPanel {{
    background-color: {barra};
    color: {texto3};
    border-bottom: 1px solid {borde};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    padding-left: 10px;
}}

/* ── Cuadros de texto / entradas ──────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {elevado};
    color: {texto};
    border: 1px solid {elevado2};
    border-radius: 7px;
    padding: 6px 9px;
    selection-background-color: {sel};
    selection-color: #FFFFFF;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{ border-color: {acento}; }}

/* La vista previa es un QTextBrowser a sangre completa, sin borde de input */
QTextBrowser {{
    background-color: {editor_bg};
    color: {texto};
    border: none;
    border-radius: 0;
    padding: 0;
}}

/* ── Botones ──────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {elevado};
    color: {texto};
    border: 1px solid {elevado2};
    border-radius: 7px;
    padding: 6px 16px;
}}
QPushButton:hover {{ background-color: {hover}; }}
QPushButton:pressed {{ background-color: {acento_lo}; color: #FFFFFF; }}
QPushButton:default {{
    background-color: {acento};
    color: #FFFFFF;
    border-color: {acento};
}}
QPushButton:default:hover {{ background-color: {acento_hi}; }}
QPushButton:default:pressed {{ background-color: {acento_lo}; }}
QPushButton#BotonPeligro {{ color: {rojo}; border-color: {rojo}; }}
QPushButton#BotonPeligro:enabled:hover {{ background-color: {rojo}; color: #FFFFFF; }}
QPushButton#BotonPeligro:enabled:pressed {{ background-color: {rojo}; color: #FFFFFF; }}

/* ── ComboBox ─────────────────────────────────────────────────────── */
QComboBox {{
    background-color: {elevado};
    color: {texto};
    border: 1px solid {elevado2};
    border-radius: 7px;
    padding: 5px 10px;
}}
QComboBox:hover {{ border-color: {acento}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox::down-arrow {{ image: url({ad}); width: 10px; height: 6px; }}
/* Selector de tamaño (editable y estrecho): menos hueco y sin resaltado de
   selección para que el número se vea siempre nítido y centrado. */
QComboBox#ComboTamano {{ padding: 5px 4px 5px 6px; }}
QComboBox#ComboTamano QLineEdit {{
    background: transparent;
    color: {texto};
    border: none;
    padding: 0;
    selection-background-color: transparent;
    selection-color: {texto};
}}
QComboBox QAbstractItemView {{
    background-color: {elevado};
    color: {texto};
    border: 1px solid {borde};
    border-radius: 8px;
    padding: 4px;
    selection-background-color: {acento};
    selection-color: #FFFFFF;
    outline: none;
}}

/* ── Spinbox ──────────────────────────────────────────────────────── */
QSpinBox {{
    background-color: {elevado};
    color: {texto};
    border: 1px solid {elevado2};
    border-radius: 7px;
    padding: 5px 24px 5px 9px;
}}
QSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid {elevado2};
    border-top-right-radius: 6px;
}}
QSpinBox::up-button:hover {{ background-color: {hover}; }}
QSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 22px;
    border-left: 1px solid {elevado2};
    border-bottom-right-radius: 6px;
}}
QSpinBox::down-button:hover {{ background-color: {hover}; }}
QSpinBox::up-arrow {{ image: url({au}); width: 10px; height: 6px; }}
QSpinBox::down-arrow {{ image: url({ad}); width: 10px; height: 6px; }}

/* ── ScrollBar (estilo overlay fino macOS) ────────────────────────── */
QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
QScrollBar::handle:vertical {{
    background-color: {texto3};
    border-radius: 5px;
    min-height: 36px;
}}
QScrollBar::handle:vertical:hover {{ background-color: {texto2}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px; }}
QScrollBar::handle:horizontal {{
    background-color: {texto3};
    border-radius: 5px;
    min-width: 36px;
}}
QScrollBar::handle:horizontal:hover {{ background-color: {texto2}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: transparent; }}

/* ── Diálogos ─────────────────────────────────────────────────────── */
QDialogButtonBox QPushButton {{ min-width: 90px; }}
QGroupBox {{
    color: {texto};
    border: 1px solid {borde};
    border-radius: 9px;
    margin-top: 10px;
    padding-top: 8px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
    color: {texto2};
}}

/* ── CheckBox ─────────────────────────────────────────────────────── */
QCheckBox {{ spacing: 7px; color: {texto}; }}
QCheckBox::indicator {{
    width: 17px;
    height: 17px;
    border: 1px solid {elevado2};
    border-radius: 5px;
    background-color: {elevado};
}}
QCheckBox::indicator:checked {{ background-color: {acento}; border-color: {acento}; }}

/* ── RadioButton ──────────────────────────────────────────────────── */
QRadioButton {{ spacing: 7px; color: {texto}; }}
QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {elevado2};
    border-radius: 9px;
    background-color: {elevado};
}}
QRadioButton::indicator:checked {{
    border: 5px solid {acento};
    background-color: #FFFFFF;
    border-radius: 9px;
}}
QRadioButton::indicator:hover {{ border-color: {acento}; }}
"""


# ─── Gestor de temas ─────────────────────────────────────────────────────────

# Colores base de cada tema para construir el QPalette (deben coincidir con los
# usados en el QSS). Sin QPalette, las vistas que Qt no estiliza por QSS
# (QTableWidget, QMessageBox…) usarían la paleta del sistema y podrían mostrar
# texto oscuro sobre fondo oscuro.
_PALETA_OSCURA = {
    "fondo": "#1E1E20", "base": "#3A3A3C", "alt": "#2A2A2C", "borde": "#36363A",
    "texto": "#EBEBF0", "texto3": "#6E6E73", "acento": "#0A84FF",
}
_PALETA_CLARA = {
    "fondo": "#ECECEE", "base": "#FFFFFF", "alt": "#F4F4F6", "borde": "#D9D9DF",
    "texto": "#1D1D1F", "texto3": "#8E8E93", "acento": "#007AFF",
}


def _crear_palette(c: dict):
    from PySide6.QtGui import QColor, QPalette
    R = QPalette.ColorRole
    G = QPalette.ColorGroup
    p = QPalette()
    p.setColor(R.Window, QColor(c["fondo"]))
    p.setColor(R.WindowText, QColor(c["texto"]))
    p.setColor(R.Base, QColor(c["base"]))
    p.setColor(R.AlternateBase, QColor(c["alt"]))
    p.setColor(R.Text, QColor(c["texto"]))
    p.setColor(R.Button, QColor(c["base"]))
    p.setColor(R.ButtonText, QColor(c["texto"]))
    p.setColor(R.BrightText, QColor("#FFFFFF"))
    p.setColor(R.ToolTipBase, QColor(c["base"]))
    p.setColor(R.ToolTipText, QColor(c["texto"]))
    p.setColor(R.PlaceholderText, QColor(c["texto3"]))
    p.setColor(R.Highlight, QColor(c["acento"]))
    p.setColor(R.HighlightedText, QColor("#FFFFFF"))
    p.setColor(R.Link, QColor(c["acento"]))
    # Grises intermedios (los usa p. ej. «palette(mid)» del panel de detalles).
    p.setColor(R.Mid, QColor(c["texto3"]))
    p.setColor(R.Midlight, QColor(c["borde"]))
    p.setColor(R.Dark, QColor(c["borde"]))
    p.setColor(R.Light, QColor(c["alt"]))
    p.setColor(R.Shadow, QColor("#000000"))
    for role in (R.WindowText, R.Text, R.ButtonText):
        p.setColor(G.Disabled, role, QColor(c["texto3"]))
    return p


class GestorTemas:
    """Aplica el tema visual seleccionado a toda la aplicación Qt."""

    @staticmethod
    def aplicar(tema: Tema) -> None:
        app = QApplication.instance()
        if app is None:
            return
        if tema == Tema.OSCURO:
            app.setStyleSheet(_qss_oscuro())
            app.setPalette(_crear_palette(_PALETA_OSCURA))
        else:
            app.setStyleSheet(_qss_claro())
            app.setPalette(_crear_palette(_PALETA_CLARA))

    @staticmethod
    def alternar(tema_actual: Tema) -> Tema:
        return Tema.CLARO if tema_actual == Tema.OSCURO else Tema.OSCURO
