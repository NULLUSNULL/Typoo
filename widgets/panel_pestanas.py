# widgets/panel_pestanas.py
# Panel de edición con soporte de múltiples pestañas

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMenu,
    QMessageBox,
    QPushButton,
    QTabBar,
    QTabWidget,
    QWidget,
)

from editors.editor_markdown import EditorMarkdown
from models.documento import ItemProyecto


class PanelPestanas(QTabWidget):
    """
    Contenedor de pestañas que agrupa editores Markdown.
    Gestiona la apertura, cierre y guardado de documentos individuales.
    """

    # Señales
    editor_cambiado        = Signal(object)     # EditorMarkdown activo cambia
    documento_modificado   = Signal(str, bool)  # (nombre_archivo, modificado)
    palabras_actualizadas  = Signal(int)        # conteo de palabras del editor activo
    mover_a_panel          = Signal(object, int) # (ItemProyecto, panel_destino 1|2|3)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._configurar_widget()

    def _item_de(self, widget) -> Optional[ItemProyecto]:
        """ItemProyecto asociado a un editor (viaja con la pestaña al moverla)."""
        if isinstance(widget, EditorMarkdown):
            return getattr(widget, "item", None)
        return None

    def _configurar_widget(self) -> None:
        self.setTabsClosable(False)  # Gestionamos botones de cierre manualmente
        self.setMovable(True)
        self.setDocumentMode(True)
        self.currentChanged.connect(self._al_cambiar_pestana)

        # Menú contextual en la barra de pestañas
        self.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabBar().customContextMenuRequested.connect(self._menu_contextual_pestana)

    def _crear_boton_cierre(self, indice: int) -> None:
        """Instala un QPushButton '×' siempre visible como botón de cierre de la pestaña."""
        btn = QPushButton("×")
        btn.setObjectName("BotonCerrarPestana")
        btn.setFixedSize(18, 18)
        btn.setToolTip("Cerrar")
        btn.clicked.connect(lambda: self._on_click_cerrar(btn))
        self.tabBar().setTabButton(indice, QTabBar.ButtonPosition.RightSide, btn)

    def _on_click_cerrar(self, btn: QPushButton) -> None:
        for i in range(self.tabBar().count()):
            if self.tabBar().tabButton(i, QTabBar.ButtonPosition.RightSide) is btn:
                self._cerrar_pestana(i)
                return

    # ─── Apertura de documentos ───────────────────────────────────────────────

    def abrir_documento(self, item: ItemProyecto, contenido: str) -> "EditorMarkdown":
        """
        Abre el documento del ItemProyecto en una pestaña.
        Si ya está abierto, activa esa pestaña.
        """
        for indice in range(self.count()):
            existente = self._item_de(self.widget(indice))
            if existente and existente.id == item.id:
                self.setCurrentIndex(indice)
                return self.widget(indice)  # type: ignore[return-value]

        editor = EditorMarkdown(self)
        editor.setPlainText(contenido)
        editor.marcar_guardado()

        editor.modificado_cambiado.connect(
            lambda mod, nombre=item.nombre: self._al_modificarse(mod, nombre)
        )
        editor.palabras_cambiadas.connect(self._al_cambiar_palabras)

        editor.ruta_archivo = item.ruta_relativa
        editor.nombre_archivo = item.nombre
        editor.item = item

        indice = self.addTab(editor, item.nombre)
        self._crear_boton_cierre(indice)
        self.setCurrentIndex(indice)
        editor.setFocus()

        return editor

    # ─── Guardado ─────────────────────────────────────────────────────────────

    def editor_activo(self) -> Optional[EditorMarkdown]:
        """Retorna el editor de la pestaña actualmente seleccionada."""
        widget = self.currentWidget()
        return widget if isinstance(widget, EditorMarkdown) else None

    def item_activo(self) -> Optional[ItemProyecto]:
        """Retorna el ItemProyecto de la pestaña actualmente seleccionada."""
        return self._item_de(self.currentWidget())

    def guardar_editor_activo(self, funcion_guardar) -> bool:
        editor = self.editor_activo()
        item = self.item_activo()
        if editor and item:
            exito = funcion_guardar(item, editor.toPlainText())
            if exito:
                editor.marcar_guardado()
                self._actualizar_titulo_pestana(self.currentIndex(), item.nombre, False)
            return exito
        return False

    def guardar_todos(self, funcion_guardar) -> None:
        for indice in range(self.count()):
            editor = self.widget(indice)
            item = self._item_de(editor)
            if isinstance(editor, EditorMarkdown) and item and editor.modificado:
                if funcion_guardar(item, editor.toPlainText()):
                    editor.marcar_guardado()
                    self._actualizar_titulo_pestana(indice, item.nombre, False)

    def hay_cambios_pendientes(self) -> bool:
        for indice in range(self.count()):
            editor = self.widget(indice)
            if isinstance(editor, EditorMarkdown) and editor.modificado:
                return True
        return False

    # ─── Extracción de pestañas (para mover entre paneles) ───────────────────

    def extraer_item(self, item_id: str) -> Optional[tuple[ItemProyecto, str]]:
        """
        Cierra la pestaña del item sin confirmación y devuelve (item, contenido).
        Devuelve None si el item no está en este panel.
        """
        for i in range(self.count()):
            editor = self.widget(i)
            it = self._item_de(editor)
            if it and it.id == item_id:
                contenido = editor.toPlainText() if isinstance(editor, EditorMarkdown) else ""
                self.removeTab(i)
                return it, contenido
        return None

    # ─── Cierre de pestañas ───────────────────────────────────────────────────

    def _cerrar_pestana(self, indice: int) -> None:
        editor = self.widget(indice)
        if isinstance(editor, EditorMarkdown) and editor.modificado:
            item_local = self._item_de(editor)
            nombre = item_local.nombre if item_local else "Sin título"
            resp = QMessageBox.question(
                self,
                "Cambios sin guardar",
                f"«{nombre}» tiene cambios sin guardar.\n¿Guardar antes de cerrar?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
            )
            if resp == QMessageBox.StandardButton.Cancel:
                return

        self.removeTab(indice)

    def cerrar_todas_pestanas(self) -> None:
        while self.count() > 0:
            self.removeTab(0)

    # ─── Menú contextual de pestañas ─────────────────────────────────────────

    def _menu_contextual_pestana(self, pos) -> None:
        indice = self.tabBar().tabAt(pos)
        if indice < 0:
            return
        item = self._item_de(self.widget(indice))
        if not item:
            return

        menu = QMenu(self)

        for num, etiqueta in [(1, "Área 1"), (2, "Área 2"), (3, "Área 3")]:
            ac = QAction(f"Mover a {etiqueta}", self)
            ac.triggered.connect(
                lambda checked=False, it=item, n=num:
                    self.mover_a_panel.emit(it, n)
            )
            menu.addAction(ac)

        menu.addSeparator()
        ac_cerrar = QAction("Cerrar pestaña", self)
        ac_cerrar.triggered.connect(lambda: self._cerrar_pestana(indice))
        menu.addAction(ac_cerrar)

        menu.exec(self.tabBar().mapToGlobal(pos))

    # ─── Callbacks internos ───────────────────────────────────────────────────

    def _al_modificarse(self, modificado: bool, nombre: str) -> None:
        indice = self.currentIndex()
        self._actualizar_titulo_pestana(indice, nombre, modificado)
        self.documento_modificado.emit(nombre, modificado)

    def _al_cambiar_palabras(self, palabras: int) -> None:
        self.palabras_actualizadas.emit(palabras)

    def _al_cambiar_pestana(self, indice: int) -> None:
        editor = self.widget(indice)
        if isinstance(editor, EditorMarkdown):
            self.editor_cambiado.emit(editor)
            self.palabras_actualizadas.emit(editor.contar_palabras())

    def _actualizar_titulo_pestana(self, indice: int, nombre: str, modificado: bool) -> None:
        titulo = f"● {nombre}" if modificado else nombre
        self.setTabText(indice, titulo)
