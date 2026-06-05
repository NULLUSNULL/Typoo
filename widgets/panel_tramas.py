# widgets/panel_tramas.py
# Visor de tramas: rejilla «story grid» que cruza las escenas (en orden de
# lectura) con tramas, personajes o ubicaciones, coloreada por entidad.
#
# Flujos que cubre:
#   Trama     → escenas que la desarrollan
#   Personaje → escenas en las que aparece
#   Ubicación → escenas que ocurren ahí

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QColorDialog,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.constantes import TipoElemento
from models.proyecto import COLORES_TRAMA

# Categorías del visor
CAT_TRAMAS = "Tramas"
CAT_PERSONAJES = "Personajes"
CAT_UBICACIONES = "Ubicaciones"


class PanelTramas(QWidget):
    """Rejilla de relaciones entidad × escena, coloreada por entidad."""

    relaciones_modificadas = Signal()   # cambió un vínculo escena↔trama (persistir)
    tramas_modificadas     = Signal()   # alta/baja/edición de tramas (persistir)
    escena_activada        = Signal(object)  # ItemProyecto de escena (abrir)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._proyecto = None
        self._entidades: list[tuple[str, str, str]] = []   # (id, nombre, color)
        self._escenas: list = []
        self._construir_ui()

    # ─── Construcción de la interfaz ──────────────────────────────────────────

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barra superior
        barra = QWidget()
        hb = QHBoxLayout(barra)
        hb.setContentsMargins(8, 6, 8, 6)
        hb.setSpacing(6)

        hb.addWidget(QLabel("Ver por:"))
        self._combo_categoria = QComboBox()
        self._combo_categoria.addItems([CAT_TRAMAS, CAT_PERSONAJES, CAT_UBICACIONES])
        self._combo_categoria.currentTextChanged.connect(self._refrescar)
        hb.addWidget(self._combo_categoria)

        hb.addSpacing(12)
        self._btn_nueva = QPushButton("＋ Trama")
        self._btn_renombrar = QPushButton("Renombrar")
        self._btn_color = QPushButton("Color")
        self._btn_eliminar = QPushButton("Eliminar")
        self._btn_nueva.clicked.connect(self._nueva_trama)
        self._btn_renombrar.clicked.connect(self._renombrar_trama)
        self._btn_color.clicked.connect(self._cambiar_color_trama)
        self._btn_eliminar.clicked.connect(self._eliminar_trama)
        for b in (self._btn_nueva, self._btn_renombrar, self._btn_color, self._btn_eliminar):
            hb.addWidget(b)

        hb.addStretch(1)
        self._lbl_ayuda = QLabel("Haz clic en una celda para marcar la escena.")
        self._lbl_ayuda.setStyleSheet("color: palette(mid);")
        hb.addWidget(self._lbl_ayuda)

        layout.addWidget(barra)

        # Rejilla
        self._tabla = QTableWidget()
        self._tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tabla.verticalHeader().setDefaultSectionSize(26)
        self._tabla.horizontalHeader().setDefaultSectionSize(96)
        self._tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self._tabla.cellClicked.connect(self._al_clic_celda)
        self._tabla.cellDoubleClicked.connect(self._al_doble_clic_celda)
        layout.addWidget(self._tabla, 1)

    # ─── API pública ──────────────────────────────────────────────────────────

    def establecer_proyecto(self, proyecto) -> None:
        self._proyecto = proyecto
        self.refrescar()

    def refrescar(self) -> None:
        self._refrescar(self._combo_categoria.currentText())

    # ─── Construcción de la rejilla ───────────────────────────────────────────

    def _categoria(self) -> str:
        return self._combo_categoria.currentText()

    def _entidades_categoria(self) -> list[tuple[str, str, str]]:
        if self._proyecto is None:
            return []
        cat = self._categoria()
        if cat == CAT_TRAMAS:
            return [(t.id, t.nombre, t.color) for t in self._proyecto.tramas]
        if cat == CAT_PERSONAJES:
            base = self._proyecto.personajes()
        else:
            base = self._proyecto.ubicaciones()
        return [
            (e.id, e.nombre, COLORES_TRAMA[i % len(COLORES_TRAMA)])
            for i, e in enumerate(base)
        ]

    def _escena_relacionada(self, entidad_id: str, escena) -> bool:
        cat = self._categoria()
        meta = escena.metadatos or {}
        if cat == CAT_TRAMAS:
            return entidad_id in (meta.get("tramas") or [])
        if cat == CAT_PERSONAJES:
            return entidad_id in (meta.get("personajes") or []) or meta.get("pov") == entidad_id
        return meta.get("ubicacion") == entidad_id

    def _refrescar(self, _categoria: str = "") -> None:
        es_tramas = self._categoria() == CAT_TRAMAS
        for b in (self._btn_nueva, self._btn_renombrar, self._btn_color, self._btn_eliminar):
            b.setVisible(es_tramas)
        self._lbl_ayuda.setVisible(es_tramas)

        self._entidades = self._entidades_categoria()
        self._escenas = self._proyecto.escenas_en_orden() if self._proyecto else []

        tabla = self._tabla
        tabla.blockSignals(True)
        tabla.clear()
        tabla.setColumnCount(len(self._escenas))
        tabla.setRowCount(len(self._entidades))

        tabla.setHorizontalHeaderLabels([e.nombre for e in self._escenas])
        for c, esc in enumerate(self._escenas):
            hi = tabla.horizontalHeaderItem(c)
            if hi:
                hi.setToolTip(esc.nombre)

        for r, (eid, nombre, color) in enumerate(self._entidades):
            cab = QTableWidgetItem(nombre)
            cab.setBackground(QColor(color))
            cab.setForeground(QColor("#FFFFFF"))
            cab.setToolTip(nombre)
            tabla.setVerticalHeaderItem(r, cab)
            for c, esc in enumerate(self._escenas):
                celda = QTableWidgetItem()
                if self._escena_relacionada(eid, esc):
                    celda.setBackground(QColor(color))
                celda.setToolTip(f"{nombre} · {esc.nombre}")
                tabla.setItem(r, c, celda)

        tabla.blockSignals(False)

    # ─── Interacción con la rejilla ───────────────────────────────────────────

    def _al_clic_celda(self, fila: int, columna: int) -> None:
        # Solo se pueden alternar las relaciones de tramas (las demás se editan
        # en el panel de Detalles de la escena).
        if self._categoria() != CAT_TRAMAS:
            return
        if not (0 <= fila < len(self._entidades)) or not (0 <= columna < len(self._escenas)):
            return
        trama_id, _nombre, color = self._entidades[fila]
        escena = self._escenas[columna]
        refs = escena.metadatos.get("tramas")
        if not isinstance(refs, list):
            refs = []
            escena.metadatos["tramas"] = refs
        celda = self._tabla.item(fila, columna)
        if trama_id in refs:
            refs.remove(trama_id)
            if celda:
                celda.setBackground(QColor(0, 0, 0, 0))
        else:
            refs.append(trama_id)
            if celda:
                celda.setBackground(QColor(color))
        if not refs:
            escena.metadatos.pop("tramas", None)
        self.relaciones_modificadas.emit()

    def _al_doble_clic_celda(self, fila: int, columna: int) -> None:
        if 0 <= columna < len(self._escenas):
            self.escena_activada.emit(self._escenas[columna])

    # ─── Gestión de tramas ────────────────────────────────────────────────────

    def _trama_seleccionada(self):
        fila = self._tabla.currentRow()
        if self._categoria() == CAT_TRAMAS and 0 <= fila < len(self._entidades):
            return self._proyecto.trama_por_id(self._entidades[fila][0])
        return None

    def _nueva_trama(self) -> None:
        if self._proyecto is None:
            return
        nombre, ok = QInputDialog.getText(self, "Nueva trama", "Nombre de la trama:")
        if ok and nombre.strip():
            self._proyecto.agregar_trama(nombre.strip())
            self.tramas_modificadas.emit()
            self.refrescar()

    def _renombrar_trama(self) -> None:
        trama = self._trama_seleccionada()
        if not trama:
            return
        nombre, ok = QInputDialog.getText(
            self, "Renombrar trama", "Nuevo nombre:", text=trama.nombre
        )
        if ok and nombre.strip():
            trama.nombre = nombre.strip()
            self.tramas_modificadas.emit()
            self.refrescar()

    def _cambiar_color_trama(self) -> None:
        trama = self._trama_seleccionada()
        if not trama:
            return
        color = QColorDialog.getColor(QColor(trama.color), self, "Color de la trama")
        if color.isValid():
            trama.color = color.name()
            self.tramas_modificadas.emit()
            self.refrescar()

    def _eliminar_trama(self) -> None:
        trama = self._trama_seleccionada()
        if not trama:
            return
        resp = QMessageBox.question(
            self, "Eliminar trama",
            f"¿Eliminar la trama «{trama.nombre}»?\n"
            "Se desvinculará de todas las escenas.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if resp == QMessageBox.StandardButton.Yes:
            self._proyecto.eliminar_trama(trama.id)
            self.tramas_modificadas.emit()
            self.refrescar()
