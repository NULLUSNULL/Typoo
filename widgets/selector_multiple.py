# widgets/selector_multiple.py
# Selector de múltiples elementos: un botón que abre un menú con casillas.

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QSizePolicy, QToolButton, QWidget


class SelectorMultiple(QToolButton):
    """
    Botón compacto que despliega un menú con casillas para seleccionar varios
    elementos de una lista (id, etiqueta). Emite `cambiado` con los ids elegidos.
    """

    cambiado = Signal(list)

    def __init__(self, placeholder: str = "Ninguno", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._placeholder = placeholder
        self._opciones: list[tuple[str, str]] = []
        self._seleccion: set[str] = set()
        self._menu = QMenu(self)
        self.setMenu(self._menu)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._actualizar_texto()

    # ─── API ──────────────────────────────────────────────────────────────────

    def set_opciones(self, opciones: list[tuple[str, str]]) -> None:
        """opciones: lista de (id, etiqueta)."""
        self._opciones = list(opciones)
        # Conservar solo la selección que siga existiendo
        ids_validos = {oid for oid, _ in self._opciones}
        self._seleccion &= ids_validos
        self._reconstruir_menu()
        self._actualizar_texto()

    def set_seleccion(self, ids) -> None:
        self._seleccion = {i for i in (ids or []) if any(oid == i for oid, _ in self._opciones)}
        self._reconstruir_menu()
        self._actualizar_texto()

    def seleccion(self) -> list[str]:
        # Mantener el orden de las opciones
        return [oid for oid, _ in self._opciones if oid in self._seleccion]

    # ─── Construcción interna ─────────────────────────────────────────────────

    def _reconstruir_menu(self) -> None:
        self._menu.clear()
        if not self._opciones:
            vacio = self._menu.addAction("(sin elementos)")
            vacio.setEnabled(False)
            return
        for oid, etiqueta in self._opciones:
            accion = QAction(etiqueta, self._menu)
            accion.setCheckable(True)
            accion.setChecked(oid in self._seleccion)
            accion.toggled.connect(lambda marcado, i=oid: self._al_alternar(i, marcado))
            self._menu.addAction(accion)

    def _al_alternar(self, oid: str, marcado: bool) -> None:
        if marcado:
            self._seleccion.add(oid)
        else:
            self._seleccion.discard(oid)
        self._actualizar_texto()
        self.cambiado.emit(self.seleccion())

    def _actualizar_texto(self) -> None:
        nombres = [et for oid, et in self._opciones if oid in self._seleccion]
        if not nombres:
            self.setText(f"  {self._placeholder}  ▾")
        elif len(nombres) <= 2:
            self.setText("  " + ", ".join(nombres) + "  ▾")
        else:
            self.setText(f"  {nombres[0]} +{len(nombres) - 1}  ▾")
        self.setToolTip(", ".join(nombres) if nombres else self._placeholder)
