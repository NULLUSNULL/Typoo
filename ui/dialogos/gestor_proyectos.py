# ui/dialogos/gestor_proyectos.py
# Gestor de proyectos: se muestra al abrir el programa y desde el menú.
# Lista todos los proyectos que conoce la aplicación y permite abrirlos,
# crear uno nuevo, añadir uno existente o eliminarlo (con confirmación
# escribiendo su nombre).

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.constantes import NOMBRE_APP, NOMBRE_ARCHIVO_PROYECTO
from ui.dialogos.nuevo_proyecto import DialogoNuevoProyecto


def _nombre_de_proyecto(ruta: Path) -> Optional[str]:
    """Lee el nombre del proyecto desde su proyecto.json; None si no es válido."""
    archivo = ruta / NOMBRE_ARCHIVO_PROYECTO
    if not archivo.exists():
        return None
    try:
        datos = json.loads(archivo.read_text(encoding="utf-8"))
        nombre = datos.get("nombre") or datos.get("proyecto", {}).get("nombre")
        return nombre or ruta.name
    except Exception:
        return ruta.name


class DialogoGestorProyectos(QDialog):
    """
    Gestor visual de proyectos.

    Tras cerrarse con «Abrir» o «Nuevo», expone:
      - self.proyecto: el `Proyecto` cargado/creado (o None si se canceló).
    Y en `self.rutas_eliminadas` las rutas de proyectos borrados del disco.
    """

    def __init__(self, gestor, config, parent: Optional[QWidget] = None,
                 al_inicio: bool = False) -> None:
        super().__init__(parent)
        self._gestor = gestor
        self._config = config
        self._al_inicio = al_inicio
        self.proyecto = None
        self.rutas_eliminadas: list[str] = []

        self.setWindowTitle(f"Proyectos — {NOMBRE_APP}")
        self.setMinimumSize(560, 440)
        self.setModal(True)
        self._construir_ui()
        self._recargar_lista()

    # ─── UI ───────────────────────────────────────────────────────────────────
    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        titulo = QLabel("Tus proyectos")
        f = titulo.font(); f.setPointSize(16); f.setBold(True); titulo.setFont(f)
        layout.addWidget(titulo)

        sub = QLabel("Abre un proyecto reciente, crea uno nuevo o añade una "
                     "carpeta existente.")
        sub.setWordWrap(True)
        sub.setStyleSheet("color: #8A8F98;")
        layout.addWidget(sub)

        self._lista = QListWidget()
        self._lista.setObjectName("ListaProyectos")
        self._lista.setAlternatingRowColors(False)
        self._lista.itemDoubleClicked.connect(lambda *_: self._abrir_seleccionado())
        self._lista.itemSelectionChanged.connect(self._actualizar_botones)
        self._lista.setStyleSheet(
            "#ListaProyectos { border: 1px solid rgba(128,128,128,0.25);"
            " border-radius: 10px; padding: 4px; }"
            "#ListaProyectos::item { padding: 8px 10px; border-radius: 7px; }"
            "#ListaProyectos::item:selected,"
            "#ListaProyectos::item:selected:!active {"
            " background: #2F6FE0; color: #FFFFFF; }"
        )
        layout.addWidget(self._lista, 1)

        self._lbl_vacio = QLabel("Aún no hay proyectos. Crea uno nuevo para empezar.")
        self._lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_vacio.setStyleSheet("color: #8A8F98; padding: 12px;")
        layout.addWidget(self._lbl_vacio)

        fila = QHBoxLayout()
        self._btn_nuevo = QPushButton("Nuevo proyecto…")
        self._btn_nuevo.clicked.connect(self._nuevo_proyecto)
        fila.addWidget(self._btn_nuevo)

        self._btn_anadir = QPushButton("Añadir existente…")
        self._btn_anadir.clicked.connect(self._anadir_existente)
        fila.addWidget(self._btn_anadir)

        self._btn_eliminar = QPushButton("Eliminar…")
        self._btn_eliminar.setObjectName("BotonPeligro")
        self._btn_eliminar.clicked.connect(self._eliminar_seleccionado)
        fila.addWidget(self._btn_eliminar)

        fila.addStretch(1)

        if not self._al_inicio:
            self._btn_cerrar = QPushButton("Cancelar")
            self._btn_cerrar.clicked.connect(self.reject)
            fila.addWidget(self._btn_cerrar)

        self._btn_abrir = QPushButton("Abrir")
        self._btn_abrir.setDefault(True)
        self._btn_abrir.clicked.connect(self._abrir_seleccionado)
        fila.addWidget(self._btn_abrir)

        layout.addLayout(fila)
        self._actualizar_botones()

    # ─── Datos ──────────────────────────────────────────────────────────────
    def _recargar_lista(self) -> None:
        self._lista.clear()
        rutas = self._config.proyectos_recientes()
        validos = 0
        for ruta_txt in rutas:
            ruta = Path(ruta_txt)
            nombre = _nombre_de_proyecto(ruta)
            existe = nombre is not None
            etiqueta = nombre or ruta.name
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, ruta_txt)
            if existe:
                item.setText(f"{etiqueta}\n{ruta_txt}")
                validos += 1
            else:
                item.setText(f"{etiqueta}  (no encontrado)\n{ruta_txt}")
                item.setForeground(Qt.GlobalColor.gray)
            self._lista.addItem(item)
        hay = self._lista.count() > 0
        self._lbl_vacio.setVisible(not hay)
        self._lista.setVisible(hay)
        if hay:
            self._lista.setCurrentRow(0)
        self._actualizar_botones()

    def _ruta_seleccionada(self) -> Optional[str]:
        if self._lista.count() == 0:
            return None
        item = self._lista.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _actualizar_botones(self) -> None:
        ruta = self._ruta_seleccionada()
        valido = bool(ruta) and _nombre_de_proyecto(Path(ruta)) is not None
        self._btn_abrir.setEnabled(valido)
        self._btn_eliminar.setEnabled(bool(ruta))

    # ─── Acciones ─────────────────────────────────────────────────────────────
    def _abrir_seleccionado(self) -> None:
        ruta = self._ruta_seleccionada()
        if not ruta:
            return
        if _nombre_de_proyecto(Path(ruta)) is None:
            QMessageBox.warning(
                self, "Proyecto no encontrado",
                f"No se encontró un proyecto Typoo válido en:\n{ruta}\n\n"
                "Puedes eliminarlo de la lista.")
            return
        try:
            self.proyecto = self._gestor.abrir_proyecto(Path(ruta))
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Error al abrir proyecto", str(e))
            return
        self._config.agregar_proyecto_reciente(ruta)
        self._config.ultimo_proyecto = ruta
        self.accept()

    def _nuevo_proyecto(self) -> None:
        dialogo = DialogoNuevoProyecto(self)
        if not dialogo.exec():
            return
        try:
            self.proyecto = self._gestor.nuevo_proyecto(
                nombre=dialogo.nombre_proyecto,
                ruta=dialogo.ruta_destino,
                autor=dialogo.nombre_autor,
            )
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Error al crear proyecto", str(e))
            return
        ruta = str(self.proyecto.ruta)
        self._config.agregar_proyecto_reciente(ruta)
        self._config.ultimo_proyecto = ruta
        self.accept()

    def _anadir_existente(self) -> None:
        ruta = QFileDialog.getExistingDirectory(
            self, "Añadir proyecto existente", str(Path.home()))
        if not ruta:
            return
        if _nombre_de_proyecto(Path(ruta)) is None:
            QMessageBox.warning(
                self, "Carpeta no válida",
                f"La carpeta no contiene un proyecto Typoo válido:\n{ruta}")
            return
        self._config.agregar_proyecto_reciente(ruta)
        self._recargar_lista()

    def _eliminar_seleccionado(self) -> None:
        ruta = self._ruta_seleccionada()
        if not ruta:
            return
        ruta_path = Path(ruta)
        nombre = _nombre_de_proyecto(ruta_path) or ruta_path.name

        # Si el proyecto ya no existe en disco, solo lo quitamos de la lista.
        if _nombre_de_proyecto(ruta_path) is None:
            self._config.eliminar_proyecto_reciente(ruta)
            self._recargar_lista()
            return

        confirmado = self._confirmar_eliminacion(nombre)
        if not confirmado:
            return
        try:
            shutil.rmtree(ruta_path)
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "No se pudo eliminar", str(e))
            return
        self._config.eliminar_proyecto_reciente(ruta)
        self.rutas_eliminadas.append(ruta)
        self._recargar_lista()

    def _confirmar_eliminacion(self, nombre: str) -> bool:
        dlg = QDialog(self)
        dlg.setWindowTitle("Eliminar proyecto")
        dlg.setModal(True)
        dlg.setMinimumWidth(440)
        lay = QVBoxLayout(dlg)
        lay.setSpacing(12)

        aviso = QLabel(
            f"Vas a <b>eliminar permanentemente</b> el proyecto "
            f"«{nombre}» y todos sus archivos del disco. "
            "Esta acción no se puede deshacer.")
        aviso.setWordWrap(True)
        lay.addWidget(aviso)

        instr = QLabel(f"Para confirmar, escribe el nombre del proyecto: "
                       f"<b>{nombre}</b>")
        instr.setWordWrap(True)
        lay.addWidget(instr)

        campo = QLineEdit()
        campo.setPlaceholderText(nombre)
        lay.addWidget(campo)

        fila = QHBoxLayout()
        fila.addStretch(1)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(dlg.reject)
        fila.addWidget(btn_cancelar)
        btn_eliminar = QPushButton("Eliminar definitivamente")
        btn_eliminar.setObjectName("BotonPeligro")
        btn_eliminar.setEnabled(False)
        btn_eliminar.clicked.connect(dlg.accept)
        fila.addWidget(btn_eliminar)
        lay.addLayout(fila)

        campo.textChanged.connect(
            lambda t: btn_eliminar.setEnabled(t.strip() == nombre))
        return bool(dlg.exec())
