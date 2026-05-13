# ui/dialogos/nuevo_proyecto.py
# Diálogo para la creación de un nuevo proyecto literario

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DialogoNuevoProyecto(QDialog):
    """
    Diálogo modal para configurar un nuevo proyecto literario.
    Solicita: nombre del proyecto, nombre del autor y directorio de destino.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nuevo proyecto")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._construir_ui()

    def _construir_ui(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(16)

        # Título
        titulo = QLabel("Crear nuevo proyecto literario")
        fuente = titulo.font()
        fuente.setPointSize(13)
        fuente.setBold(True)
        titulo.setFont(fuente)
        layout_principal.addWidget(titulo)

        # Formulario
        formulario = QFormLayout()
        formulario.setSpacing(10)

        self._campo_nombre = QLineEdit()
        self._campo_nombre.setPlaceholderText("Ej: Mi gran novela")
        formulario.addRow("Nombre del proyecto *:", self._campo_nombre)

        self._campo_autor = QLineEdit()
        self._campo_autor.setPlaceholderText("Ej: Juan García")
        formulario.addRow("Autor:", self._campo_autor)

        # Directorio de destino
        layout_ruta = QHBoxLayout()
        self._campo_ruta = QLineEdit()
        self._campo_ruta.setPlaceholderText("Selecciona el directorio donde se guardará...")
        self._campo_ruta.setReadOnly(True)
        btn_explorar = QPushButton("Explorar…")
        btn_explorar.setFixedWidth(90)
        btn_explorar.clicked.connect(self._explorar_directorio)
        layout_ruta.addWidget(self._campo_ruta)
        layout_ruta.addWidget(btn_explorar)
        formulario.addRow("Directorio *:", layout_ruta)

        layout_principal.addLayout(formulario)

        # Aviso
        aviso = QLabel(
            "Se creará una carpeta con el nombre del proyecto dentro del directorio seleccionado."
        )
        aviso.setWordWrap(True)
        aviso.setStyleSheet("color: gray; font-size: 11px;")
        layout_principal.addWidget(aviso)

        layout_principal.addStretch(1)

        # Botones Aceptar / Cancelar
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        botones.button(QDialogButtonBox.StandardButton.Ok).setText("Crear proyecto")
        botones.accepted.connect(self._validar_y_aceptar)
        botones.rejected.connect(self.reject)
        layout_principal.addWidget(botones)

    def _explorar_directorio(self) -> None:
        directorio = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar directorio de destino",
            str(Path.home()),
        )
        if directorio:
            self._campo_ruta.setText(directorio)

    def _validar_y_aceptar(self) -> None:
        nombre = self._campo_nombre.text().strip()
        ruta   = self._campo_ruta.text().strip()

        if not nombre:
            QMessageBox.warning(self, "Campo requerido", "El nombre del proyecto es obligatorio.")
            self._campo_nombre.setFocus()
            return

        if not ruta:
            QMessageBox.warning(self, "Campo requerido", "Debes seleccionar un directorio de destino.")
            return

        ruta_proyecto = Path(ruta) / nombre
        if ruta_proyecto.exists():
            resp = QMessageBox.question(
                self,
                "Directorio existente",
                f"Ya existe una carpeta «{nombre}» en ese directorio.\n¿Deseas continuar de todas formas?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if resp == QMessageBox.StandardButton.No:
                return

        self.accept()

    # ─── Getters de resultados ────────────────────────────────────────────────

    @property
    def nombre_proyecto(self) -> str:
        return self._campo_nombre.text().strip()

    @property
    def nombre_autor(self) -> str:
        return self._campo_autor.text().strip()

    @property
    def ruta_destino(self) -> Path:
        return Path(self._campo_ruta.text().strip()) / self.nombre_proyecto
