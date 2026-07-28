# ui/dialogos/preferencias.py
# Diálogo de configuración y preferencias de la aplicación

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.configuracion import Configuracion
from core.constantes import Tema

# Opciones de intervalo de respaldo automático (etiqueta, milisegundos)
_INTERVALOS_RESPALDO = [
    ("Desactivado",  0),
    ("5 minutos",    5  * 60_000),
    ("15 minutos",   15 * 60_000),
    ("30 minutos",   30 * 60_000),
    ("45 minutos",   45 * 60_000),
    ("1 hora",       60 * 60_000),
]


class DialogoPreferencias(QDialog):
    """
    Diálogo modal para ajustar las preferencias de la aplicación.
    Lee y escribe sobre la instancia singleton de Configuracion.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferencias")
        self.setMinimumWidth(460)
        self.setModal(True)
        self._config = Configuracion()
        self._construir_ui()
        self._cargar_valores()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # La tipografía y el tamaño del editor se ajustan desde la barra de
        # formato (y con Ctrl+rueda), por lo que ya no se configuran aquí.

        # ── Autoguardado ──────────────────────────────────────────────────────
        grupo_auto = QGroupBox("Autoguardado")
        form_auto = QFormLayout(grupo_auto)

        self._chk_autoguardado = QCheckBox("Activar autoguardado")
        form_auto.addRow(self._chk_autoguardado)

        self._spin_intervalo = QSpinBox()
        self._spin_intervalo.setRange(10, 600)
        self._spin_intervalo.setSuffix(" segundos")
        self._spin_intervalo.setSingleStep(10)
        form_auto.addRow("Intervalo:", self._spin_intervalo)

        self._chk_autoguardado.toggled.connect(self._spin_intervalo.setEnabled)
        layout.addWidget(grupo_auto)

        # ── Respaldos ─────────────────────────────────────────────────────────
        grupo_resp = QGroupBox("Respaldos")
        form_resp = QFormLayout(grupo_resp)

        self._spin_max_resp = QSpinBox()
        self._spin_max_resp.setRange(1, 50)
        self._spin_max_resp.setSuffix(" respaldos")
        form_resp.addRow("Máximo de respaldos:", self._spin_max_resp)

        # Intervalo de respaldo automático
        self._combo_intervalo_resp = QComboBox()
        for etiqueta, _ in _INTERVALOS_RESPALDO:
            self._combo_intervalo_resp.addItem(etiqueta)
        form_resp.addRow("Respaldo automático:", self._combo_intervalo_resp)

        # Ruta personalizada de respaldo
        fila_ruta = QWidget()
        hl = QHBoxLayout(fila_ruta)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(6)
        self._edit_ruta_resp = QLineEdit()
        self._edit_ruta_resp.setPlaceholderText("Dejar vacío para guardar junto al proyecto")
        self._edit_ruta_resp.setReadOnly(True)
        btn_examinar = QPushButton("Examinar…")
        btn_examinar.setFixedWidth(90)
        btn_examinar.clicked.connect(self._seleccionar_ruta_respaldo)
        btn_limpiar = QPushButton("×")
        btn_limpiar.setFixedWidth(28)
        btn_limpiar.setToolTip("Usar ruta predeterminada")
        btn_limpiar.clicked.connect(lambda: self._edit_ruta_resp.clear())
        hl.addWidget(self._edit_ruta_resp, 1)
        hl.addWidget(btn_examinar)
        hl.addWidget(btn_limpiar)
        form_resp.addRow("Carpeta de respaldos:", fila_ruta)

        layout.addWidget(grupo_resp)
        layout.addStretch(1)

        # Botones
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self._guardar_y_aceptar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _seleccionar_ruta_respaldo(self) -> None:
        ruta = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de respaldos",
            self._edit_ruta_resp.text() or str(Path.home()),
        )
        if ruta:
            self._edit_ruta_resp.setText(ruta)

    def _cargar_valores(self) -> None:
        """Precarga la UI con los valores actuales de configuración."""
        self._chk_autoguardado.setChecked(self._config.autoguardado_activo)
        self._spin_intervalo.setValue(self._config.intervalo_autoguardado // 1000)
        self._spin_intervalo.setEnabled(self._config.autoguardado_activo)

        self._spin_max_resp.setValue(self._config.max_respaldos)

        ms_actual = self._config.intervalo_respaldo_ms
        idx_resp = 0
        for i, (_, ms) in enumerate(_INTERVALOS_RESPALDO):
            if ms == ms_actual:
                idx_resp = i
                break
        self._combo_intervalo_resp.setCurrentIndex(idx_resp)

        self._edit_ruta_resp.setText(self._config.ruta_respaldos)

    def _guardar_y_aceptar(self) -> None:
        """Persiste los cambios en la configuración."""
        self._config.autoguardado_activo    = self._chk_autoguardado.isChecked()
        self._config.intervalo_autoguardado = self._spin_intervalo.value() * 1000
        self._config.max_respaldos          = self._spin_max_resp.value()
        self._config.intervalo_respaldo_ms  = _INTERVALOS_RESPALDO[
            self._combo_intervalo_resp.currentIndex()
        ][1]
        self._config.ruta_respaldos = self._edit_ruta_resp.text().strip()
        self._config.sincronizar()
        self.accept()
