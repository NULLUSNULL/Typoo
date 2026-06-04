# widgets/barra_herramientas.py
# Barra de formato del editor, al estilo de un procesador de textos pero
# orientada a la escritura de novelas.
#
# Incluye selector de tipografía y tamaño, énfasis (negrita, cursiva,
# subrayado, tachado, subíndice, superíndice), niveles de título, citas,
# listas (viñetas, numeradas y multinivel mediante sangría) y un submenú de
# caracteres especiales.

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QMenu,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.configuracion import Configuracion
from core.fuentes import grupos_para_selector

# Tamaños de fuente ofrecidos en el selector.
_TAMANOS = [10, 11, 12, 13, 14, 15, 16, 18, 20, 22, 24, 28, 32]


def _boton_formato(
    texto: str,
    tooltip: str,
    negrita: bool = False,
    cursiva: bool = False,
    subrayado: bool = False,
    tachado: bool = False,
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
    fuente.setUnderline(subrayado)
    fuente.setStrikeOut(tachado)
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
    Barra de formato ubicada sobre el editor.
    Emite señales de acción que la ventana principal conecta al editor activo.
    """

    # Tipografía
    fuente_cambiada         = Signal(str)
    tamano_cambiado         = Signal(int)

    # Énfasis de carácter
    negrita_solicitada      = Signal()
    cursiva_solicitada      = Signal()
    subrayado_solicitado    = Signal()
    tachado_solicitado      = Signal()
    subindice_solicitado    = Signal()
    superindice_solicitado  = Signal()

    # Estructura
    encabezado_solicitado   = Signal(int)    # 1 = título, 2 = sección, 3 = subsección
    cita_solicitada         = Signal()

    # Listas
    lista_viñeta_solicitada = Signal()
    lista_num_solicitada    = Signal()
    sangria_aumentar_sol    = Signal()       # multinivel: aumentar nivel
    sangria_disminuir_sol   = Signal()       # multinivel: disminuir nivel

    # Separador de escena
    separador_solicitado    = Signal()

    # Caracteres especiales (submenú)
    caracter_solicitado     = Signal(str)        # inserta el texto tal cual
    envolver_solicitado     = Signal(str, str)   # envuelve la selección (comillas)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("BarraHerramientas")
        self._config = Configuracion()
        self._construir_ui()

    def _construir_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        fila = QWidget()
        layout = QHBoxLayout(fila)
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(3)

        # ── Grupo: Tipografía ────────────────────────────────────────────────
        self._combo_fuente = self._crear_combo_fuentes()
        self._combo_fuente.currentTextChanged.connect(self._al_cambiar_fuente)
        layout.addWidget(self._combo_fuente)

        self._combo_tamano = QComboBox()
        self._combo_tamano.setToolTip("Tamaño de fuente")
        self._combo_tamano.setFixedWidth(58)
        self._combo_tamano.setEditable(True)
        self._combo_tamano.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        for t in _TAMANOS:
            self._combo_tamano.addItem(str(t))
        self._seleccionar_tamano_inicial()
        self._combo_tamano.currentTextChanged.connect(self._al_cambiar_tamano)
        layout.addWidget(self._combo_tamano)

        layout.addWidget(_separador_vertical())

        # ── Grupo: Énfasis ───────────────────────────────────────────────────
        self._btn_negrita   = _boton_formato("B", "Negrita (Ctrl+B)", negrita=True)
        self._btn_cursiva   = _boton_formato("I", "Cursiva (Ctrl+I)", cursiva=True)
        self._btn_subrayado = _boton_formato("U", "Subrayado (Ctrl+U)", subrayado=True)
        self._btn_tachado   = _boton_formato("S", "Tachado", tachado=True)
        self._btn_subindice = _boton_formato("x₂", "Subíndice", ancho=34)
        self._btn_superind  = _boton_formato("x²", "Superíndice", ancho=34)

        self._btn_negrita.clicked.connect(self.negrita_solicitada)
        self._btn_cursiva.clicked.connect(self.cursiva_solicitada)
        self._btn_subrayado.clicked.connect(self.subrayado_solicitado)
        self._btn_tachado.clicked.connect(self.tachado_solicitado)
        self._btn_subindice.clicked.connect(self.subindice_solicitado)
        self._btn_superind.clicked.connect(self.superindice_solicitado)

        for btn in (self._btn_negrita, self._btn_cursiva, self._btn_subrayado,
                    self._btn_tachado, self._btn_subindice, self._btn_superind):
            layout.addWidget(btn)

        layout.addWidget(_separador_vertical())

        # ── Grupo: Estructura (títulos) ──────────────────────────────────────
        self._combo_encabezado = QComboBox()
        self._combo_encabezado.setToolTip("Nivel de título")
        self._combo_encabezado.setFixedWidth(140)
        self._combo_encabezado.addItem("Texto normal")
        self._combo_encabezado.addItem("Título (capítulo)")
        self._combo_encabezado.addItem("Sección")
        self._combo_encabezado.addItem("Subsección")
        self._combo_encabezado.currentIndexChanged.connect(self._al_cambiar_encabezado)
        layout.addWidget(self._combo_encabezado)

        self._btn_cita = _boton_formato("❝", "Cita / epígrafe")
        self._btn_cita.clicked.connect(self.cita_solicitada)
        layout.addWidget(self._btn_cita)

        layout.addWidget(_separador_vertical())

        # ── Grupo: Listas ────────────────────────────────────────────────────
        self._btn_lista_v = _boton_formato("•", "Lista con viñetas")
        self._btn_lista_n = _boton_formato("1.", "Lista numerada", ancho=34)
        self._btn_sang_mas = _boton_formato("⇥", "Aumentar nivel / sangría (Tab)", ancho=32)
        self._btn_sang_men = _boton_formato("⇤", "Disminuir nivel / sangría (Mayús+Tab)", ancho=32)

        self._btn_lista_v.clicked.connect(self.lista_viñeta_solicitada)
        self._btn_lista_n.clicked.connect(self.lista_num_solicitada)
        self._btn_sang_mas.clicked.connect(self.sangria_aumentar_sol)
        self._btn_sang_men.clicked.connect(self.sangria_disminuir_sol)

        for btn in (self._btn_lista_v, self._btn_lista_n,
                    self._btn_sang_mas, self._btn_sang_men):
            layout.addWidget(btn)

        layout.addWidget(_separador_vertical())

        # ── Grupo: Separador de escena y caracteres especiales ───────────────
        self._btn_sep = _boton_formato("✻", "Separador de escena (* * *)", ancho=34)
        self._btn_sep.clicked.connect(self.separador_solicitado)
        layout.addWidget(self._btn_sep)

        self._btn_caracteres = QToolButton()
        self._btn_caracteres.setText("Ω")
        self._btn_caracteres.setToolTip("Caracteres especiales")
        self._btn_caracteres.setFixedHeight(28)
        self._btn_caracteres.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_caracteres.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._btn_caracteres.setMenu(self._crear_menu_caracteres())
        layout.addWidget(self._btn_caracteres)

        layout.addStretch(1)
        outer.addWidget(fila)

        # Separador inferior visible entre la barra de formato y el editor
        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)
        linea.setObjectName("SeparadorBarraFormato")
        outer.addWidget(linea)

    # ─── Selector de fuentes ──────────────────────────────────────────────────

    def _crear_combo_fuentes(self) -> QComboBox:
        """Combo de fuentes con encabezados de grupo no seleccionables."""
        combo = QComboBox()
        combo.setToolTip("Tipografía del editor")
        combo.setFixedWidth(170)
        modelo = QStandardItemModel(combo)

        actual = self._config.fuente_familia
        indice_actual = -1
        for titulo, familias in grupos_para_selector():
            cabecera = QStandardItem(f"— {titulo} —")
            cabecera.setFlags(Qt.ItemFlag.NoItemFlags)   # no seleccionable
            modelo.appendRow(cabecera)
            for fam in familias:
                item = QStandardItem(fam)
                # Mostrar cada nombre con su propia tipografía
                fuente = item.font()
                fuente.setFamily(fam)
                item.setFont(fuente)
                modelo.appendRow(item)
                if fam == actual:
                    indice_actual = modelo.rowCount() - 1

        combo.setModel(modelo)
        combo.blockSignals(True)
        if indice_actual >= 0:
            combo.setCurrentIndex(indice_actual)
        else:
            # Si la fuente configurada no está en la lista, añadirla al final
            combo.addItem(actual)
            combo.setCurrentText(actual)
        combo.blockSignals(False)
        return combo

    def _seleccionar_tamano_inicial(self) -> None:
        actual = str(self._config.fuente_tamanio)
        idx = self._combo_tamano.findText(actual)
        self._combo_tamano.blockSignals(True)
        if idx >= 0:
            self._combo_tamano.setCurrentIndex(idx)
        else:
            self._combo_tamano.setCurrentText(actual)
        self._combo_tamano.blockSignals(False)

    def _al_cambiar_fuente(self, familia: str) -> None:
        if familia and not familia.startswith("—"):
            self.fuente_cambiada.emit(familia)

    def _al_cambiar_tamano(self, texto: str) -> None:
        try:
            valor = int(texto)
        except ValueError:
            return
        if 6 <= valor <= 96:
            self.tamano_cambiado.emit(valor)

    # ─── Submenú de caracteres especiales ─────────────────────────────────────

    def _crear_menu_caracteres(self) -> QMenu:
        """Construye el menú de caracteres tipográficos útiles para novela."""
        menu = QMenu(self)

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
        """1 = título (H1), 2 = sección (H2), 3 = subsección (H3)."""
        if indice > 0:
            self.encabezado_solicitado.emit(indice)
            self._combo_encabezado.blockSignals(True)
            self._combo_encabezado.setCurrentIndex(0)
            self._combo_encabezado.blockSignals(False)

    # ─── API para sincronizar con la configuración ───────────────────────────

    def reflejar_fuente(self, familia: str, tamano: int) -> None:
        """Actualiza los selectores sin reemitir señales (p. ej. tras zoom)."""
        self._combo_fuente.blockSignals(True)
        idx = self._combo_fuente.findText(familia)
        if idx >= 0:
            self._combo_fuente.setCurrentIndex(idx)
        self._combo_fuente.blockSignals(False)

        self._combo_tamano.blockSignals(True)
        self._combo_tamano.setCurrentText(str(tamano))
        self._combo_tamano.blockSignals(False)
