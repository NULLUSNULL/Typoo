# editors/resaltador_sintaxis.py
# Resaltado de sintaxis Markdown mediante QSyntaxHighlighter

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)


@dataclass
class ReglaResaltado:
    """Par patrón → formato para el resaltador."""
    patron: str
    formato: QTextCharFormat


def _formato(
    color: str | None = None,
    negrita: bool = False,
    cursiva: bool = False,
    fondo: str | None = None,
) -> QTextCharFormat:
    """Factoría de QTextCharFormat con parámetros simples."""
    fmt = QTextCharFormat()
    if color:
        fmt.setForeground(QColor(color))
    if fondo:
        fmt.setBackground(QColor(fondo))
    if negrita:
        fmt.setFontWeight(QFont.Weight.Bold)
    if cursiva:
        fmt.setFontItalic(True)
    return fmt


class ResaltadorMarkdown(QSyntaxHighlighter):
    """
    Resaltador de sintaxis para Markdown.
    Aplica formatos diferenciados a encabezados, negrita, cursiva,
    código, enlaces, citas y listas.
    """

    # ─── Paleta literaria oscura (por defecto) ────────────────────────────────
    # Tonos discretos: el texto manda, los marcadores Markdown se atenúan.
    COLORES_OSCURO = {
        "encabezado":  "#C9A86A",   # títulos en tono pergamino cálido
        "negrita":     None,        # solo peso, sin color
        "cursiva":     None,        # solo cursiva, sin color
        "codigo":      "#9AA0A6",
        "fondo_codigo":"#26262A",
        "enlace":      "#7FA8C9",
        "cita":        "#8A8F98",
        "lista":       "#9AA0A6",
        "hr":          "#4A4A4F",
        "metadato":    "#A0A0A6",
        "html":        "#6E6E73",
    }

    # ─── Paleta literaria clara ───────────────────────────────────────────────
    COLORES_CLARO = {
        "encabezado":  "#8A6D3B",   # títulos en sepia
        "negrita":     None,
        "cursiva":     None,
        "codigo":      "#6E6E73",
        "fondo_codigo":"#F0F0F2",
        "enlace":      "#2C6E9A",
        "cita":        "#8A8F98",
        "lista":       "#9A9AA0",
        "hr":          "#C7C7CC",
        "metadato":    "#4A4A4F",
        "html":        "#9A9AA0",
    }

    def __init__(self, documento: QTextDocument, tema_oscuro: bool = True) -> None:
        super().__init__(documento)
        self._tema_oscuro = tema_oscuro
        self._reglas: list[ReglaResaltado] = []
        self._formato_bloque_codigo = QTextCharFormat()
        self._en_bloque_codigo = False
        self._actualizar_reglas()

    def cambiar_tema(self, oscuro: bool) -> None:
        """Actualiza las reglas al cambiar el tema de la interfaz."""
        self._tema_oscuro = oscuro
        self._actualizar_reglas()
        self.rehighlight()

    def _colores(self) -> dict[str, str]:
        return self.COLORES_OSCURO if self._tema_oscuro else self.COLORES_CLARO

    def _actualizar_reglas(self) -> None:
        c = self._colores()
        self._reglas = []

        # Línea de separación horizontal (--- o ***)
        self._reglas.append(ReglaResaltado(
            r"^(\-{3,}|\*{3,}|_{3,})\s*$",
            _formato(color=c["hr"]),
        ))

        # Encabezados H1–H6
        for nivel in range(1, 7):
            prefijo = "#" * nivel
            peso = QFont.Weight.Bold if nivel <= 2 else QFont.Weight.Medium
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(c["encabezado"]))
            fmt.setFontWeight(peso)
            tam = max(1.0, 1.6 - (nivel - 1) * 0.1)
            fmt.setFontPointSize(12 + (6 - nivel) * 1.5)
            self._reglas.append(ReglaResaltado(
                rf"^{re.escape(prefijo)}\s.*$",
                fmt,
            ))

        # Código en línea `código`
        fmt_codigo = _formato(color=c["codigo"], fondo=c["fondo_codigo"])
        fmt_codigo.setFontFamily("Courier New")
        self._reglas.append(ReglaResaltado(r"`[^`]+`", fmt_codigo))

        # Negrita **texto** o __texto__
        self._reglas.append(ReglaResaltado(
            r"(\*\*|__).+?(\*\*|__)",
            _formato(color=c["negrita"], negrita=True),
        ))

        # Cursiva *texto* o _texto_ (sin capturar negritas)
        self._reglas.append(ReglaResaltado(
            r"(?<!\*)(\*|_)(?!\*)(?!\s).+?(?<!\s)(\*|_)(?!\*)",
            _formato(color=c["cursiva"], cursiva=True),
        ))

        # Tachado ~~texto~~
        self._reglas.append(ReglaResaltado(
            r"~~.+?~~",
            _formato(color=c["cita"]),
        ))

        # Citas > texto
        self._reglas.append(ReglaResaltado(
            r"^>\s.*$",
            _formato(color=c["cita"], cursiva=True),
        ))

        # Listas no ordenadas: - item / * item / + item
        self._reglas.append(ReglaResaltado(
            r"^\s*[-*+]\s",
            _formato(color=c["lista"], negrita=True),
        ))

        # Listas ordenadas: 1. item
        self._reglas.append(ReglaResaltado(
            r"^\s*\d+\.\s",
            _formato(color=c["lista"], negrita=True),
        ))

        # Imágenes ![alt](url)
        self._reglas.append(ReglaResaltado(
            r"!\[[^\]]*\]\([^\)]*\)",
            _formato(color=c["enlace"]),
        ))

        # Enlaces [texto](url)
        self._reglas.append(ReglaResaltado(
            r"\[[^\]]*\]\([^\)]*\)",
            _formato(color=c["enlace"]),
        ))

        # Tags HTML básicos
        self._reglas.append(ReglaResaltado(
            r"<[^>]+>",
            _formato(color=c["html"]),
        ))

        # Preparar el formato del bloque de código
        self._formato_bloque_codigo = _formato(
            color=c["codigo"],
            fondo=c["fondo_codigo"],
        )
        self._formato_bloque_codigo.setFontFamily("Courier New")

    # ─── highlightBlock ──────────────────────────────────────────────────────

    def highlightBlock(self, texto: str) -> None:
        """Qt llama a este método por cada bloque (párrafo) del documento."""

        # Estado previo (para bloques de código multi-línea)
        estado_previo = self.previousBlockState()

        # Detectar inicio/fin de bloque de código ```
        if texto.startswith("```"):
            if estado_previo == 1:
                # Cierre del bloque
                self.setFormat(0, len(texto), self._formato_bloque_codigo)
                self.setCurrentBlockState(0)
            else:
                # Apertura del bloque
                self.setFormat(0, len(texto), self._formato_bloque_codigo)
                self.setCurrentBlockState(1)
            return

        if estado_previo == 1:
            # Interior del bloque de código
            self.setFormat(0, len(texto), self._formato_bloque_codigo)
            self.setCurrentBlockState(1)
            return

        self.setCurrentBlockState(0)

        # Aplicar reglas una por una
        for regla in self._reglas:
            expresion = QRegularExpression(regla.patron)
            it = expresion.globalMatch(texto)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), regla.formato)
