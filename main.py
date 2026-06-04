# main.py
# Punto de entrada de la aplicación Typoo
# Uso: python main.py

import sys
from pathlib import Path

# Añadir el directorio raíz al path de Python para importaciones relativas
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QIcon

from core.constantes import NOMBRE_APP, VERSION_APP, RUTA_ICONO
from core.logger import logger


def main() -> int:
    """Función principal que inicializa y lanza la aplicación."""

    # Necesario en Windows para mostrar el ícono correcto en la barra de tareas
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            f"nullusnull.{NOMBRE_APP.lower()}.{VERSION_APP}"
        )
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName(NOMBRE_APP)
    app.setApplicationVersion(VERSION_APP)
    app.setOrganizationName("NULLUSNULL")
    app.setOrganizationDomain("nullusnull.dev")

    # Traducir los elementos estándar de Qt (botones, diálogos) al español
    _ruta_traducciones = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    _locale = QLocale(QLocale.Language.Spanish, QLocale.Country.Spain)
    for _catalogo in ("qtbase", "qt"):
        _tr = QTranslator(app)
        if _tr.load(_locale, _catalogo, "_", _ruta_traducciones):
            app.installTranslator(_tr)
            break

    # Fuente base de la interfaz
    fuente_base = QFont("Segoe UI", 10)
    app.setFont(fuente_base)

    # Registrar las tipografías empaquetadas (Lora, EB Garamond, Literata…)
    from core.fuentes import registrar_fuentes_empaquetadas
    registrar_fuentes_empaquetadas()

    # Icono de la aplicación (barra de tareas, bandeja del sistema, alt-tab)
    if RUTA_ICONO.exists():
        icono = QIcon(str(RUTA_ICONO))
        app.setWindowIcon(icono)

    # Importación tardía para que QApplication ya exista al inicializar los widgets
    from ui.ventana_principal import VentanaPrincipal

    ventana = VentanaPrincipal()
    ventana.show()

    logger.info("Aplicación iniciada: %s %s", NOMBRE_APP, VERSION_APP)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
