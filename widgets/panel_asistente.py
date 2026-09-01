# widgets/panel_asistente.py
# Panel de chat con la IA usando el manuscrito como contexto (RAG ligero).

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.configuracion import Configuracion


def _escapar(texto: str) -> str:
    return (texto.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace("\n", "<br>"))


class PanelAsistente(QWidget):
    """Chat lateral que responde preguntas sobre el proyecto con contexto."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._config = Configuracion()
        self._gestor = None
        self._historial: list[dict[str, str]] = []   # turnos para el modelo
        self._mensajes_ui: list[dict[str, str]] = []  # burbujas mostradas
        self._trabajador = None
        self._pregunta_pendiente = ""
        self._construir_ui()
        self._nota_inicial()

    def establecer_gestor(self, gestor) -> None:
        self._gestor = gestor

    def poner_foco(self) -> None:
        self._entrada.setFocus()

    # ─── UI ──────────────────────────────────────────────────────────────────
    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self._vista = QTextEdit()
        self._vista.setReadOnly(True)
        layout.addWidget(self._vista, 1)

        # La barra de entrada va ENCIMA de los botones.
        self._entrada = QLineEdit()
        self._entrada.setPlaceholderText("Pregunta sobre tu manuscrito…")
        self._entrada.returnPressed.connect(self._enviar)
        layout.addWidget(self._entrada)

        fila = QHBoxLayout()
        self._btn_enviar = QPushButton("Enviar")
        self._btn_enviar.clicked.connect(self._enviar)
        fila.addWidget(self._btn_enviar)
        self._btn_detener = QPushButton("Detener")
        self._btn_detener.setEnabled(False)
        self._btn_detener.clicked.connect(self._detener)
        fila.addWidget(self._btn_detener)
        fila.addStretch(1)
        self._btn_limpiar = QPushButton("Limpiar")
        self._btn_limpiar.clicked.connect(self._limpiar)
        fila.addWidget(self._btn_limpiar)
        layout.addLayout(fila)

    def _nota_inicial(self) -> None:
        self._mensajes_ui = [{
            "tipo": "nota",
            "texto": "Escribe una pregunta y pulsa Enviar. Uso el manuscrito y el "
                     "dossier como contexto (por ejemplo: «resume el arco de …» o "
                     "«¿dónde aparece …?»).",
        }]
        self._render()

    # ─── Render ──────────────────────────────────────────────────────────────
    def _render(self) -> None:
        partes: list[str] = []
        for m in self._mensajes_ui:
            tipo, texto = m["tipo"], _escapar(m["texto"])
            if tipo == "tu":
                partes.append(f'<p style="margin:8px 0 2px 0;"><b>Tú:</b> {texto}</p>')
            elif tipo == "ia":
                partes.append(
                    f'<p style="margin:2px 0 8px 0;"><b>Asistente:</b> {texto}</p>')
            elif tipo == "fuentes":
                partes.append(
                    f'<p style="margin:0 0 4px 0; color:#8A8F98;">'
                    f'<i>Fuentes: {texto}</i></p>')
            elif tipo == "error":
                partes.append(f'<p style="color:#FF3B30;">[Error: {texto}]</p>')
            else:  # nota
                partes.append(f'<p style="color:#8A8F98;"><i>{texto}</i></p>')
        self._vista.setHtml("".join(partes))
        barra = self._vista.verticalScrollBar()
        barra.setValue(barra.maximum())

    def _añadir(self, tipo: str, texto: str) -> int:
        self._mensajes_ui.append({"tipo": tipo, "texto": texto})
        self._render()
        return len(self._mensajes_ui) - 1

    # ─── Envío ─────────────────────────────────────────────────────────────────
    def _enviar(self) -> None:
        pregunta = self._entrada.text().strip()
        if not pregunta:
            return
        if not self._config.ia_habilitada:
            self._añadir("nota", "El asistente de IA no está habilitado "
                                 "(IA → Configurar asistente…).")
            return
        if self._trabajador is not None and self._trabajador.isRunning():
            return
        self._entrada.clear()
        self._añadir("tu", pregunta)

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
            self._añadir("fuentes", ", ".join(fuentes))

        from ai.proveedores import crear_proveedor_desde_config
        from ai.servicio import TrabajadorIA
        from ai.tareas import mensajes_chat

        proveedor = crear_proveedor_desde_config(self._config)
        mensajes = mensajes_chat(pregunta, contexto, self._historial[-6:])
        self._pregunta_pendiente = pregunta
        self._indice_respuesta = self._añadir("ia", "…")
        self._respuesta = []

        self._trabajador = TrabajadorIA(proveedor, mensajes, parent=self)
        self._trabajador.token.connect(self._al_token)
        self._trabajador.terminado.connect(self._al_terminar)
        self._trabajador.error.connect(self._al_error)
        self._ocupado(True)
        self._trabajador.start()

    def _al_token(self, trozo: str) -> None:
        self._respuesta.append(trozo)
        self._mensajes_ui[self._indice_respuesta]["texto"] = "".join(self._respuesta)
        self._render()

    def _al_terminar(self, texto: str) -> None:
        final = texto or "".join(self._respuesta)
        self._mensajes_ui[self._indice_respuesta]["texto"] = final or "(sin respuesta)"
        self._render()
        self._historial.append({"role": "user", "content": self._pregunta_pendiente})
        self._historial.append({"role": "assistant", "content": final})
        self._ocupado(False)

    def _al_error(self, mensaje: str) -> None:
        self._mensajes_ui[self._indice_respuesta]["tipo"] = "error"
        self._mensajes_ui[self._indice_respuesta]["texto"] = mensaje
        self._render()
        self._ocupado(False)

    def _detener(self) -> None:
        if self._trabajador is not None and self._trabajador.isRunning():
            self._trabajador.cancelar()
        self._ocupado(False)

    def _limpiar(self) -> None:
        self._historial.clear()
        self._mensajes_ui.clear()
        self._nota_inicial()

    def _ocupado(self, activo: bool) -> None:
        self._btn_enviar.setEnabled(not activo)
        self._entrada.setEnabled(not activo)
        self._btn_detener.setEnabled(activo)
