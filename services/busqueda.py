# services/busqueda.py
# Servicio de búsqueda simple y avanzada en documentos del proyecto

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from core.logger import logger


@dataclass
class ResultadoBusqueda:
    """Encapsula un resultado de búsqueda con su contexto."""
    ruta: Path
    nombre_archivo: str
    numero_linea: int
    texto_linea: str
    inicio: int
    fin: int


class ServicioBusqueda:
    """
    Realiza búsquedas de texto (simple, con regex, con reemplazo)
    en uno o varios documentos del proyecto.
    """

    @staticmethod
    def buscar_en_texto(
        texto: str,
        patron: str,
        usar_regex: bool = False,
        ignorar_mayusculas: bool = True,
    ) -> list[tuple[int, int]]:
        """
        Busca ocurrencias del patrón en un texto plano.
        Retorna lista de tuplas (inicio, fin) de cada coincidencia.
        """
        coincidencias = []
        try:
            flags = re.IGNORECASE if ignorar_mayusculas else 0
            if not usar_regex:
                patron = re.escape(patron)
            for m in re.finditer(patron, texto, flags):
                coincidencias.append((m.start(), m.end()))
        except re.error as e:
            logger.warning("Patrón de búsqueda inválido: %s", e)
        return coincidencias

    @staticmethod
    def reemplazar_en_texto(
        texto: str,
        patron: str,
        reemplazo: str,
        usar_regex: bool = False,
        ignorar_mayusculas: bool = True,
        solo_primera: bool = False,
    ) -> str:
        """
        Reemplaza ocurrencias del patrón en el texto.
        Retorna el texto modificado.
        """
        try:
            flags = re.IGNORECASE if ignorar_mayusculas else 0
            if not usar_regex:
                patron = re.escape(patron)
            count = 1 if solo_primera else 0
            return re.sub(patron, reemplazo, texto, count=count, flags=flags)
        except re.error as e:
            logger.warning("Error en reemplazo: %s", e)
            return texto

    @staticmethod
    def buscar_en_proyecto(
        ruta_proyecto: Path,
        patron: str,
        usar_regex: bool = False,
        ignorar_mayusculas: bool = True,
    ) -> list[ResultadoBusqueda]:
        """
        Busca el patrón en todos los archivos .md del proyecto.
        Retorna lista de resultados con contexto de línea.
        """
        resultados: list[ResultadoBusqueda] = []
        try:
            flags = re.IGNORECASE if ignorar_mayusculas else 0
            patron_compilado = re.compile(
                patron if usar_regex else re.escape(patron),
                flags,
            )
        except re.error as e:
            logger.warning("Patrón inválido para búsqueda en proyecto: %s", e)
            return resultados

        for archivo in ruta_proyecto.rglob("*.md"):
            # Excluir la carpeta de respaldos
            if ".respaldos" in archivo.parts:
                continue
            try:
                lineas = archivo.read_text(encoding="utf-8").splitlines()
                for num, linea in enumerate(lineas, start=1):
                    for m in patron_compilado.finditer(linea):
                        resultados.append(ResultadoBusqueda(
                            ruta=archivo,
                            nombre_archivo=archivo.name,
                            numero_linea=num,
                            texto_linea=linea.strip(),
                            inicio=m.start(),
                            fin=m.end(),
                        ))
            except (OSError, UnicodeDecodeError):
                continue

        return resultados
