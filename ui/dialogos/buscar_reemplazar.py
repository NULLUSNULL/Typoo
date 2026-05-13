# ui/dialogos/buscar_reemplazar.py
# Diálogo de búsqueda y reemplazo de texto

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class DialogoBuscarReemplazar(QDialog):
    """
    Diálogo no modal de búsqueda y reemplazo.
    Emite señales que la ventana principal intercepta para operar sobre el editor activo.
    """

    # Señales para comunicarse con la ventana principal
    buscar_solicitado       = Signal(str, bool, bool)    # (patron, regex, ignorar_mayus)
    buscar_siguiente        = Signal()
    buscar_anterior         = Signal()
    reemplazar_solicitado   = Signal(str, str, bool, bool)  # (patron, reemplazo, regex, ignorar)
    reemplazar_todo         = Signal(str, str, bool, bool)
    buscar_proyecto         = Signal(str, bool, bool)    # búsqueda en todo el proyecto

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Buscar y reemplazar")
        self.setMinimumWidth(460)
        # No modal: permite editar mientras el diálogo está abierto
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        )
        self._construir_ui()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Pestañas: Buscar / Buscar y reemplazar / En proyecto
        self._pestanas = QTabWidget()
        self._pestanas.addTab(self._tab_buscar(),        "Buscar")
        self._pestanas.addTab(self._tab_reemplazar(),    "Reemplazar")
        self._pestanas.addTab(self._tab_en_proyecto(),   "En el proyecto")
        layout.addWidget(self._pestanas)

        # Opciones comunes
        grupo_opciones = QGroupBox("Opciones")
        lay_opciones = QHBoxLayout(grupo_opciones)
        self._chk_ignorar = QCheckBox("Ignorar mayúsculas")
        self._chk_ignorar.setChecked(True)
        self._chk_regex    = QCheckBox("Expresión regular")
        lay_opciones.addWidget(self._chk_ignorar)
        lay_opciones.addWidget(self._chk_regex)
        lay_opciones.addStretch()
        layout.addWidget(grupo_opciones)

        # Botón Cerrar
        self._lbl_resultado = QLabel("")
        self._lbl_resultado.setStyleSheet("color: gray;")
        layout.addWidget(self._lbl_resultado)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)

    def _tab_buscar(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)

        lay_campo = QHBoxLayout()
        lay_campo.addWidget(QLabel("Buscar:"))
        self._campo_buscar = QLineEdit()
        self._campo_buscar.setPlaceholderText("Texto a buscar…")
        self._campo_buscar.returnPressed.connect(self._al_buscar)
        lay_campo.addWidget(self._campo_buscar)
        layout.addLayout(lay_campo)

        lay_botones = QHBoxLayout()
        btn_anterior  = QPushButton("◀ Anterior")
        btn_siguiente = QPushButton("Siguiente ▶")
        btn_anterior.clicked.connect(self.buscar_anterior)
        btn_siguiente.clicked.connect(self._al_buscar)
        lay_botones.addStretch()
        lay_botones.addWidget(btn_anterior)
        lay_botones.addWidget(btn_siguiente)
        layout.addLayout(lay_botones)
        layout.addStretch()
        return widget

    def _tab_reemplazar(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)

        lay1 = QHBoxLayout()
        lay1.addWidget(QLabel("Buscar:  "))
        self._campo_buscar_r = QLineEdit()
        self._campo_buscar_r.setPlaceholderText("Texto a buscar…")
        lay1.addWidget(self._campo_buscar_r)
        layout.addLayout(lay1)

        lay2 = QHBoxLayout()
        lay2.addWidget(QLabel("Reemplazar:"))
        self._campo_reemplazo = QLineEdit()
        self._campo_reemplazo.setPlaceholderText("Texto de reemplazo…")
        lay2.addWidget(self._campo_reemplazo)
        layout.addLayout(lay2)

        lay_btn = QHBoxLayout()
        btn_uno  = QPushButton("Reemplazar")
        btn_todo = QPushButton("Reemplazar todo")
        btn_uno.clicked.connect(self._al_reemplazar_uno)
        btn_todo.clicked.connect(self._al_reemplazar_todo)
        lay_btn.addStretch()
        lay_btn.addWidget(btn_uno)
        lay_btn.addWidget(btn_todo)
        layout.addLayout(lay_btn)
        layout.addStretch()
        return widget

    def _tab_en_proyecto(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)

        lay = QHBoxLayout()
        lay.addWidget(QLabel("Buscar:"))
        self._campo_buscar_p = QLineEdit()
        self._campo_buscar_p.setPlaceholderText("Buscar en todos los archivos del proyecto…")
        lay.addWidget(self._campo_buscar_p)
        layout.addLayout(lay)

        btn = QPushButton("Buscar en todo el proyecto")
        btn.clicked.connect(self._al_buscar_proyecto)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addStretch()
        return widget

    # ─── Callbacks internos ───────────────────────────────────────────────────

    def _opciones(self) -> tuple[bool, bool]:
        return self._chk_regex.isChecked(), self._chk_ignorar.isChecked()

    def _al_buscar(self) -> None:
        patron = self._campo_buscar.text()
        if patron:
            regex, ignorar = self._opciones()
            self.buscar_solicitado.emit(patron, regex, ignorar)

    def _al_reemplazar_uno(self) -> None:
        patron    = self._campo_buscar_r.text()
        reemplazo = self._campo_reemplazo.text()
        if patron:
            regex, ignorar = self._opciones()
            self.reemplazar_solicitado.emit(patron, reemplazo, regex, ignorar)

    def _al_reemplazar_todo(self) -> None:
        patron    = self._campo_buscar_r.text()
        reemplazo = self._campo_reemplazo.text()
        if patron:
            regex, ignorar = self._opciones()
            self.reemplazar_todo.emit(patron, reemplazo, regex, ignorar)

    def _al_buscar_proyecto(self) -> None:
        patron = self._campo_buscar_p.text()
        if patron:
            regex, ignorar = self._opciones()
            self.buscar_proyecto.emit(patron, regex, ignorar)

    def mostrar_resultado(self, texto: str) -> None:
        self._lbl_resultado.setText(texto)

    def establecer_texto_busqueda(self, texto: str) -> None:
        """Pre-rellena el campo de búsqueda con texto seleccionado en el editor."""
        self._campo_buscar.setText(texto)
        self._campo_buscar_r.setText(texto)
