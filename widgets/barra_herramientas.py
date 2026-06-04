# widgets/barra_herramientas.py
# Barra de formato del editor, orientada a la escritura de novelas.
#
# Se han retirado las opciones propias de la escritura técnica (subrayado,
# tachado, código en línea, bloque de código, enlaces y listas numeradas) por
# no ser estrictamente necesarias para redactar prosa narrativa, y se han
# agrupado los caracteres tipográficos en un único botón con submenú.

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QMenu,
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
    Barra de formato ubicada sobre el editor, pensada para novela.
    Emite señales de acción que la ventana principal conecta al editor activo.
    """

    # Formato esencial de prosa
    negrita_solicitada      = Signal()
    cursiva_solicitada      = Signal()
    encabezado_solicitado   = Signal(int)    # 1 = capítulo, 2 = sección, 3 = subsección
    cita_solicitada         = Signal()
    lista_viñeta_solicitada = Signal()
    separador_solicitado    = Signal()       # separador de escena (* * *)

    # Caracteres especiales (submenú)
    caracter_solicitado     = Signal(str)        # inserta el texto tal cual
    envolver_solicitado     = Signal(str, str)   # envuelve la selección (p. ej. comillas)

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
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(3)

        # ── Grupo: Énfasis ───────────────────────────────────────────────────
        self._btn_negrita = _boton_formato("B", "Negrita (Ctrl+B)", negrita=True)
        self._btn_cursiva = _boton_formato("I", "Cursiva (Ctrl+I)", cursiva=True)

        self._btn_negrita.clicked.connect(self.negrita_solicitada)
        self._btn_cursiva.clicked.connect(self.cursiva_solicitada)

        for btn in (self._btn_negrita, self._btn_cursiva):
            layout.addWidget(btn)

        layout.addWidget(_separador_vertical())

        # ── Grupo: Estructura (encabezados) ──────────────────────────────────
        self._combo_encabezado = QComboBox()
        self._combo_encabezado.setToolTip("Nivel de título")
        self._combo_encabezado.setFixedWidth(140)
        self._combo_encabezado.addItem("Texto normal")
        self._combo_encabezado.addItem("Título (capítulo)")
        self._combo_encabezado.addItem("Sección")
        self._combo_encabezado.addItem("Subsección")
        self._combo_encabezado.currentIndexChanged.connect(self._al_cambiar_encabezado)
        layout.addWidget(self._combo_encabezado)

        layout.addWidget(_separador_vertical())

        # ── Grupo: Bloques narrativos ────────────────────────────────────────
        self._btn_cita    = _boton_formato("❝", "Cita / epígrafe")
        self._btn_lista_v = _boton_formato("•", "Lista con viñetas")
        self._btn_sep     = _boton_formato("✻", "Separador de escena (* * *)", ancho=34)

        self._btn_cita.clicked.connect(self.cita_solicitada)
        self._btn_lista_v.clicked.connect(self.lista_viñeta_solicitada)
        self._btn_sep.clicked.connect(self.separador_solicitado)

        for btn in (self._btn_cita, self._btn_lista_v, self._btn_sep):
            layout.addWidget(btn)

        layout.addWidget(_separador_vertical())

        # ── Grupo: Caracteres especiales (botón con submenú) ─────────────────
        self._btn_caracteres = QToolButton()
        self._btn_caracteres.setText("Ω")
        self._btn_caracteres.setToolTip("Caracteres especiales")
        self._btn_caracteres.setFixedHeight(28)
        self._btn_caracteres.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_caracteres.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._btn_caracteres.setMenu(self._crear_menu_caracteres())
        layout.addWidget(self._btn_caracteres)

        # Espaciador al final
        layout.addStretch(1)

        outer.addWidget(fila)

        # Separador inferior visible entre la barra de formato y el editor
        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)
        linea.setObjectName("SeparadorBarraFormato")
        outer.addWidget(linea)

    # ─── Submenú de caracteres especiales ─────────────────────────────────────

    def _crear_menu_caracteres(self) -> QMenu:
        """Construye el menú de caracteres tipográficos útiles para novela."""
        menu = QMenu(self)

        # Inserciones literales: (símbolo, descripción, texto a insertar)
        rayas = [
            ("—", "Raya de diálogo / inciso", "—"),
            ("–", "Guion (rangos: 1820–1830)", "–"),
        ]
        puntuacion = [
            ("…", "Puntos suspensivos", "…"),
            ("¿", "Apertura de interrogación", "¿"),
            ("¡", "Apertura de exclamación", "¡"),
            ("’", "Apóstrofo tipográfico", "’"),
        ]
        ornamentos = [
            ("* * *", "Separador de escena", "\n\n* * *\n\n"),
            ("⁂", "Asterismo", "⁂"),
            ("❧", "Fleurón (hoja)", "❧"),
            ("†", "Cruz / daga", "†"),
            ("‡", "Doble daga", "‡"),
            ("§", "Signo de sección", "§"),
        ]
        # Envoltorios de selección: (símbolo, descripción, apertura, cierre)
        comillas = [
            ("«»", "Comillas latinas (angulares)", "«", "»"),
            ("“”", "Comillas inglesas (dobles)", "“", "”"),
            ("‘’", "Comillas simples", "‘", "’"),
        ]

        menu.addSection("Rayas y guiones")
        self._añadir_inserciones(menu, rayas)

        menu.addSection("Comillas")
        self._añadir_envoltorios(menu, comillas)

        menu.addSection("Puntuación")
        self._añadir_inserciones(menu, puntuacion)

        menu.addSection("Ornamentos y símbolos")
        self._añadir_inserciones(menu, ornamentos)

        return menu

    def _añadir_inserciones(self, menu: QMenu, items) -> None:
        for simbolo, descripcion, texto in items:
            accion = menu.addAction(f"{simbolo}\t{descripcion}")
            accion.triggered.connect(
                lambda _=False, t=texto: self.caracter_solicitado.emit(t)
            )

    def _añadir_envoltorios(self, menu: QMenu, items) -> None:
        for simbolo, descripcion, apertura, cierre in items:
            accion = menu.addAction(f"{simbolo}\t{descripcion}")
            accion.triggered.connect(
                lambda _=False, a=apertura, c=cierre:
                    self.envolver_solicitado.emit(a, c)
            )

    # ─── Encabezados ──────────────────────────────────────────────────────────

    def _al_cambiar_encabezado(self, indice: int) -> None:
        """
        Índice 0 = texto normal, 1 = título (H1), 2 = sección (H2),
        3 = subsección (H3). Solo emite si se eligió un nivel de título real.
        """
        if indice > 0:
            self.encabezado_solicitado.emit(indice)
            # Resetear el combo para poder volver a aplicar el mismo nivel
            self._combo_encabezado.blockSignals(True)
            self._combo_encabezado.setCurrentIndex(0)
            self._combo_encabezado.blockSignals(False)
