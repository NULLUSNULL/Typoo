# ai/apple.py
# Apoyo para el proveedor «Apple Foundation»: localiza el ayudante nativo y
# reporta su disponibilidad. El framework Foundation Models solo tiene API en
# Swift, así que hablamos con un pequeño ejecutable (typoo-apple-llm) que
# recibe la petición por stdin y escribe la respuesta en streaming por stdout.

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Optional

NOMBRE_HELPER = "typoo-apple-llm"


def ruta_helper() -> Optional[str]:
    """Devuelve la ruta del ayudante si se encuentra, o None."""
    candidatos: list[Path] = []

    # 1) Junto al ejecutable de la app empaquetada (o en Resources del .app).
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent
        candidatos += [base / NOMBRE_HELPER, base.parent / "Resources" / NOMBRE_HELPER]
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidatos.append(Path(meipass) / NOMBRE_HELPER)

    # 2) Compilado dentro del repositorio (desarrollo).
    raiz = Path(__file__).resolve().parent.parent
    candidatos.append(
        raiz / "extras" / "apple_foundation" / ".build" / "release" / NOMBRE_HELPER)

    for c in candidatos:
        if c.is_file() and os.access(c, os.X_OK):
            return str(c)

    # 3) En el PATH del sistema.
    return shutil.which(NOMBRE_HELPER)


def disponible() -> bool:
    return sys.platform == "darwin" and ruta_helper() is not None


def estado() -> tuple[bool, str]:
    """(ok, mensaje) para la prueba de conexión del proveedor Apple."""
    if sys.platform != "darwin":
        return False, "Solo disponible en macOS (Apple Silicon)."
    if ruta_helper() is None:
        return False, ("Falta el ayudante «typoo-apple-llm». Compílalo desde "
                       "extras/apple_foundation (ver su README).")
    return True, ("Ayudante encontrado. Requiere macOS con Apple Intelligence "
                  "activado; se usará el modelo del sistema.")
