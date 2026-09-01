# ui/dialogos/configurar_ia.py
# Diálogo de configuración del asistente de IA (opcional, opt-in).

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.configuracion import Configuracion
from ai.proveedores import PROVEEDORES, ProveedorIA, info_proveedor
from ai.servicio import TrabajadorPrueba


class DialogoConfigurarIA(QDialog):
    """Permite habilitar la IA y elegir proveedor, modelo y credenciales."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._config = Configuracion()
        self._prueba: Optional[TrabajadorPrueba] = None
        self.setWindowTitle("Configurar asistente de IA")
        self.setMinimumWidth(520)
        self._construir_ui()
        self._cargar_valores()

    # ─── Construcción ─────────────────────────────────────────────────────────

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self._chk_habilitar = QCheckBox("Habilitar el asistente de IA")
        self._chk_habilitar.toggled.connect(self._al_cambiar_habilitado)
        layout.addWidget(self._chk_habilitar)

        aviso = QLabel(
            "La IA es opcional. Con proveedores en la nube, el texto que envíes "
            "saldrá de tu equipo hacia un tercero. Los modos locales (Ollama, "
            "LM Studio) funcionan sin conexión."
        )
        aviso.setWordWrap(True)
        aviso.setStyleSheet("color: #8A8F98;")
        layout.addWidget(aviso)

        self._form_widget = QWidget()
        form = QFormLayout(self._form_widget)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._combo_prov = QComboBox()
        import sys
        for info in PROVEEDORES.values():
            # El proveedor de Apple solo tiene sentido en macOS.
            if info.id == "apple" and sys.platform != "darwin":
                continue
            self._combo_prov.addItem(info.etiqueta, info.id)
        self._combo_prov.currentIndexChanged.connect(self._al_cambiar_proveedor)
        form.addRow("Proveedor:", self._combo_prov)

        self._edit_modelo = QLineEdit()
        self._lbl_modelo = QLabel("Modelo:")
        form.addRow(self._lbl_modelo, self._edit_modelo)

        self._edit_url = QLineEdit()
        self._edit_url.setPlaceholderText("URL base del servicio")
        self._lbl_url = QLabel("URL base:")
        form.addRow(self._lbl_url, self._edit_url)

        self._edit_clave = QLineEdit()
        self._edit_clave.setEchoMode(QLineEdit.EchoMode.Password)
        self._edit_clave.setPlaceholderText("Se guarda solo en este equipo")
        self._lbl_clave = QLabel("API key:")
        form.addRow(self._lbl_clave, self._edit_clave)

        # Fila específica del modo embebido: modelo elegido + gestor de descargas.
        self._id_embebido = ""
        self._fila_embebido = QWidget()
        hl = QHBoxLayout(self._fila_embebido)
        hl.setContentsMargins(0, 0, 0, 0)
        self._lbl_modelo_emb = QLabel("(ninguno)")
        self._btn_gestionar = QPushButton("Gestionar modelos…")
        self._btn_gestionar.clicked.connect(self._gestionar_embebidos)
        hl.addWidget(self._lbl_modelo_emb, 1)
        hl.addWidget(self._btn_gestionar)
        self._lbl_emb = QLabel("Modelo embebido:")
        form.addRow(self._lbl_emb, self._fila_embebido)

        layout.addWidget(self._form_widget)

        self._lbl_ayuda = QLabel()
        self._lbl_ayuda.setWordWrap(True)
        self._lbl_ayuda.setStyleSheet("color: #8A8F98;")
        layout.addWidget(self._lbl_ayuda)

        # Probar conexión
        fila_prueba = QWidget()
        fila_layout = QVBoxLayout(fila_prueba)
        fila_layout.setContentsMargins(0, 0, 0, 0)
        self._btn_probar = QPushButton("Probar conexión")
        self._btn_probar.clicked.connect(self._probar_conexion)
        fila_layout.addWidget(self._btn_probar)
        self._lbl_estado = QLabel("")
        self._lbl_estado.setWordWrap(True)
        fila_layout.addWidget(self._lbl_estado)
        layout.addWidget(fila_prueba)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self._guardar_y_aceptar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    # ─── Carga y estado ────────────────────────────────────────────────────────

    def _cargar_valores(self) -> None:
        self._chk_habilitar.setChecked(self._config.ia_habilitada)
        if self._config.ia_proveedor == "embebido":
            self._id_embebido = self._config.ia_modelo
        idx = self._combo_prov.findData(self._config.ia_proveedor)
        if idx >= 0:
            self._combo_prov.setCurrentIndex(idx)
        self._al_cambiar_proveedor()  # rellena url/modelo/clave según proveedor
        # Sobrescribir con lo guardado si el proveedor coincide con el activo
        if self._config.ia_proveedor != "embebido" and self._config.ia_modelo:
            self._edit_modelo.setText(self._config.ia_modelo)
        if self._config.ia_base_url:
            self._edit_url.setText(self._config.ia_base_url)
        self._al_cambiar_habilitado(self._chk_habilitar.isChecked())

    def _proveedor_actual_id(self) -> str:
        return self._combo_prov.currentData() or "openai"

    def _al_cambiar_habilitado(self, activo: bool) -> None:
        self._form_widget.setEnabled(activo)
        self._btn_probar.setEnabled(activo)

    def _al_cambiar_proveedor(self) -> None:
        info = info_proveedor(self._proveedor_actual_id())
        es_embebido = info.modo == "embebido"
        es_apple = info.protocolo == "apple"
        # Apple no necesita modelo/URL/clave (usa el modelo del sistema).
        campos_estandar = not es_embebido and not es_apple

        self._lbl_modelo.setVisible(campos_estandar)
        self._edit_modelo.setVisible(campos_estandar)
        self._lbl_url.setVisible(campos_estandar)
        self._edit_url.setVisible(campos_estandar)
        self._lbl_clave.setVisible(campos_estandar and info.requiere_clave)
        self._edit_clave.setVisible(campos_estandar and info.requiere_clave)
        self._lbl_emb.setVisible(es_embebido)
        self._fila_embebido.setVisible(es_embebido)

        if campos_estandar:
            self._edit_modelo.setText(info.modelo_defecto)
            self._edit_url.setText(info.base_url)
            self._edit_clave.setText(self._config.ia_api_key(info.id))
        elif es_embebido:
            self._actualizar_label_embebido()

        self._lbl_ayuda.setText(info.ayuda)
        self._lbl_estado.setText("")

    # ─── Modo embebido ───────────────────────────────────────────────────────────

    def _actualizar_label_embebido(self) -> None:
        from ai.modelos import modelo_por_id
        info = modelo_por_id(self._id_embebido)
        self._lbl_modelo_emb.setText(info.etiqueta if info else "(ninguno seleccionado)")

    def _gestionar_embebidos(self) -> None:
        from ui.dialogos.modelos_embebidos import DialogoModelosEmbebidos
        dlg = DialogoModelosEmbebidos(self._id_embebido, self)
        if dlg.exec() and dlg.id_seleccionado:
            self._id_embebido = dlg.id_seleccionado
        self._actualizar_label_embebido()

    # ─── Prueba de conexión ─────────────────────────────────────────────────────

    def _proveedor_desde_campos(self) -> ProveedorIA:
        info = info_proveedor(self._proveedor_actual_id())
        if info.modo == "embebido":
            return ProveedorIA(info, modelo=self._id_embebido)
        if info.protocolo == "apple":
            return ProveedorIA(info)
        return ProveedorIA(
            info,
            modelo=self._edit_modelo.text().strip(),
            api_key=self._edit_clave.text().strip() if info.requiere_clave else "",
            base_url=self._edit_url.text().strip(),
        )

    def _probar_conexion(self) -> None:
        self._btn_probar.setEnabled(False)
        self._lbl_estado.setStyleSheet("color: #8A8F98;")
        self._lbl_estado.setText("Probando…")
        self._prueba = TrabajadorPrueba(self._proveedor_desde_campos(), self)
        self._prueba.resultado.connect(self._al_resultado_prueba)
        self._prueba.start()

    def _al_resultado_prueba(self, ok: bool, mensaje: str) -> None:
        self._btn_probar.setEnabled(True)
        color = "#34C759" if ok else "#FF3B30"
        self._lbl_estado.setStyleSheet(f"color: {color};")
        self._lbl_estado.setText(("✓ " if ok else "✗ ") + mensaje)

    # ─── Guardado ────────────────────────────────────────────────────────────────

    def _guardar_y_aceptar(self) -> None:
        info = info_proveedor(self._proveedor_actual_id())
        self._config.ia_habilitada = self._chk_habilitar.isChecked()
        self._config.ia_proveedor = info.id
        self._config.ia_modo = info.modo
        if info.modo == "embebido":
            self._config.ia_modelo = self._id_embebido
            self._config.ia_base_url = ""
        elif info.protocolo == "apple":
            self._config.ia_modelo = ""
            self._config.ia_base_url = ""
        else:
            self._config.ia_modelo = self._edit_modelo.text().strip()
            self._config.ia_base_url = self._edit_url.text().strip()
            if info.requiere_clave:
                self._config.set_ia_api_key(info.id, self._edit_clave.text().strip())
        self._config.sincronizar()
        self.accept()

    def closeEvent(self, evento) -> None:  # type: ignore[override]
        if self._prueba and self._prueba.isRunning():
            self._prueba.wait(2000)
        super().closeEvent(evento)
