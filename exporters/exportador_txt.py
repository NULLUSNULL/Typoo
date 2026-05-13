# exporters/exportador_txt.py
# Exportación del manuscrito a texto plano (.txt)

from __future__ import annotations

import re
from pathlib import Path

from core.logger import logger
from models.proyecto import Proyecto


class ExportadorTxt:
    """
    Genera un archivo de texto plano (.txt) con el contenido completo
    del proyecto literario, eliminando la sintaxis Markdown.
    """

    @staticmethod
    def exportar(proyecto: Proyecto, ruta_destino: Path) -> bool:
        """
        Recorre todos los documentos del árbol del proyecto y los vuelca
        en un único archivo de texto con separadores entre capítulos.
        """
        try:
            fragmentos: list[str] = []
            fragmentos.append(proyecto.nombre.upper())
            fragmentos.append("=" * len(proyecto.nombre))
            if proyecto.autor:
                fragmentos.append(f"por {proyecto.autor}")
            fragmentos.append("")

            ExportadorTxt._recorrer_arbol(proyecto, fragmentos)

            contenido = "\n".join(fragmentos)
            ruta_destino.write_text(contenido, encoding="utf-8")
            logger.info("Exportado TXT: %s", ruta_destino)
            return True
        except Exception as e:
            logger.error("Error al exportar TXT: %s", e)
            return False

    @staticmethod
    def _recorrer_arbol(proyecto: Proyecto, fragmentos: list[str]) -> None:
        from core.constantes import TipoElemento
        from models.documento import ItemProyecto

        def procesar(item: ItemProyecto) -> None:
            if item.ruta_relativa:
                ruta = proyecto.ruta / item.ruta_relativa
                if ruta.is_file():
                    texto = ruta.read_text(encoding="utf-8")
                    limpio = ExportadorTxt._limpiar_markdown(texto)
                    if limpio.strip():
                        fragmentos.append("")
                        fragmentos.append("─" * 60)
                        fragmentos.append("")
                        fragmentos.append(limpio)

            for hijo in sorted(item.hijos, key=lambda h: h.orden):
                procesar(hijo)

        if proyecto.raiz:
            for hijo in sorted(proyecto.raiz.hijos, key=lambda h: h.orden):
                procesar(hijo)

    @staticmethod
    def _limpiar_markdown(texto: str) -> str:
        """Elimina la sintaxis Markdown dejando solo el texto limpio."""
        # Bloques de código
        texto = re.sub(r"```[\s\S]*?```", "", texto)
        texto = re.sub(r"`([^`]+)`", r"\1", texto)
        # Encabezados
        texto = re.sub(r"^#{1,6}\s+", "", texto, flags=re.MULTILINE)
        # Negrita e cursiva
        texto = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", texto)
        texto = re.sub(r"_{1,3}(.+?)_{1,3}", r"\1", texto)
        # Tachado
        texto = re.sub(r"~~(.+?)~~", r"\1", texto)
        # Enlaces e imágenes
        texto = re.sub(r"!\[([^\]]*)\]\([^\)]*\)", r"\1", texto)
        texto = re.sub(r"\[([^\]]+)\]\([^\)]*\)", r"\1", texto)
        # Citas
        texto = re.sub(r"^>\s+", "", texto, flags=re.MULTILINE)
        # Separadores horizontales
        texto = re.sub(r"^[-*_]{3,}\s*$", "\n", texto, flags=re.MULTILINE)
        # Listas
        texto = re.sub(r"^\s*[-*+]\s+", "", texto, flags=re.MULTILINE)
        texto = re.sub(r"^\s*\d+\.\s+", "", texto, flags=re.MULTILINE)
        return texto.strip()
