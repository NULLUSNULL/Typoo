# widgets/barra_estado.py
# Barra de estado inferior con información contextual del editor

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QStatusBar, QWidget


class BarraEstado(QStatusBar):
    """
    Barra de estado con secciones para:
    - Nombre del archivo actual
    - Posición del cursor (línea:columna)
    - Conteo de palabras
    - Estado del documento (guardado / modificado)
    - Modo de escritura (inserción / sobreescritura)
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._construir_secciones()

    def _construir_secciones(self) -> None:
        # Mensaje de estado principal (izquierda)
        self._lbl_estado = QLabel("Listo")
        self.addWidget(self._lbl_estado, 1)

        # Secciones permanentes (derecha, de izquierda a derecha)
        self._lbl_palabras    = self._etiqueta_permanente("Palabras: 0")
        self._lbl_posicion    = self._etiqueta_permanente("Ln 1, Col 1")
        self._lbl_archivo     = self._etiqueta_permanente("Sin archivo")
        self._lbl_modificado  = self._etiqueta_permanente("")

        self.addPermanentWidget(self._lbl_palabras)
        self.addPermanentWidget(self._separador())
        self.addPermanentWidget(self._lbl_posicion)
        self.addPermanentWidget(self._separador())
        self.addPermanentWidget(self._lbl_archivo)
        self.addPermanentWidget(self._separador())
        self.addPermanentWidget(self._lbl_modificado)

    @staticmethod
    def _etiqueta_permanente(texto: str) -> QLabel:
        lbl = QLabel(texto)
        lbl.setMinimumWidth(80)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    @staticmethod
    def _separador() -> QLabel:
        sep = QLabel(" │ ")
        sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return sep

    # ─── Actualizadores públicos ──────────────────────────────────────────────

    def actualizar_palabras(self, palabras: int) -> None:
        self._lbl_palabras.setText(f"Palabras: {palabras:,}")

    def actualizar_posicion(self, linea: int, columna: int) -> None:
        self._lbl_posicion.setText(f"Ln {linea}, Col {columna}")

    def actualizar_archivo(self, nombre: str) -> None:
        # Mostrar solo el nombre del archivo, no la ruta completa
        self._lbl_archivo.setText(nombre or "Sin archivo")

    def actualizar_modificado(self, modificado: bool) -> None:
        if modificado:
            self._lbl_modificado.setText("● Modificado")
            self._lbl_modificado.setStyleSheet("color: #E06C75;")
        else:
            self._lbl_modificado.setText("✓ Guardado")
            self._lbl_modificado.setStyleSheet("color: #98C379;")

    def mostrar_mensaje(self, mensaje: str, tiempo_ms: int = 3000) -> None:
        """Muestra un mensaje temporal en la sección izquierda."""
        self.showMessage(mensaje, tiempo_ms)
