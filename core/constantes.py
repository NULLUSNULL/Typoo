# core/constantes.py
# Constantes globales de la aplicación Typoo

import sys
from enum import Enum, auto
from pathlib import Path


def _base_dir() -> Path:
    """Raíz de recursos: directorio del proyecto en dev, sys._MEIPASS en exe compilado."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent

# ─── Información de la aplicación ────────────────────────────────────────────

NOMBRE_APP     = "Typoo"
VERSION_APP    = "1.0.0"
AUTOR_APP      = "NULLUSNULL"
LICENCIA_APP   = "MIT License"
DESCRIPCION    = "Suite profesional de escritura de novelas y proyectos literarios"

# ─── Rutas y archivos ─────────────────────────────────────────────────────────

NOMBRE_ARCHIVO_PROYECTO  = "proyecto.json"
EXTENSION_DOCUMENTO      = ".md"
DIRECTORIO_RESPALDOS     = ".respaldos"

RUTA_ICONO = _base_dir() / "assets" / "iconos" / "typoo-icon.ico"

# ─── Tipos de elementos del árbol del proyecto ───────────────────────────────

class TipoElemento(str, Enum):
    PROYECTO    = "proyecto"
    CARPETA     = "carpeta"
    CAPITULO    = "capitulo"
    ESCENA      = "escena"
    NOTA        = "nota"
    PERSONAJE   = "personaje"
    UBICACION   = "ubicacion"


# ─── Tipos de panel de edición ────────────────────────────────────────────────

class TipoPanel(Enum):
    PRINCIPAL   = auto()
    SECUNDARIO1 = auto()
    SECUNDARIO2 = auto()


# ─── Temas de la interfaz ─────────────────────────────────────────────────────

class Tema(str, Enum):
    CLARO  = "claro"
    OSCURO = "oscuro"


# ─── Configuración por defecto ────────────────────────────────────────────────

INTERVALO_AUTOGUARDADO_MS   = 60_000    # 1 minuto
MAX_RESPALDOS                = 10
ANCHO_MINIMO_EXPLORADOR      = 180
ANCHO_MAXIMO_EXPLORADOR      = 450
ANCHO_MINIMO_VISTA_PREVIA    = 200
FUENTE_EDITOR_FAMILIA        = "Courier New"
FUENTE_EDITOR_TAMANIO        = 12

# ─── Iconos de texto para la barra de herramientas ───────────────────────────
# Se usan caracteres Unicode ya que no se distribuyen archivos de imagen

ICONO_NEGRITA       = "B"
ICONO_CURSIVA       = "I"
ICONO_SUBRAYADO     = "U"
ICONO_TACHADO       = "S"
ICONO_H1            = "H1"
ICONO_H2            = "H2"
ICONO_H3            = "H3"
ICONO_LISTA_VIÑETAS = "≡"
ICONO_LISTA_NUMERADA = "1."
ICONO_CITA          = "❝"
ICONO_CODIGO        = "<>"
ICONO_ENLACE        = "🔗"
ICONO_SEPARADOR     = "—"
ICONO_GUION_LARGO   = "—"
ICONO_GUION_CORTO   = "–"
ICONO_COMILLAS_ESP  = "«»"
ICONO_COMILLAS_ING  = '""'
