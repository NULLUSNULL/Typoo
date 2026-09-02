# ui/dialogos/modelos_embebidos.py
# Gestor de modelos de IA embebidos: descargar, eliminar y elegir.

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ai import modelos
from ai.modelos import CATALOGO, InfoModelo
from ai.servicio import TrabajadorDescarga


def _humano(n: int) -> str:
    for unidad in ("B", "KB", "MB", "GB"):
        if n < 1024 or unidad == "GB":
            return f"{n:.0f} {unidad}" if unidad == "B" else f"{n/1024:.1f} {unidad}"
        n /= 1024
    return f"{n:.1f} GB"


class _TarjetaModelo(QGroupBox):
    """Fila con el estado y las acciones de un modelo embebido."""

    def __init__(self, info: InfoModelo, dialogo: "DialogoModelosEmbebidos") -> None:
        super().__init__(info.etiqueta)
        self._info = info
        self._dialogo = dialogo
        self._trabajador: Optional[TrabajadorDescarga] = None

        lay = QVBoxLayout(self)
        desc = QLabel(f"{info.descripcion}\n{info.ram}  ·  ~{info.tamano_gb:.0f} GB en disco")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #8A8F98;")
        lay.addWidget(desc)

        self._barra = QProgressBar()
        self._barra.setVisible(False)
        lay.addWidget(self._barra)

        fila = QHBoxLayout()
        self._estado = QLabel()
        fila.addWidget(self._estado)
        fila.addStretch(1)

        self._btn_descargar = QPushButton("Descargar")
        self._btn_descargar.clicked.connect(self._descargar)
        fila.addWidget(self._btn_descargar)

        self._btn_cancelar = QPushButton("Cancelar")
        self._btn_cancelar.clicked.connect(self._cancelar)
        self._btn_cancelar.setVisible(False)
        fila.addWidget(self._btn_cancelar)

        self._btn_eliminar = QPushButton("Eliminar")
        self._btn_eliminar.clicked.connect(self._eliminar)
        fila.addWidget(self._btn_eliminar)

        self._btn_usar = QPushButton("Usar este modelo")
        self._btn_usar.clicked.connect(self._usar)
        fila.addWidget(self._btn_usar)

        lay.addLayout(fila)
        self._refrescar()

    def _refrescar(self) -> None:
        descargado = modelos.esta_descargado(self._info)
        seleccionado = self._dialogo.id_seleccionado == self._info.id
        if descargado:
            self._estado.setText("✓ Descargado" + ("  ·  en uso" if seleccionado else ""))
            self._estado.setStyleSheet("color: #34C759;")
        else:
            self._estado.setText("No descargado")
            self._estado.setStyleSheet("color: #8A8F98;")
        self._btn_descargar.setVisible(not descargado)
        self._btn_eliminar.setVisible(descargado)
        self._btn_usar.setEnabled(descargado)

    # -- Descarga -----------------------------------------------------------
    def _descargar(self) -> None:
        if not self._dialogo.puede_descargar():
            return
        self._dialogo.set_descarga_activa(True)
        self._barra.setRange(0, 100)
        self._barra.setValue(0)
        self._barra.setVisible(True)
        self._btn_descargar.setVisible(False)
        self._btn_cancelar.setVisible(True)
        self._estado.setText("Descargando…")
        self._estado.setStyleSheet("color: #8A8F98;")
        self._trabajador = TrabajadorDescarga(self._info, self)
        self._trabajador.progreso.connect(self._al_progreso)
        self._trabajador.terminado.connect(self._al_terminar)
        self._trabajador.cancelado.connect(self._al_cancelado)
        self._trabajador.error.connect(self._al_error)
        self._trabajador.start()

    def _al_progreso(self, leido: int, total: int) -> None:
        if total > 0:
            self._barra.setValue(int(leido * 100 / total))
            self._estado.setText(f"Descargando… {_humano(leido)} / {_humano(total)}")
        else:
            self._barra.setRange(0, 0)  # indeterminada
            self._estado.setText(f"Descargando… {_humano(leido)}")

    def _al_terminar(self) -> None:
        self._fin_descarga()
        self._refrescar()

    def _al_cancelado(self) -> None:
        self._fin_descarga()
        self._estado.setText("Descarga cancelada.")
        self._refrescar()

    def _al_error(self, mensaje: str) -> None:
        self._fin_descarga()
        self._estado.setText(f"Error: {mensaje}")
        self._estado.setStyleSheet("color: #FF3B30;")

    def _fin_descarga(self) -> None:
        self._barra.setVisible(False)
        self._btn_cancelar.setVisible(False)
        self._dialogo.set_descarga_activa(False)

    def _cancelar(self) -> None:
        if self._trabajador and self._trabajador.isRunning():
            self._trabajador.cancelar()

    def _eliminar(self) -> None:
        if modelos.eliminar(self._info):
            if self._dialogo.id_seleccionado == self._info.id:
                self._dialogo.id_seleccionado = ""
            self._refrescar()

    def _usar(self) -> None:
        self._dialogo.id_seleccionado = self._info.id
        self._dialogo.accept()

    def descarga_en_curso(self) -> bool:
        return self._trabajador is not None and self._trabajador.isRunning()


class DialogoModelosEmbebidos(QDialog):
    """Descarga y selección de un modelo embebido. Expone `id_seleccionado`."""

    def __init__(self, id_actual: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.id_seleccionado = id_actual
        self._descarga_activa = False
        self.setWindowTitle("Modelos embebidos")
        self.setMinimumWidth(560)
        self._construir_ui()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)

        intro = QLabel(
            "Modelos que se ejecutan en tu equipo, sin conexión ni coste. "
            "Elige según la potencia de tu ordenador."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self._tarjetas = []
        for info in CATALOGO:
            tarjeta = _TarjetaModelo(info, self)
            self._tarjetas.append(tarjeta)
            layout.addWidget(tarjeta)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botones.rejected.connect(self.reject)
        botones.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.reject)
        layout.addWidget(botones)

    # -- Coordinación de descargas (solo una a la vez) ----------------------
    def puede_descargar(self) -> bool:
        return not self._descarga_activa

    def set_descarga_activa(self, activa: bool) -> None:
        self._descarga_activa = activa
        for t in self._tarjetas:
            # Deshabilitar «Descargar» del resto mientras una descarga está activa.
            if not t.descarga_en_curso():
                t._btn_descargar.setEnabled(not activa)

    def closeEvent(self, evento) -> None:  # type: ignore[override]
        for t in self._tarjetas:
            if t.descarga_en_curso():
                t._cancelar()
                t._trabajador.wait(2000)
        super().closeEvent(evento)
