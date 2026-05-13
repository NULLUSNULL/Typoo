# widgets/barra_herramientas.py
# Barra de herramientas de formato Markdown para el editor

from __future__ import annotations

from typing import Optional, Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


def _boton_formato(
    texto: str,
    tooltip: str,
    negrita: bool = False,
    cursiva: bool = False,
    ancho: int = 32,
) -> QToolButton:
    """Factoría de botones de la barra de formato."""
    btn = QToolButton()
    btn.setText(texto)
    btn.setToolTip(tooltip)
    btn.setFixedWidth(ancho)
    btn.setFixedHeight(28)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)

    fuente = btn.font()
    fuente.setBold(negrita)
    fuente.setItalic(cursiva)
    btn.setFont(fuente)
    return btn


def _separador_vertical() -> QFrame:
    """Separador visual entre grupos de botones."""
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.VLine)
    sep.setFrameShadow(QFrame.Shadow.Sunken)
    sep.setFixedWidth(8)
    return sep


class BarraHerramientas(QWidget):
    """
    Barra de herramientas de formato Markdown ubicada sobre el editor.
    Emite señales de acción que la ventana principal conecta al editor activo.
    """

    # Señales de formato básico
    negrita_solicitada      = Signal()
    cursiva_solicitada      = Signal()
    subrayado_solicitado    = Signal()
    tachado_solicitado      = Signal()
    encabezado_solicitado   = Signal(int)    # nivel 1-6
    lista_viñeta_solicitada = Signal()
    lista_num_solicitada    = Signal()
    cita_solicitada         = Signal()
    codigo_linea_solicitado = Signal()
    bloque_codigo_solicitado= Signal()
    enlace_solicitado       = Signal()
    separador_solicitado    = Signal()

    # Señales de símbolos especiales
    guion_largo_solicitado  = Signal()       # —
    guion_corto_solicitado  = Signal()       # –
    comillas_esp_solicitadas= Signal()       # « »
    comillas_ing_solicitadas= Signal()       # " "
    puntos_suspension_sol   = Signal()       # …

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("BarraHerramientas")
        self._construir_ui()

    def _construir_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        fila = QWidget()
        layout = QHBoxLayout(fila)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        # ── Grupo: Texto básico ──────────────────────────────────────────────
        self._btn_negrita = _boton_formato("B", "Negrita (Ctrl+B)", negrita=True)
        self._btn_cursiva = _boton_formato("I", "Cursiva (Ctrl+I)", cursiva=True)
        self._btn_subrayado = _boton_formato("U̲", "Subrayado (Ctrl+U)")
        self._btn_tachado = _boton_formato("S̶", "Tachado")

        self._btn_negrita.clicked.connect(self.negrita_solicitada)
        self._btn_cursiva.clicked.connect(self.cursiva_solicitada)
        self._btn_subrayado.clicked.connect(self.subrayado_solicitado)
        self._btn_tachado.clicked.connect(self.tachado_solicitado)

        for btn in [self._btn_negrita, self._btn_cursiva,
                    self._btn_subrayado, self._btn_tachado]:
            layout.addWidget(btn)

        layout.addWidget(_separador_vertical())

        # ── Grupo: Encabezados ───────────────────────────────────────────────
        self._combo_encabezado = QComboBox()
        self._combo_encabezado.setToolTip("Nivel de encabezado")
        self._combo_encabezado.setFixedWidth(80)
        self._combo_encabezado.addItem("Párrafo")
        for i in range(1, 7):
            self._combo_encabezado.addItem(f"H{i}")
        self._combo_encabezado.currentIndexChanged.connect(self._al_cambiar_encabezado)
        layout.addWidget(self._combo_encabezado)

        layout.addWidget(_separador_vertical())

        # ── Grupo: Listas y citas ────────────────────────────────────────────
        self._btn_lista_v = _boton_formato("≡", "Lista con viñetas")
        self._btn_lista_n = _boton_formato("1.", "Lista numerada", ancho=36)
        self._btn_cita    = _boton_formato("❝", "Cita")

        self._btn_lista_v.clicked.connect(self.lista_viñeta_solicitada)
        self._btn_lista_n.clicked.connect(self.lista_num_solicitada)
        self._btn_cita.clicked.connect(self.cita_solicitada)

        for btn in [self._btn_lista_v, self._btn_lista_n, self._btn_cita]:
            layout.addWidget(btn)

        layout.addWidget(_separador_vertical())

        # ── Grupo: Código ────────────────────────────────────────────────────
        self._btn_codigo    = _boton_formato("</>", "Código en línea", ancho=40)
        self._btn_blq_cod   = _boton_formato("```", "Bloque de código", ancho=40)

        self._btn_codigo.clicked.connect(self.codigo_linea_solicitado)
        self._btn_blq_cod.clicked.connect(self.bloque_codigo_solicitado)

        for btn in [self._btn_codigo, self._btn_blq_cod]:
            layout.addWidget(btn)

        layout.addWidget(_separador_vertical())

        # ── Grupo: Enlace y separador ────────────────────────────────────────
        self._btn_enlace = _boton_formato("🔗", "Insertar enlace", ancho=36)
        self._btn_sep    = _boton_formato("─", "Separador horizontal (---)", ancho=36)

        self._btn_enlace.clicked.connect(self.enlace_solicitado)
        self._btn_sep.clicked.connect(self.separador_solicitado)

        for btn in [self._btn_enlace, self._btn_sep]:
            layout.addWidget(btn)

        layout.addWidget(_separador_vertical())

        # ── Grupo: Símbolos literarios ───────────────────────────────────────
        self._btn_guion_largo  = _boton_formato("—", "Guion largo (em dash)")
        self._btn_guion_corto  = _boton_formato("–", "Guion corto (en dash)")
        self._btn_com_esp      = _boton_formato("«»", "Comillas españolas", ancho=36)
        self._btn_com_ing      = _boton_formato('""', "Comillas inglesas", ancho=36)
        self._btn_puntos       = _boton_formato("…", "Puntos suspensivos")

        self._btn_guion_largo.clicked.connect(self.guion_largo_solicitado)
        self._btn_guion_corto.clicked.connect(self.guion_corto_solicitado)
        self._btn_com_esp.clicked.connect(self.comillas_esp_solicitadas)
        self._btn_com_ing.clicked.connect(self.comillas_ing_solicitadas)
        self._btn_puntos.clicked.connect(self.puntos_suspension_sol)

        for btn in [self._btn_guion_largo, self._btn_guion_corto,
                    self._btn_com_esp, self._btn_com_ing, self._btn_puntos]:
            layout.addWidget(btn)

        # Espaciador al final
        layout.addStretch(1)

        outer.addWidget(fila)

        # Separador inferior visible entre la barra de formato y el editor
        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)
        linea.setObjectName("SeparadorBarraFormato")
        outer.addWidget(linea)

    def _al_cambiar_encabezado(self, indice: int) -> None:
        """
        Índice 0 = párrafo (sin encabezado), 1-6 = H1-H6.
        Solo emite la señal si se seleccionó un encabezado real.
        """
        if indice > 0:
            self.encabezado_solicitado.emit(indice)
            # Resetear el combo para que se pueda aplicar de nuevo
            self._combo_encabezado.blockSignals(True)
            self._combo_encabezado.setCurrentIndex(0)
            self._combo_encabezado.blockSignals(False)
