# core/logger.py
# Configuración centralizada del sistema de registro (logging) de Typoo

import logging
import sys
from pathlib import Path


def configurar_logger(nivel: int = logging.DEBUG) -> logging.Logger:
    """
    Configura y retorna el logger principal de la aplicación.
    Registra en consola y en archivo de log dentro del directorio de usuario.
    """
    logger = logging.getLogger("typoo")

    if logger.handlers:
        return logger

    logger.setLevel(nivel)
    formato = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler de consola
    handler_consola = logging.StreamHandler(sys.stdout)
    handler_consola.setLevel(nivel)
    handler_consola.setFormatter(formato)
    logger.addHandler(handler_consola)

    # Handler de archivo (en directorio de usuario)
    try:
        ruta_log = Path.home() / ".typoo" / "typoo.log"
        ruta_log.parent.mkdir(parents=True, exist_ok=True)
        handler_archivo = logging.FileHandler(ruta_log, encoding="utf-8")
        handler_archivo.setLevel(logging.WARNING)
        handler_archivo.setFormatter(formato)
        logger.addHandler(handler_archivo)
    except Exception:
        # Si no se puede crear el archivo de log, se continúa solo con consola
        pass

    return logger


# Logger global accesible desde cualquier módulo
logger = configurar_logger()
