# ui/dialogos/exportar.py
# Diálogo para la exportación del manuscrito

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)


class DialogoExportar(QDialog):
    """
    Diálogo para configurar y ejecutar la exportación del manuscrito
    a los formatos soportados: DOCX, PDF y TXT.
    """

    FORMATOS = {
        "Word (.docx)":        ("docx", "Documentos Word (*.docx)"),
        "PDF (.pdf)":          ("pdf",  "Archivos PDF (*.pdf)"),
        "Texto plano (.txt)":  ("txt",  "Archivos de texto (*.txt)"),
    }

    def __init__(
        self,
        nombre_proyecto: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Exportar manuscrito")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._nombre_proyecto = nombre_proyecto
        self._ruta_seleccionada: Optional[Path] = None
        self._construir_ui()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # Selección de formato
        grupo_formato = QGroupBox("Formato de exportación")
        lay_formato = QVBoxLayout(grupo_formato)
        self._radios: dict[str, QRadioButton] = {}
        for etiqueta in self.FORMATOS:
            radio = QRadioButton(etiqueta)
            lay_formato.addWidget(radio)
            self._radios[etiqueta] = radio
        self._radios["Word (.docx)"].setChecked(True)  # Por defecto
        layout.addWidget(grupo_formato)

        # Opciones adicionales
        grupo_opciones = QGroupBox("Opciones")
        lay_opciones = QVBoxLayout(grupo_opciones)
        self._chk_portada = QCheckBox("Incluir portada con título y autor")
        self._chk_portada.setChecked(True)
        lay_opciones.addWidget(self._chk_portada)
        layout.addWidget(grupo_opciones)

        # Ruta de destino
        grupo_destino = QGroupBox("Archivo de destino")
        lay_destino = QVBoxLayout(grupo_destino)
        lay_ruta = QHBoxLayout()
        self._campo_ruta = QLineEdit()
        self._campo_ruta.setReadOnly(True)
        self._campo_ruta.setPlaceholderText("Selecciona dónde guardar el archivo exportado…")
        btn_explorar = QPushButton("Guardar como…")
        btn_explorar.clicked.connect(self._explorar_destino)
        lay_ruta.addWidget(self._campo_ruta)
        lay_ruta.addWidget(btn_explorar)
        lay_destino.addLayout(lay_ruta)
        layout.addWidget(grupo_destino)

        layout.addStretch(1)

        # Botones
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        botones.button(QDialogButtonBox.StandardButton.Ok).setText("Exportar")
        botones.accepted.connect(self._validar_y_aceptar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _formato_seleccionado(self) -> tuple[str, str, str]:
        """Retorna (etiqueta, extension, filtro_dialogo)."""
        for etiqueta, (ext, filtro) in self.FORMATOS.items():
            if self._radios[etiqueta].isChecked():
                return etiqueta, ext, filtro
        # Fallback: primer formato de la lista
        primera_etiqueta = next(iter(self.FORMATOS))
        ext, filtro = self.FORMATOS[primera_etiqueta]
        return primera_etiqueta, ext, filtro

    def _explorar_destino(self) -> None:
        _, ext, filtro = self._formato_seleccionado()
        nombre_defecto = f"{self._nombre_proyecto}.{ext}"
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar como",
            str(Path.home() / nombre_defecto),
            filtro,
        )
        if ruta:
            if not ruta.endswith(f".{ext}"):
                ruta += f".{ext}"
            self._campo_ruta.setText(ruta)
            self._ruta_seleccionada = Path(ruta)

    def _validar_y_aceptar(self) -> None:
        if not self._ruta_seleccionada:
            QMessageBox.warning(
                self, "Sin destino",
                "Selecciona dónde guardar el archivo exportado."
            )
            return
        self.accept()

    # ─── Getters de configuración ─────────────────────────────────────────────

    @property
    def ruta_destino(self) -> Optional[Path]:
        return self._ruta_seleccionada

    @property
    def formato(self) -> str:
        _, ext, _ = self._formato_seleccionado()
        return ext

    @property
    def incluir_portada(self) -> bool:
        return self._chk_portada.isChecked()
