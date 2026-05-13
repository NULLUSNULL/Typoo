# exporters/exportador_pdf.py
# Exportación del manuscrito a PDF usando reportlab

from __future__ import annotations

import re
from pathlib import Path

from core.logger import logger
from models.proyecto import Proyecto


class ExportadorPdf:
    """
    Genera un archivo PDF con el contenido del proyecto literario.
    Requiere la dependencia: reportlab
    """

    # Márgenes y configuración de página
    MARGEN       = 72   # 1 pulgada en puntos
    FUENTE_TEXTO = "Helvetica"
    FUENTE_MONO  = "Courier"
    TAMANIO_H1   = 20
    TAMANIO_H2   = 16
    TAMANIO_H3   = 13
    TAMANIO_TEXTO= 11
    INTERLINEADO  = 16

    @staticmethod
    def exportar(proyecto: Proyecto, ruta_destino: Path) -> bool:
        """Exporta el proyecto completo a un archivo PDF."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer,
                HRFlowable, PageBreak
            )
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
            from reportlab.lib import colors
        except ImportError:
            logger.error("reportlab no está instalado. Ejecuta: pip install reportlab")
            return False

        try:
            doc = SimpleDocTemplate(
                str(ruta_destino),
                pagesize=A4,
                rightMargin=ExportadorPdf.MARGEN,
                leftMargin=ExportadorPdf.MARGEN,
                topMargin=ExportadorPdf.MARGEN,
                bottomMargin=ExportadorPdf.MARGEN,
            )

            estilos = getSampleStyleSheet()

            # Estilos personalizados
            est_titulo = ParagraphStyle(
                "Titulo", parent=estilos["Title"],
                fontSize=24, spaceAfter=6, alignment=TA_CENTER,
            )
            est_autor = ParagraphStyle(
                "Autor", parent=estilos["Normal"],
                fontSize=14, spaceAfter=40, alignment=TA_CENTER,
            )
            est_h1 = ParagraphStyle(
                "H1", parent=estilos["Heading1"],
                fontSize=20, spaceBefore=24, spaceAfter=8,
            )
            est_h2 = ParagraphStyle(
                "H2", parent=estilos["Heading2"],
                fontSize=16, spaceBefore=16, spaceAfter=6,
            )
            est_h3 = ParagraphStyle(
                "H3", parent=estilos["Heading3"],
                fontSize=13, spaceBefore=12, spaceAfter=4,
            )
            est_cuerpo = ParagraphStyle(
                "Cuerpo", parent=estilos["Normal"],
                fontSize=11, leading=18, alignment=TA_JUSTIFY,
                spaceAfter=6,
            )
            est_cita = ParagraphStyle(
                "Cita", parent=estilos["Normal"],
                fontSize=11, leading=18, leftIndent=30,
                textColor=colors.grey, fontName="Helvetica-Oblique",
            )
            est_codigo = ParagraphStyle(
                "Codigo", parent=estilos["Code"],
                fontSize=9, leading=14, leftIndent=20,
                backColor=colors.HexColor("#F0F0F0"),
            )

            mapa_estilos = {
                1: est_h1, 2: est_h2, 3: est_h3,
                4: est_h3, 5: est_h3, 6: est_h3,
            }

            historia: list = []

            # Portada
            historia.append(Spacer(1, 80))
            historia.append(Paragraph(proyecto.nombre, est_titulo))
            if proyecto.autor:
                historia.append(Paragraph(f"por {proyecto.autor}", est_autor))
            historia.append(PageBreak())

            # Contenido del proyecto
            ExportadorPdf._recorrer_arbol(
                proyecto, historia,
                mapa_estilos, est_cuerpo, est_cita, est_codigo,
            )

            doc.build(historia)
            logger.info("Exportado PDF: %s", ruta_destino)
            return True
        except Exception as e:
            logger.error("Error al exportar PDF: %s", e)
            return False

    @staticmethod
    def _recorrer_arbol(proyecto, historia, mapa_estilos, est_cuerpo, est_cita, est_codigo):
        from models.documento import ItemProyecto

        def procesar(item: ItemProyecto) -> None:
            if item.ruta_relativa:
                ruta = proyecto.ruta / item.ruta_relativa
                if ruta.is_file():
                    texto = ruta.read_text(encoding="utf-8")
                    ExportadorPdf._markdown_a_pdf(
                        historia, texto,
                        mapa_estilos, est_cuerpo, est_cita, est_codigo,
                    )

            for hijo in sorted(item.hijos, key=lambda h: h.orden):
                procesar(hijo)

        if proyecto.raiz:
            for hijo in sorted(proyecto.raiz.hijos, key=lambda h: h.orden):
                procesar(hijo)

    @staticmethod
    def _markdown_a_pdf(historia, texto, mapa_estilos, est_cuerpo, est_cita, est_codigo):
        """Convierte Markdown a flowables de ReportLab."""
        from reportlab.platypus import Paragraph, Spacer, HRFlowable

        lineas = texto.splitlines()
        en_bloque = False
        buffer: list[str] = []

        for linea in lineas:
            if linea.startswith("```"):
                if en_bloque and buffer:
                    historia.append(Paragraph("<br/>".join(buffer), est_codigo))
                    historia.append(Spacer(1, 6))
                    buffer.clear()
                en_bloque = not en_bloque
                continue

            if en_bloque:
                buffer.append(linea)
                continue

            # Encabezados
            m = re.match(r"^(#{1,6})\s+(.+)$", linea)
            if m:
                nivel = len(m.group(1))
                estilo = mapa_estilos.get(nivel, mapa_estilos[3])
                historia.append(Paragraph(
                    ExportadorPdf._escape(m.group(2)), estilo
                ))
                continue

            # Separador
            if re.match(r"^[-*_]{3,}\s*$", linea):
                historia.append(HRFlowable(width="60%", thickness=0.5, color="#999999"))
                historia.append(Spacer(1, 6))
                continue

            # Cita
            if linea.startswith("> "):
                historia.append(Paragraph(
                    ExportadorPdf._escape(linea[2:]), est_cita
                ))
                continue

            # Párrafo
            if linea.strip():
                historia.append(Paragraph(
                    ExportadorPdf._inline_md(linea), est_cuerpo
                ))
            else:
                historia.append(Spacer(1, 6))

    @staticmethod
    def _escape(texto: str) -> str:
        """Escapa caracteres especiales de XML para ReportLab."""
        return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    @staticmethod
    def _inline_md(texto: str) -> str:
        """Convierte marcadores Markdown inline a etiquetas HTML de ReportLab."""
        texto = ExportadorPdf._escape(texto)
        texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
        texto = re.sub(r"__(.+?)__",     r"<b>\1</b>", texto)
        texto = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", texto)
        texto = re.sub(r"_(.+?)_",       r"<i>\1</i>", texto)
        texto = re.sub(r"`(.+?)`",       r"<font name='Courier'>\1</font>", texto)
        return texto
