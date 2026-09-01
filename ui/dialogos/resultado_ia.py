# ui/dialogos/resultado_ia.py
# Muestra en streaming la sugerencia de la IA y permite aplicarla al editor.

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ai.proveedores import ProveedorIA, Mensaje
from ai.servicio import TrabajadorIA


class DialogoResultadoIA(QDialog):
    """
    Ejecuta una tarea de IA en streaming y ofrece aplicar el resultado.
    Tras cerrarse con «Reemplazar» o «Insertar debajo», expone:
      - self.accion:  "reemplazar" | "insertar" | None
      - self.texto_resultado:  el texto sugerido
    """

    def __init__(
        self,
        proveedor: ProveedorIA,
        mensajes: list[Mensaje],
        texto_original: str,
        *,
        titulo: str = "Sugerencia de la IA",
        acciones: Optional[list[tuple[str, str]]] = None,
        etiqueta_original: str = "Original",
        etiqueta_sugerencia: str = "Sugerencia",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.accion: Optional[str] = None
        self.texto_resultado: str = ""
        self._original = texto_original
        # (id, etiqueta) de los botones que aplican el resultado. Lista vacía =
        # modo solo lectura (informe); None = acciones de reescritura por defecto.
        if acciones is None:
            acciones = [("reemplazar", "Reemplazar selección"),
                        ("insertar", "Insertar debajo")]
        self._acciones = acciones
        self._etiqueta_original = etiqueta_original
        self._etiqueta_sugerencia = etiqueta_sugerencia
        self._botones_aplicar: list[QPushButton] = []

        self.setWindowTitle(titulo)
        self.resize(820, 480)
        self._construir_ui()

        self._trabajador = TrabajadorIA(proveedor, mensajes, parent=self)
        self._trabajador.token.connect(self._al_token)
        self._trabajador.terminado.connect(self._al_terminar)
        self._trabajador.error.connect(self._al_error)
        self._trabajador.start()

    # ─── UI ─────────────────────────────────────────────────────────────────────

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)

        split = QSplitter(Qt.Orientation.Horizontal)

        izq = QWidget(); lay_izq = QVBoxLayout(izq); lay_izq.setContentsMargins(0, 0, 0, 0)
        lay_izq.addWidget(QLabel(self._etiqueta_original))
        self._txt_original = QPlainTextEdit(self._original)
        self._txt_original.setReadOnly(True)
        lay_izq.addWidget(self._txt_original)
        split.addWidget(izq)

        der = QWidget(); lay_der = QVBoxLayout(der); lay_der.setContentsMargins(0, 0, 0, 0)
        lay_der.addWidget(QLabel(self._etiqueta_sugerencia))
        self._txt_sugerencia = QPlainTextEdit()
        self._txt_sugerencia.setReadOnly(True)
        lay_der.addWidget(self._txt_sugerencia)
        split.addWidget(der)

        split.setSizes([410, 410])
        layout.addWidget(split, 1)

        self._lbl_estado = QLabel("Generando…")
        self._lbl_estado.setStyleSheet("color: #8A8F98;")
        layout.addWidget(self._lbl_estado)

        fila = QHBoxLayout()
        self._btn_detener = QPushButton("Detener")
        self._btn_detener.clicked.connect(self._detener)
        fila.addWidget(self._btn_detener)
        fila.addStretch(1)

        for id_accion, etiqueta in self._acciones:
            btn = QPushButton(etiqueta)
            btn.setEnabled(False)
            btn.clicked.connect(lambda checked=False, a=id_accion: self._aplicar(a))
            fila.addWidget(btn)
            self._botones_aplicar.append(btn)

        self._btn_cerrar = QPushButton("Cerrar")
        self._btn_cerrar.clicked.connect(self.reject)
        fila.addWidget(self._btn_cerrar)

        layout.addLayout(fila)

    # ─── Señales del trabajador ──────────────────────────────────────────────────

    def _al_token(self, trozo: str) -> None:
        self._txt_sugerencia.insertPlainText(trozo)

    def _al_terminar(self, texto: str) -> None:
        self.texto_resultado = texto or self._txt_sugerencia.toPlainText()
        self._lbl_estado.setText("Listo. Revisa la sugerencia y aplícala si te convence.")
        self._btn_detener.setEnabled(False)
        habilitar = bool(self.texto_resultado.strip())
        for btn in self._botones_aplicar:
            btn.setEnabled(habilitar)

    def _al_error(self, mensaje: str) -> None:
        self._lbl_estado.setStyleSheet("color: #FF3B30;")
        self._lbl_estado.setText(f"Error: {mensaje}")
        self._btn_detener.setEnabled(False)

    # ─── Acciones ────────────────────────────────────────────────────────────────

    def _detener(self) -> None:
        self._trabajador.cancelar()
        self._lbl_estado.setText("Generación detenida.")
        self._btn_detener.setEnabled(False)
        texto = self._txt_sugerencia.toPlainText()
        self.texto_resultado = texto
        for btn in self._botones_aplicar:
            btn.setEnabled(bool(texto.strip()))

    def _aplicar(self, accion: str) -> None:
        self.accion = accion
        self.texto_resultado = self._txt_sugerencia.toPlainText()
        self.accept()

    def closeEvent(self, evento) -> None:  # type: ignore[override]
        if self._trabajador.isRunning():
            self._trabajador.cancelar()
            self._trabajador.wait(2000)
        super().closeEvent(evento)
