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
    QListWidget,
    QListWidgetItem,
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
    resultado_activado      = Signal(object)             # resultado de la lista elegido

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Buscar y reemplazar")
        self.setMinimumWidth(460)
        self.resize(560, 460)
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
        self._campo_buscar_p.returnPressed.connect(self._al_buscar_proyecto)
        lay.addWidget(self._campo_buscar_p)
        btn = QPushButton("Buscar en el proyecto")
        btn.clicked.connect(self._al_buscar_proyecto)
        lay.addWidget(btn)
        layout.addLayout(lay)

        self._lista_resultados = QListWidget()
        self._lista_resultados.setObjectName("ListaResultadosProyecto")
        self._lista_resultados.setAlternatingRowColors(False)
        self._lista_resultados.setStyleSheet(
            "#ListaResultadosProyecto::item { padding: 4px 6px; border-radius: 5px; }"
            "#ListaResultadosProyecto::item:selected,"
            "#ListaResultadosProyecto::item:selected:!active {"
            " background: #2F6FE0; color: #FFFFFF; }"
        )
        self._lista_resultados.itemActivated.connect(self._al_activar_resultado)
        layout.addWidget(self._lista_resultados, 1)

        ayuda = QLabel("Doble clic (o Intro) en un resultado para ir a esa línea.")
        ayuda.setStyleSheet("color: #8A8F98;")
        layout.addWidget(ayuda)
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

    # ─── Resultados de la búsqueda en el proyecto ──────────────────────────────

    def mostrar_resultados_proyecto(self, encontrados: list) -> None:
        """Rellena la lista con los resultados, agrupados por documento.

        `encontrados` es una lista de tuplas (ItemProyecto, ResultadoBusqueda),
        ya ordenada por documento. Cada resultado se guarda en el propio
        QListWidgetItem para poder recuperarlo al activarlo."""
        self._lista_resultados.clear()
        item_id_anterior = None
        for item_proyecto, resultado in encontrados:
            if item_proyecto.id != item_id_anterior:
                cabecera = QListWidgetItem(f"📄 {item_proyecto.nombre}")
                cabecera.setFlags(Qt.ItemFlag.NoItemFlags)
                f = cabecera.font()
                f.setBold(True)
                cabecera.setFont(f)
                self._lista_resultados.addItem(cabecera)
                item_id_anterior = item_proyecto.id
            fila = QListWidgetItem(
                f"      línea {resultado.numero_linea}:  {_contexto(resultado)}")
            fila.setData(Qt.ItemDataRole.UserRole, (item_proyecto, resultado))
            self._lista_resultados.addItem(fila)

        n = len(encontrados)
        self.mostrar_resultado(
            f"{n} coincidencia(s) en todo el proyecto." if n else
            "Sin coincidencias en el proyecto.")

    def _al_activar_resultado(self, item: QListWidgetItem) -> None:
        datos = item.data(Qt.ItemDataRole.UserRole)
        if datos is not None:
            self.resultado_activado.emit(datos)


def _contexto(resultado, radio: int = 40) -> str:
    """Fragmento legible de la línea con la coincidencia resaltada entre ⟪⟫."""
    linea = resultado.texto_linea
    ini, fin = resultado.inicio, resultado.fin
    inicio_ctx = max(0, ini - radio)
    fin_ctx = min(len(linea), fin + radio)
    prefijo = "…" if inicio_ctx > 0 else ""
    sufijo = "…" if fin_ctx < len(linea) else ""
    return (f"{prefijo}{linea[inicio_ctx:ini]}"
            f"⟪{linea[ini:fin]}⟫{linea[fin:fin_ctx]}{sufijo}")
