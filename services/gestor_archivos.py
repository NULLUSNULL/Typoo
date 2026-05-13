# services/gestor_archivos.py
# Servicio de operaciones de bajo nivel sobre el sistema de archivos

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.constantes import DIRECTORIO_RESPALDOS
from core.logger import logger


class GestorArchivos:
    """
    Proporciona operaciones de sistema de archivos para documentos del proyecto:
    copias de seguridad, lectura y escritura de texto, exploración de directorios.
    """

    @staticmethod
    def leer_texto(ruta: Path) -> str:
        """Lee un archivo de texto con codificación UTF-8."""
        try:
            return ruta.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.error("Error al leer %s: %s", ruta, e)
            return ""

    @staticmethod
    def escribir_texto(ruta: Path, contenido: str) -> bool:
        """Escribe texto en un archivo con codificación UTF-8."""
        try:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(contenido, encoding="utf-8")
            return True
        except OSError as e:
            logger.error("Error al escribir %s: %s", ruta, e)
            return False

    @staticmethod
    def crear_respaldo(
        ruta_proyecto: Path,
        max_respaldos: int = 10,
        ruta_destino: Optional[Path] = None,
    ) -> bool:
        """
        Crea una copia de seguridad comprimida del proyecto.
        Si ruta_destino es None los respaldos van a ruta_proyecto/.respaldos/
        """
        try:
            directorio_respaldos = ruta_destino if ruta_destino else ruta_proyecto / DIRECTORIO_RESPALDOS
            directorio_respaldos.mkdir(exist_ok=True)

            marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_respaldo = f"respaldo_{marca_tiempo}"
            ruta_respaldo = directorio_respaldos / nombre_respaldo

            # Copiar directorio excluyendo la carpeta de respaldos
            shutil.copytree(
                ruta_proyecto,
                ruta_respaldo,
                ignore=shutil.ignore_patterns(".respaldos", "*.pyc"),
            )

            # Comprimir en zip
            shutil.make_archive(str(ruta_respaldo), "zip", ruta_respaldo)
            shutil.rmtree(ruta_respaldo)

            # Eliminar respaldos más antiguos si se supera el límite
            GestorArchivos._limpiar_respaldos_antiguos(directorio_respaldos, max_respaldos)

            logger.info("Respaldo creado: %s.zip", ruta_respaldo)
            return True
        except Exception as e:
            logger.error("Error al crear respaldo: %s", e)
            return False

    @staticmethod
    def _limpiar_respaldos_antiguos(directorio: Path, max_respaldos: int) -> None:
        """Elimina los respaldos más antiguos si hay más del máximo permitido."""
        respaldos = sorted(
            directorio.glob("respaldo_*.zip"),
            key=lambda p: p.stat().st_mtime,
        )
        while len(respaldos) > max_respaldos:
            respaldos[0].unlink()
            logger.debug("Respaldo eliminado: %s", respaldos[0].name)
            respaldos.pop(0)

    @staticmethod
    def listar_archivos_md(directorio: Path) -> list[Path]:
        """Lista todos los archivos Markdown en un directorio recursivamente."""
        return sorted(directorio.rglob("*.md"))

    @staticmethod
    def es_proyecto_valido(ruta: Path) -> bool:
        """Verifica si una ruta contiene un proyecto Typoo válido."""
        from core.constantes import NOMBRE_ARCHIVO_PROYECTO
        return (ruta / NOMBRE_ARCHIVO_PROYECTO).exists()
