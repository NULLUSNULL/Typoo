# widgets/panel_asistente.py
# Panel de chat con la IA usando el manuscrito como contexto (RAG ligero).

from __future__ import annotations

from typing import Optional

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.configuracion import Configuracion


class PanelAsistente(QWidget):
    """Chat lateral que responde preguntas sobre el proyecto con contexto."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._config = Configuracion()
        self._gestor = None
        self._historial: list[dict[str, str]] = []
        self._trabajador = None
        self._pregunta_pendiente = ""
        self._construir_ui()

    def establecer_gestor(self, gestor) -> None:
        self._gestor = gestor

    def poner_foco(self) -> None:
        self._entrada.setFocus()

    # ─── UI ──────────────────────────────────────────────────────────────────
    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        self._vista = QTextEdit()
        self._vista.setReadOnly(True)
        layout.addWidget(self._vista, 1)

        fila = QHBoxLayout()
        self._entrada = QLineEdit()
        self._entrada.setPlaceholderText("Pregunta sobre tu manuscrito…")
        self._entrada.returnPressed.connect(self._enviar)
        fila.addWidget(self._entrada, 1)
        self._btn_enviar = QPushButton("Enviar")
        self._btn_enviar.clicked.connect(self._enviar)
        fila.addWidget(self._btn_enviar)
        self._btn_detener = QPushButton("Detener")
        self._btn_detener.setEnabled(False)
        self._btn_detener.clicked.connect(self._detener)
        fila.addWidget(self._btn_detener)
        layout.addLayout(fila)

        fila2 = QHBoxLayout()
        fila2.addStretch(1)
        self._btn_limpiar = QPushButton("Limpiar conversación")
        self._btn_limpiar.clicked.connect(self._limpiar)
        fila2.addWidget(self._btn_limpiar)
        layout.addLayout(fila2)

        self._nota(
            "Escribe una pregunta y pulsa Enviar. Uso el manuscrito y el dossier "
            "como contexto (por ejemplo: «resume el arco de …» o «¿dónde aparece …?»)."
        )

    # ─── Utilidades de render ──────────────────────────────────────────────────
    def _fin(self) -> None:
        self._vista.moveCursor(QTextCursor.MoveOperation.End)

    def _html(self, html: str) -> None:
        self._fin()
        self._vista.insertHtml(html)
        self._fin()

    def _texto(self, texto: str) -> None:
        self._fin()
        self._vista.insertPlainText(texto)
        self._fin()

    def _nota(self, texto: str) -> None:
        self._html(f'<p style="color:#8A8F98;"><i>{texto}</i></p>')

    # ─── Envío ─────────────────────────────────────────────────────────────────
    def _enviar(self) -> None:
        pregunta = self._entrada.text().strip()
        if not pregunta:
            return
        if not self._config.ia_habilitada:
            self._nota("El asistente de IA no está habilitado (IA → Configurar asistente…).")
            return
        if self._trabajador is not None and self._trabajador.isRunning():
            return
        self._entrada.clear()
        self._html(f'<p><b>Tú:</b> {_escapar(pregunta)}</p>')

        contexto = ""
        fuentes: list[str] = []
        if self._gestor is not None and self._gestor.hay_proyecto:
            from ai.recuperacion import construir_corpus, recuperar, formatear_contexto
            corpus = construir_corpus(
                self._gestor.proyecto_activo, self._gestor.leer_documento)
            fragmentos = recuperar(corpus, pregunta)
            contexto = formatear_contexto(fragmentos)
            fuentes = [f.titulo for f in fragmentos]
        if fuentes:
            self._html(
                f'<p style="color:#8A8F98;"><i>Fuentes: {_escapar(", ".join(fuentes))}</i></p>')

        from ai.proveedores import crear_proveedor_desde_config
        from ai.servicio import TrabajadorIA
        from ai.tareas import mensajes_chat

        proveedor = crear_proveedor_desde_config(self._config)
        mensajes = mensajes_chat(pregunta, contexto, self._historial[-6:])
        self._pregunta_pendiente = pregunta

        self._html('<p><b>Asistente:</b> </p>')
        self._trabajador = TrabajadorIA(proveedor, mensajes, parent=self)
        self._trabajador.token.connect(self._texto)
        self._trabajador.terminado.connect(self._al_terminar)
        self._trabajador.error.connect(self._al_error)
        self._ocupado(True)
        self._trabajador.start()

    def _al_terminar(self, texto: str) -> None:
        self._historial.append({"role": "user", "content": self._pregunta_pendiente})
        self._historial.append({"role": "assistant", "content": texto})
        self._texto("\n")
        self._ocupado(False)

    def _al_error(self, mensaje: str) -> None:
        self._html(f'<p style="color:#FF3B30;">[Error: {_escapar(mensaje)}]</p>')
        self._ocupado(False)

    def _detener(self) -> None:
        if self._trabajador is not None and self._trabajador.isRunning():
            self._trabajador.cancelar()
        self._ocupado(False)

    def _limpiar(self) -> None:
        self._historial.clear()
        self._vista.clear()
        self._nota("Conversación reiniciada.")

    def _ocupado(self, activo: bool) -> None:
        self._btn_enviar.setEnabled(not activo)
        self._entrada.setEnabled(not activo)
        self._btn_detener.setEnabled(activo)


def _escapar(texto: str) -> str:
    return (texto.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace("\n", "<br>"))
