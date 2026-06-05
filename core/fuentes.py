# core/fuentes.py
# Registro de las tipografías empaquetadas y catálogo de fuentes para el editor.

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QFontDatabase


def _base_dir() -> Path:
    """Raíz de recursos: directorio del proyecto en dev, sys._MEIPASS en exe."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent


RUTA_FONTS = _base_dir() / "assets" / "fonts"

# Tipografías incluidas con la aplicación (siempre disponibles, licencia SIL OFL).
FUENTES_EMPAQUETADAS = [
    "EB Garamond", "Lora", "Literata", "Crimson Pro",
    "Spectral", "Bitter", "Playfair Display", "Inter",
]

# Familias del sistema que se ofrecen si están instaladas.
_FUENTES_SISTEMA = [
    "Georgia", "Palatino Linotype", "Palatino", "Book Antiqua", "Cambria",
    "Garamond", "Baskerville", "Iowan Old Style", "Charter", "Hoefler Text",
    "Constantia", "Times New Roman", "Helvetica Neue", "Avenir Next",
    "Segoe UI", "Verdana", "Courier New", "Consolas",
]

# Agrupación mostrada en el selector de la barra de formato.
_GRUPOS = [
    ("Literarias", ["EB Garamond", "Lora", "Literata", "Crimson Pro", "Spectral", "Bitter"]),
    ("Decorativas", ["Playfair Display"]),
    ("Modernas", ["Inter"]),
]

_registradas = False


def registrar_fuentes_empaquetadas() -> int:
    """
    Carga en Qt todas las tipografías .ttf incluidas en assets/fonts.
    Requiere que exista una QApplication. Devuelve el número de archivos cargados.
    """
    global _registradas
    if _registradas:
        return 0
    cargadas = 0
    if RUTA_FONTS.is_dir():
        for ttf in sorted(RUTA_FONTS.glob("*.ttf")):
            if QFontDatabase.addApplicationFont(str(ttf)) != -1:
                cargadas += 1
    _registradas = True
    return cargadas


def grupos_para_selector() -> list[tuple[str, list[str]]]:
    """
    Devuelve los grupos de fuentes a mostrar en el selector.
    Las empaquetadas siempre aparecen; las del sistema solo si están instaladas.
    """
    instaladas = set(QFontDatabase.families())
    grupos: list[tuple[str, list[str]]] = [(titulo, list(fams)) for titulo, fams in _GRUPOS]
    sistema = [f for f in _FUENTES_SISTEMA if f in instaladas]
    if sistema:
        grupos.append(("Sistema", sistema))
    return grupos
