# ui/dialogos/tormenta_ia.py
# Tormenta de ideas guiada: la IA propone 3 caminos distintos, el autor elige
# uno (obligatorio) y la IA lo desarrolla para ayudarle a seguir escribiendo.

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ai.proveedores import ProveedorIA
from ai.servicio import TrabajadorIA
from ai.tareas import (
    mensajes_desarrollar_camino,
    mensajes_tres_caminos,
    parsear_opciones,
)


class DialogoTormenta(QDialog):
    """
    Paso 1: genera 3 caminos y obliga a elegir uno.
    Paso 2: desarrolla el elegido en streaming.
    Al aceptar con «Insertar», expone:
      - self.accion == "insertar"
      - self.texto_resultado (el desarrollo a pegar en el editor)
    """

    def __init__(self, proveedor: ProveedorIA, contexto: str, foco: str = "",
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.accion: Optional[str] = None
        self.texto_resultado: str = ""
        self._proveedor = proveedor
        self._contexto = contexto
        self._foco = foco
        self._opciones: list[tuple[str, str]] = []
        self._buffer: list[str] = []
        self._trabajador: Optional[TrabajadorIA] = None

        self.setWindowTitle("Tormenta de ideas: ¿cómo continuar?")
        self.resize(720, 520)
        self._construir_ui()
        self._generar_opciones()

    # ─── UI ──────────────────────────────────────────────────────────────────
    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._estado = QLabel()
        self._estado.setWordWrap(True)
        self._estado.setStyleSheet("color: #8A8F98;")
        layout.addWidget(self._estado)

        # Paso 1: opciones (radios)
        self._area_opciones = QWidget()
        self._lay_opciones = QVBoxLayout(self._area_opciones)
        self._lay_opciones.setContentsMargins(0, 0, 0, 0)
        self._grupo = QButtonGroup(self)
        self._grupo.buttonToggled.connect(self._al_elegir)
        layout.addWidget(self._area_opciones)

        # Paso 2: desarrollo del camino elegido
        self._vista = QTextEdit()
        self._vista.setReadOnly(True)
        self._vista.hide()
        layout.addWidget(self._vista, 1)

        layout.addStretch(0)
        fila = QHBoxLayout()
        self._btn_detener = QPushButton("Detener")
        self._btn_detener.clicked.connect(self._detener)
        fila.addWidget(self._btn_detener)
        self._btn_regenerar = QPushButton("Otras 3 ideas")
        self._btn_regenerar.setEnabled(False)
        self._btn_regenerar.clicked.connect(self._generar_opciones)
        fila.addWidget(self._btn_regenerar)
        fila.addStretch(1)
        self._btn_volver = QPushButton("← Ver opciones")
        self._btn_volver.hide()
        self._btn_volver.clicked.connect(self._volver_a_opciones)
        fila.addWidget(self._btn_volver)
        self._btn_explorar = QPushButton("Explorar esta idea →")
        self._btn_explorar.setEnabled(False)
        self._btn_explorar.clicked.connect(self._explorar)
        fila.addWidget(self._btn_explorar)
        self._btn_insertar = QPushButton("Insertar en el editor")
        self._btn_insertar.hide()
        self._btn_insertar.clicked.connect(self._insertar)
        fila.addWidget(self._btn_insertar)
        self._btn_cerrar = QPushButton("Cerrar")
        self._btn_cerrar.clicked.connect(self.reject)
        fila.addWidget(self._btn_cerrar)
        layout.addLayout(fila)

    # ─── Paso 1: generar los 3 caminos ─────────────────────────────────────────
    def _generar_opciones(self) -> None:
        self._limpiar_opciones()
        self._vista.hide()
        self._area_opciones.show()
        self._btn_volver.hide()
        self._btn_insertar.hide()
        self._btn_explorar.show()
        self._btn_explorar.setEnabled(False)
        self._btn_regenerar.setEnabled(False)
        self._estado.setText("Generando 3 caminos posibles…")
        self._buffer = []
        mensajes = mensajes_tres_caminos(self._contexto, self._foco)
        self._lanzar(mensajes, self._al_terminar_opciones)

    def _limpiar_opciones(self) -> None:
        for b in list(self._grupo.buttons()):
            self._grupo.removeButton(b)
            b.setParent(None)
            b.deleteLater()
        while self._lay_opciones.count():
            it = self._lay_opciones.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

    def _al_terminar_opciones(self, texto: str) -> None:
        self._opciones = parsear_opciones(texto)
        if not self._opciones:
            self._estado.setText("No pude generar opciones claras. Pulsa «Otras 3 ideas».")
            self._btn_regenerar.setEnabled(True)
            return
        self._estado.setText("Elige un camino y pulsa «Explorar esta idea».")
        for i, (titulo, desc) in enumerate(self._opciones):
            etiqueta = f"<b>{_esc(titulo)}</b>" + (f" — {_esc(desc)}" if desc else "")
            radio = QRadioButton()
            radio.setStyleSheet("padding: 6px 0;")
            lbl = QLabel(etiqueta)
            lbl.setWordWrap(True)
            fila = QWidget()
            hl = QHBoxLayout(fila)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.addWidget(radio)
            hl.addWidget(lbl, 1)
            lbl.mousePressEvent = lambda _e, r=radio: r.setChecked(True)  # clic en el texto
            self._grupo.addButton(radio, i)
            self._lay_opciones.addWidget(fila)
        self._btn_regenerar.setEnabled(True)

    def _al_elegir(self, *_a) -> None:
        self._btn_explorar.setEnabled(self._grupo.checkedId() >= 0)

    # ─── Paso 2: desarrollar el camino elegido ─────────────────────────────────
    def _explorar(self) -> None:
        idx = self._grupo.checkedId()
        if idx < 0 or idx >= len(self._opciones):
            return
        titulo, desc = self._opciones[idx]
        self._area_opciones.hide()
        self._btn_explorar.hide()
        self._btn_regenerar.setEnabled(False)
        self._vista.clear()
        self._vista.show()
        self._btn_volver.show()
        self._estado.setText(f"Desarrollando: «{titulo}»…")
        self._buffer = []
        mensajes = mensajes_desarrollar_camino(self._contexto, titulo, desc, self._foco)
        self._lanzar(mensajes, self._al_terminar_desarrollo)

    def _al_terminar_desarrollo(self, texto: str) -> None:
        self.texto_resultado = (texto or "".join(self._buffer)).strip()
        self._estado.setText("Puedes insertarlo en el editor para seguir escribiendo.")
        self._btn_insertar.show()
        self._btn_insertar.setEnabled(bool(self.texto_resultado))

    def _volver_a_opciones(self) -> None:
        if self._trabajador and self._trabajador.isRunning():
            self._trabajador.cancelar()
        self._vista.hide()
        self._btn_volver.hide()
        self._btn_insertar.hide()
        self._area_opciones.show()
        self._btn_explorar.show()
        self._btn_explorar.setEnabled(self._grupo.checkedId() >= 0)
        self._btn_regenerar.setEnabled(True)
        self._estado.setText("Elige un camino y pulsa «Explorar esta idea».")

    def _insertar(self) -> None:
        self.accion = "insertar"
        if not self.texto_resultado:
            self.texto_resultado = self._vista.toPlainText().strip()
        self.accept()

    # ─── Motor común ────────────────────────────────────────────────────────────
    def _lanzar(self, mensajes, al_terminar) -> None:
        self._btn_detener.setEnabled(True)
        self._trabajador = TrabajadorIA(self._proveedor, mensajes, parent=self)
        self._trabajador.token.connect(self._al_token)
        self._trabajador.terminado.connect(al_terminar)
        self._trabajador.terminado.connect(lambda *_: self._btn_detener.setEnabled(False))
        self._trabajador.error.connect(self._al_error)
        self._trabajador.start()

    def _al_token(self, trozo: str) -> None:
        self._buffer.append(trozo)
        if self._vista.isVisible():
            self._vista.moveCursor(self._vista.textCursor().MoveOperation.End)
            self._vista.insertPlainText(trozo)

    def _al_error(self, mensaje: str) -> None:
        self._estado.setStyleSheet("color: #FF3B30;")
        self._estado.setText(f"Error: {mensaje}")
        self._btn_detener.setEnabled(False)

    def _detener(self) -> None:
        if self._trabajador and self._trabajador.isRunning():
            self._trabajador.cancelar()
        self._btn_detener.setEnabled(False)

    def closeEvent(self, evento) -> None:  # type: ignore[override]
        if self._trabajador and self._trabajador.isRunning():
            self._trabajador.cancelar()
            self._trabajador.wait(2000)
        super().closeEvent(evento)


def _esc(texto: str) -> str:
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
