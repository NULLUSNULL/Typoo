# editors/editor_markdown.py
# Editor de texto Markdown con numeración de líneas y formato integrado

from __future__ import annotations

import re
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
    tamano_zoom_cambiado = Signal(int)      # Emite el nuevo tamaño tras zoom (Ctrl+rueda)

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
        self.setObjectName("EditorMarkdown")
        self.aplicar_fuente(self._config.fuente_familia, self._config.fuente_tamanio)

    def aplicar_fuente(self, familia: str, tamano: int) -> None:
        """
        Aplica la tipografía al editor. Además de setFont (para que las
        métricas internas sean correctas), fija la familia y el tamaño como
        hoja de estilo propia del widget, que tiene prioridad sobre el QSS
        global de la aplicación (que define la fuente de la interfaz).
        """
        fuente = QFont(familia, tamano)
        fuente.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.setFont(fuente)
        self.setStyleSheet(
            f'QPlainTextEdit#EditorMarkdown {{ font-family: "{familia}"; '
            f'font-size: {tamano}pt; }}'
        )
        if hasattr(self, "_widget_lineas"):
            self._actualizar_ancho_lineas()
            self._widget_lineas.update()

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

    # ─── Listas y sangría (operan sobre las líneas seleccionadas) ─────────────

    def _transformar_lineas(self, func) -> None:
        """
        Aplica `func(texto_linea, indice)` a cada línea abarcada por la
        selección (o a la línea actual si no hay selección) y preserva la
        selección resultante.
        """
        cursor = self.textCursor()
        habia_seleccion = cursor.hasSelection()
        ini, fin = cursor.selectionStart(), cursor.selectionEnd()
        doc = self.document()

        sonda = QTextCursor(doc)
        sonda.setPosition(ini)
        primero = sonda.blockNumber()
        sonda.setPosition(fin)
        ultimo = sonda.blockNumber()

        cursor.beginEditBlock()
        for n in range(primero, ultimo + 1):
            bloque = doc.findBlockByNumber(n)
            c = QTextCursor(bloque)
            c.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            c.movePosition(QTextCursor.MoveOperation.EndOfBlock,
                           QTextCursor.MoveMode.KeepAnchor)
            original = bloque.text()
            nuevo = func(original, n - primero)
            if nuevo != original:
                c.insertText(nuevo)
        cursor.endEditBlock()

        # Restaurar una selección coherente con el rango afectado
        b_ini = doc.findBlockByNumber(primero)
        b_fin = doc.findBlockByNumber(ultimo)
        sel = self.textCursor()
        if habia_seleccion:
            sel.setPosition(b_ini.position())
            sel.setPosition(b_fin.position() + len(b_fin.text()),
                            QTextCursor.MoveMode.KeepAnchor)
        else:
            sel.setPosition(b_ini.position() + len(b_ini.text()))
        self.setTextCursor(sel)

    @staticmethod
    def _sangria(linea: str) -> str:
        return re.match(r"^(\s*)", linea).group(1)

    def alternar_lista_vinetas(self) -> None:
        """Activa o quita la viñeta '- ' en cada línea seleccionada."""
        def f(linea: str, _i: int) -> str:
            if not linea.strip():
                return linea
            m = re.match(r"^(\s*)([-*+]\s+)(.*)$", linea)
            if m:
                return m.group(1) + m.group(3)
            s = self._sangria(linea)
            return f"{s}- {linea[len(s):]}"
        self._transformar_lineas(f)

    def alternar_lista_numerada(self) -> None:
        """Activa o quita la numeración '1. 2. …' en las líneas seleccionadas."""
        def f(linea: str, i: int) -> str:
            if not linea.strip():
                return linea
            m = re.match(r"^(\s*)(\d+\.\s+)(.*)$", linea)
            if m:
                return m.group(1) + m.group(3)
            s = self._sangria(linea)
            return f"{s}{i + 1}. {linea[len(s):]}"
        self._transformar_lineas(f)

    def aumentar_sangria(self) -> None:
        """Aumenta un nivel de sangría (cuatro espacios) → listas multinivel."""
        self._transformar_lineas(lambda l, _i: ("    " + l) if l.strip() else l)

    def disminuir_sangria(self) -> None:
        """Reduce un nivel de sangría."""
        def f(linea: str, _i: int) -> str:
            if linea.startswith("    "):
                return linea[4:]
            if linea.startswith("\t"):
                return linea[1:]
            return re.sub(r"^[ \t]{1,4}", "", linea)
        self._transformar_lineas(f)

    def _en_linea_lista(self) -> bool:
        linea = self.textCursor().block().text()
        return bool(re.match(r"^\s*([-*+]|\d+\.)\s", linea))

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

    # ─── Sangría con el teclado (Tab / Mayús+Tab) ────────────────────────────

    def keyPressEvent(self, evento) -> None:  # type: ignore[override]
        es_tab = evento.key() == Qt.Key.Key_Tab
        es_backtab = evento.key() == Qt.Key.Key_Backtab
        mays = bool(evento.modifiers() & Qt.KeyboardModifier.ShiftModifier)

        if es_backtab or (es_tab and mays):
            self.disminuir_sangria()
            evento.accept()
            return
        if es_tab:
            cursor = self.textCursor()
            # Tab sangra cuando hay selección de varias líneas o se está en una lista
            if cursor.hasSelection() or self._en_linea_lista():
                self.aumentar_sangria()
                evento.accept()
                return
        super().keyPressEvent(evento)

    # ─── Zoom con la rueda del ratón ─────────────────────────────────────────

    def wheelEvent(self, evento: QWheelEvent) -> None:  # type: ignore[override]
        if evento.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = evento.angleDelta().y()
            nuevo_tamanio = self.font().pointSize() + (1 if delta > 0 else -1)
            if 6 <= nuevo_tamanio <= 48:
                self.aplicar_fuente(self.font().family(), nuevo_tamanio)
                self.tamano_zoom_cambiado.emit(nuevo_tamanio)
            evento.accept()
        else:
            super().wheelEvent(evento)
