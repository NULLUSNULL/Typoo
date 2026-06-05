# widgets/panel_metadatos.py
# Panel lateral derecho que muestra y edita los metadatos del documento
# (pestaña) que tiene el foco. Los campos dependen del tipo de elemento.

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.metadatos import CampoMeta, esquema_para, etiqueta_tipo
from models.documento import ItemProyecto
from widgets.selector_multiple import SelectorMultiple


class PanelMetadatos(QWidget):
    """
    Panel de detalles del elemento activo. Construye dinámicamente un
    formulario según el tipo de elemento y guarda los cambios en
    `ItemProyecto.metadatos`.
    """

    # Se emite cuando el usuario modifica algún metadato (para persistir).
    metadatos_modificados = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._item: Optional[ItemProyecto] = None
        self._proyecto = None
        self._cargando = False
        self._editores: dict[str, QWidget] = {}
        self._construir_ui()
        self.mostrar_item(None)

    def establecer_proyecto(self, proyecto) -> None:
        """Inyecta el proyecto para resolver referencias (personajes, tramas…)."""
        self._proyecto = proyecto

    def refrescar(self) -> None:
        """Reconstruye el panel (p. ej. al cambiar personajes/tramas disponibles)."""
        self.mostrar_item(self._item)

    # ─── Construcción de la interfaz ──────────────────────────────────────────

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Cabecera del panel
        self._cabecera = QLabel("  Detalles")
        self._cabecera.setFixedHeight(28)
        self._cabecera.setObjectName("CabeceraPanel")
        layout.addWidget(self._cabecera)

        # Zona desplazable con el formulario
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        layout.addWidget(self._scroll, 1)

        self._contenedor = QWidget()
        self._scroll.setWidget(self._contenedor)

        cont_layout = QVBoxLayout(self._contenedor)
        cont_layout.setContentsMargins(12, 12, 12, 12)
        cont_layout.setSpacing(10)

        # Título del elemento (nombre + tipo)
        self._lbl_titulo = QLabel()
        self._lbl_titulo.setWordWrap(True)
        self._lbl_titulo.setStyleSheet("font-size: 15px; font-weight: 600;")
        cont_layout.addWidget(self._lbl_titulo)

        self._lbl_tipo = QLabel()
        self._lbl_tipo.setStyleSheet("font-size: 11px; color: palette(mid);")
        cont_layout.addWidget(self._lbl_tipo)

        # Mensaje cuando no hay metadatos
        self._lbl_vacio = QLabel(
            "Abre una escena, personaje, ubicación, capítulo o nota "
            "para ver y editar sus detalles aquí."
        )
        self._lbl_vacio.setWordWrap(True)
        self._lbl_vacio.setStyleSheet("color: palette(mid);")
        cont_layout.addWidget(self._lbl_vacio)

        # Formulario dinámico
        self._form_widget = QWidget()
        self._form = QFormLayout(self._form_widget)
        self._form.setContentsMargins(0, 6, 0, 0)
        self._form.setSpacing(8)
        self._form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self._form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        # Si el panel es estrecho, la etiqueta pasa arriba y el campo debajo
        # (evita que etiqueta y campo se solapen).
        self._form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        cont_layout.addWidget(self._form_widget)

        cont_layout.addStretch(1)

    # ─── API pública ──────────────────────────────────────────────────────────

    def mostrar_item(self, item: Optional[ItemProyecto]) -> None:
        """Reconstruye el panel para mostrar los metadatos del item dado."""
        self._item = item
        self._limpiar_formulario()

        if item is None:
            self._lbl_titulo.setText("Sin documento activo")
            self._lbl_tipo.setText("")
            self._lbl_vacio.show()
            self._form_widget.hide()
            return

        self._lbl_titulo.setText(item.nombre)
        self._lbl_tipo.setText(etiqueta_tipo(item.tipo).upper())

        campos = esquema_para(item.tipo)
        if not campos:
            self._lbl_vacio.setText(
                f"«{item.nombre}» no tiene metadatos editables."
            )
            self._lbl_vacio.show()
            self._form_widget.hide()
            return

        self._lbl_vacio.hide()
        self._form_widget.show()
        self._construir_campos(campos, item.metadatos or {})

    def refrescar_titulo(self, nombre: str) -> None:
        """Actualiza el nombre mostrado si el elemento se renombra."""
        if self._item is not None:
            self._lbl_titulo.setText(nombre)

    # ─── Construcción dinámica de campos ──────────────────────────────────────

    def _limpiar_formulario(self) -> None:
        self._editores.clear()
        while self._form.count():
            elem = self._form.takeAt(0)
            w = elem.widget()
            if w is not None:
                # Desvincular de inmediato (evita «fantasmas» superpuestos si el
                # formulario se reconstruye antes de que deleteLater se procese).
                w.hide()
                w.setParent(None)
                w.deleteLater()

    def _construir_campos(self, campos: list[CampoMeta], valores: dict) -> None:
        self._cargando = True
        for campo in campos:
            editor = self._crear_editor(campo, valores.get(campo.clave))
            self._editores[campo.clave] = editor
            self._form.addRow(f"{campo.etiqueta}:", editor)
        self._cargando = False

    def _crear_editor(self, campo: CampoMeta, valor) -> QWidget:
        if campo.tipo == "multiline":
            w = QTextEdit()
            w.setAcceptRichText(False)
            w.setFixedHeight(70)
            if campo.marcador:
                w.setPlaceholderText(campo.marcador)
            if valor:
                w.setPlainText(str(valor))
            w.textChanged.connect(lambda c=campo.clave, e=w: self._al_cambiar(c, e.toPlainText()))
            return w

        if campo.tipo == "combo":
            w = QComboBox()
            w.addItem("—")
            w.addItems(list(campo.opciones))
            if valor and valor in campo.opciones:
                w.setCurrentText(str(valor))
            w.currentTextChanged.connect(
                lambda texto, c=campo.clave: self._al_cambiar(c, "" if texto == "—" else texto)
            )
            return w

        if campo.tipo == "int":
            w = QSpinBox()
            w.setRange(0, 1_000_000)
            w.setSingleStep(100)
            w.setGroupSeparatorShown(True)
            try:
                w.setValue(int(valor))
            except (TypeError, ValueError):
                w.setValue(0)
            w.valueChanged.connect(lambda v, c=campo.clave: self._al_cambiar(c, v))
            return w

        if campo.tipo == "ref":
            w = QComboBox()
            w.addItem("—", "")
            for oid, etiqueta in self._opciones_fuente(campo.fuente):
                w.addItem(etiqueta, oid)
            idx = w.findData(valor) if valor else 0
            w.setCurrentIndex(idx if idx >= 0 else 0)
            w.currentIndexChanged.connect(
                lambda _i, c=campo.clave, e=w: self._al_cambiar(c, e.currentData())
            )
            return w

        if campo.tipo == "multiref":
            w = SelectorMultiple(placeholder="Ninguno")
            w.set_opciones(self._opciones_fuente(campo.fuente))
            if isinstance(valor, list):
                w.set_seleccion(valor)
            w.cambiado.connect(lambda ids, c=campo.clave: self._al_cambiar(c, list(ids)))
            return w

        # line (por defecto)
        w = QLineEdit()
        if campo.marcador:
            w.setPlaceholderText(campo.marcador)
        if valor:
            w.setText(str(valor))
        w.textEdited.connect(lambda texto, c=campo.clave: self._al_cambiar(c, texto))
        return w

    # ─── Resolución de opciones (referencias) ─────────────────────────────────

    def _opciones_fuente(self, fuente: str) -> list[tuple[str, str]]:
        """Devuelve [(id, etiqueta)] de la fuente de referencia indicada."""
        if self._proyecto is None or not fuente:
            return []
        if fuente == "personajes":
            return [(p.id, p.nombre) for p in self._proyecto.personajes()]
        if fuente == "ubicaciones":
            return [(u.id, u.nombre) for u in self._proyecto.ubicaciones()]
        if fuente == "tramas":
            return [(t.id, t.nombre) for t in self._proyecto.tramas]
        return []

    # ─── Persistencia de cambios ──────────────────────────────────────────────

    def _al_cambiar(self, clave: str, valor) -> None:
        if self._cargando or self._item is None:
            return
        vacio = valor in ("", None) or (isinstance(valor, list) and not valor)
        if vacio:
            self._item.metadatos.pop(clave, None)
        else:
            self._item.metadatos[clave] = valor
        self.metadatos_modificados.emit()
