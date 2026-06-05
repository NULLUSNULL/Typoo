# editors/editor_markdown.py
# Editor de texto Markdown con numeración de líneas y formato integrado

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QKeySequence,
    QPainter,
    QPaintEvent,
    QResizeEvent,
    QTextCursor,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QPlainTextEdit,
    QWidget,
)

from core.configuracion import Configuracion
from core.constantes import Tema
from editors.resaltador_sintaxis import ResaltadorMarkdown


class _NumeroLineas(QWidget):
    """
    Widget lateral que muestra los números de línea del editor.
    Se vincula al QPlainTextEdit padre.
    """

    def __init__(self, editor: "EditorMarkdown") -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.ancho_numeros_linea(), 0)

    def paintEvent(self, evento: QPaintEvent) -> None:  # type: ignore[override]
        self._editor.pintar_numeros_linea(evento)


class EditorMarkdown(QPlainTextEdit):
    """
    Editor principal con:
    - Numeración de líneas
    - Resaltado de sintaxis Markdown
    - Contador de palabras integrado
    - Detección de cambios no guardados
    - Inserción de fragmentos de formato
    """

    # Señales personalizadas
    palabras_cambiadas = Signal(int)        # Emite el conteo actualizado de palabras
    modificado_cambiado = Signal(bool)      # Emite True cuando hay cambios sin guardar
    foco_recibido = Signal()                # Emite cuando el editor gana el foco

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._config = Configuracion()
        self._modificado = False
        self._ruta_archivo: str = ""
        self._nombre_archivo: str = "Sin título"

        self._widget_lineas = _NumeroLineas(self)
        self._resaltador: Optional[ResaltadorMarkdown] = None

        self._configurar_fuente()
        self._configurar_editor()
        self._conectar_señales()
        self._inicializar_resaltador()

    # ─── Propiedades ──────────────────────────────────────────────────────────

    @property
    def modificado(self) -> bool:
        return self._modificado

    @property
    def ruta_archivo(self) -> str:
        return self._ruta_archivo

    @ruta_archivo.setter
    def ruta_archivo(self, ruta: str) -> None:
        self._ruta_archivo = ruta

    @property
    def nombre_archivo(self) -> str:
        return self._nombre_archivo

    @nombre_archivo.setter
    def nombre_archivo(self, nombre: str) -> None:
        self._nombre_archivo = nombre

    # ─── Configuración inicial ────────────────────────────────────────────────

    def _configurar_fuente(self) -> None:
        fuente = QFont(self._config.fuente_familia, self._config.fuente_tamanio)
        fuente.setFixedPitch(True)
        self.setFont(fuente)

    def _configurar_editor(self) -> None:
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setTabStopDistance(40)
        self.updateGeometry()

    def _conectar_señales(self) -> None:
        self.blockCountChanged.connect(self._actualizar_ancho_lineas)
        self.updateRequest.connect(self._actualizar_numeros_linea)
        self.textChanged.connect(self._al_texto_cambiado)
        self._actualizar_ancho_lineas()

    def _inicializar_resaltador(self) -> None:
        es_oscuro = self._config.tema == Tema.OSCURO
        self._resaltador = ResaltadorMarkdown(self.document(), tema_oscuro=es_oscuro)

    # ─── Estilo y tema ────────────────────────────────────────────────────────

    def aplicar_tema(self, oscuro: bool) -> None:
        """Actualiza la paleta y el resaltador al cambiar el tema."""
        if self._resaltador:
            self._resaltador.cambiar_tema(oscuro)
        self._widget_lineas.update()

    # ─── Numeración de líneas ─────────────────────────────────────────────────

    def ancho_numeros_linea(self) -> int:
        digitos = max(1, len(str(max(1, self.blockCount()))))
        return 6 + self.fontMetrics().horizontalAdvance("9") * digitos

    def _actualizar_ancho_lineas(self) -> None:
        self.setViewportMargins(self.ancho_numeros_linea(), 0, 0, 0)

    def _actualizar_numeros_linea(self, rect: QRect, dy: int) -> None:
        if dy:
            self._widget_lineas.scroll(0, dy)
        else:
            self._widget_lineas.update(
                0, rect.y(), self._widget_lineas.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self._actualizar_ancho_lineas()

    def resizeEvent(self, evento: QResizeEvent) -> None:  # type: ignore[override]
        super().resizeEvent(evento)
        cr = self.contentsRect()
        self._widget_lineas.setGeometry(
            QRect(cr.left(), cr.top(), self.ancho_numeros_linea(), cr.height())
        )

    def focusInEvent(self, evento) -> None:  # type: ignore[override]
        super().focusInEvent(evento)
        self.foco_recibido.emit()

    def pintar_numeros_linea(self, evento: QPaintEvent) -> None:
        """Dibuja los números de línea en el widget lateral."""
        painter = QPainter(self._widget_lineas)
        oscuro = self._config.tema == Tema.OSCURO
        fondo = QColor("#2C313A") if oscuro else QColor("#F0F0F0")
        texto = QColor("#5C6370") if oscuro else QColor("#9CA3AF")
        actual = QColor("#ABB2BF") if oscuro else QColor("#374151")

        painter.fillRect(evento.rect(), fondo)

        bloque = self.firstVisibleBlock()
        num_bloque = bloque.blockNumber()
        offset = self.contentOffset()
        top = int(self.blockBoundingGeometry(bloque).translated(offset).top())
        bottom = top + int(self.blockBoundingRect(bloque).height())
        linea_actual = self.textCursor().blockNumber()

        while bloque.isValid() and top <= evento.rect().bottom():
            if bloque.isVisible() and bottom >= evento.rect().top():
                numero = str(num_bloque + 1)
                color = actual if num_bloque == linea_actual else texto
                painter.setPen(color)
                painter.drawText(
                    0, top, self._widget_lineas.width() - 2,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, numero
                )
            bloque = bloque.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(bloque).height())
            num_bloque += 1

    # ─── Conteo de palabras y estado de modificación ─────────────────────────

    def _al_texto_cambiado(self) -> None:
        if not self._modificado:
            self._modificado = True
            self.modificado_cambiado.emit(True)
        palabras = len(self.toPlainText().split())
        self.palabras_cambiadas.emit(palabras)

    def marcar_guardado(self) -> None:
        """Restablece el estado de modificación a 'sin cambios'."""
        self._modificado = False
        self.modificado_cambiado.emit(False)

    def contar_palabras(self) -> int:
        texto = self.toPlainText().strip()
        return len(texto.split()) if texto else 0

    # ─── Inserción de formato Markdown ────────────────────────────────────────

    def insertar_formato(self, marcador: str, marcador_fin: str = "") -> None:
        """
        Envuelve el texto seleccionado (o inserta en el cursor) con
        los marcadores dados. Si no hay selección, coloca el cursor entre ellos.
        """
        cursor = self.textCursor()
        seleccion = cursor.selectedText()
        if not marcador_fin:
            marcador_fin = marcador

        if seleccion:
            cursor.insertText(f"{marcador}{seleccion}{marcador_fin}")
            self.setTextCursor(cursor)
        else:
            pos = cursor.position()
            cursor.insertText(f"{marcador}{marcador_fin}")
            cursor.setPosition(pos + len(marcador))
            self.setTextCursor(cursor)

    def insertar_encabezado(self, nivel: int) -> None:
        """Añade el prefijo de encabezado Markdown al inicio de la línea actual."""
        import re
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        linea = cursor.block().text()
        linea_limpia = re.sub(r"^#+\s*", "", linea)
        prefijo = "#" * nivel + " "
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        cursor.insertText(prefijo + linea_limpia)
        self.setTextCursor(cursor)

    def insertar_lista_viñeta(self) -> None:
        """Añade '- ' al inicio de la línea actual."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.insertText("- ")
        self.setTextCursor(cursor)

    def insertar_lista_numerada(self) -> None:
        """Añade '1. ' al inicio de la línea actual."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.insertText("1. ")
        self.setTextCursor(cursor)

    def insertar_cita(self) -> None:
        """Añade '> ' al inicio de la línea actual."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.insertText("> ")
        self.setTextCursor(cursor)

    def insertar_separador(self) -> None:
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        cursor.insertText("\n\n---\n\n")
        self.setTextCursor(cursor)

    def insertar_enlace(self) -> None:
        cursor = self.textCursor()
        seleccion = cursor.selectedText()
        if seleccion:
            cursor.insertText(f"[{seleccion}](url)")
            self.setTextCursor(cursor)
        else:
            pos = cursor.position()
            cursor.insertText("[texto](url)")
            cursor.setPosition(pos + 1)
            self.setTextCursor(cursor)

    # ─── Zoom con la rueda del ratón ─────────────────────────────────────────

    def wheelEvent(self, evento: QWheelEvent) -> None:  # type: ignore[override]
        if evento.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = evento.angleDelta().y()
            fuente = self.font()
            nuevo_tamanio = fuente.pointSize() + (1 if delta > 0 else -1)
            if 6 <= nuevo_tamanio <= 48:
                fuente.setPointSize(nuevo_tamanio)
                self.setFont(fuente)
            evento.accept()
        else:
            super().wheelEvent(evento)
