# widgets/explorador_proyecto.py
# Panel lateral de exploración jerárquica del proyecto literario

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QInputDialog,
    QMenu,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.constantes import TipoElemento
from core.logger import logger
from models.documento import ItemProyecto
from models.proyecto import (
    Proyecto,
    ROL_MANUSCRITO, ROL_PERSONAJES, ROL_UBICACIONES, ROL_NOTAS,
)


# Mapeo de tipo → emoji/símbolo para el árbol
ICONO_POR_TIPO: dict[TipoElemento, str] = {
    TipoElemento.PROYECTO:   "📚",
    TipoElemento.CARPETA:    "📁",
    TipoElemento.CAPITULO:   "📖",
    TipoElemento.ESCENA:     "🎬",
    TipoElemento.NOTA:       "📝",
    TipoElemento.PERSONAJE:  "👤",
    TipoElemento.UBICACION:  "🗺",
}


class _ArbolProyecto(QTreeWidget):
    """QTreeWidget con reordenación por arrastre validada por el explorador."""

    def __init__(self, explorador: "ExploradorProyecto") -> None:
        super().__init__()
        self._explorador = explorador
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

    def dragMoveEvent(self, event) -> None:  # type: ignore[override]
        super().dragMoveEvent(event)  # deja que Qt calcule el indicador de drop
        origen = self.currentItem()
        destino = self.itemAt(event.position().toPoint())
        if self._explorador._destino_valido(origen, destino, self.dropIndicatorPosition()):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:  # type: ignore[override]
        origen = self.currentItem()
        destino = self.itemAt(event.position().toPoint())
        indicador = self.dropIndicatorPosition()
        # Gestionamos el modelo y refrescamos nosotros; no movemos widgets de Qt.
        self._explorador._procesar_soltar(event, origen, destino, indicador)


class ExploradorProyecto(QWidget):
    """
    Panel lateral izquierdo que muestra el árbol de un proyecto literario.
    Emite señales al seleccionar o crear elementos.
    """

    # Señales
    elemento_seleccionado = Signal(object)      # ItemProyecto seleccionado
    elemento_doble_click  = Signal(object)      # ItemProyecto para abrir en editor
    elemento_renombrado   = Signal(str, str)    # (id, nuevo_nombre)
    elemento_eliminado    = Signal(str)         # id del elemento eliminado
    elemento_creado       = Signal(object, str) # (ItemProyecto nuevo, padre_id)
    elemento_movido       = Signal(str)         # id del elemento reordenado/movido
    abrir_en_panel        = Signal(object, int) # (ItemProyecto, número de panel 1|2|3)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._proyecto: Optional[Proyecto] = None
        self._items_widget: dict[str, QTreeWidgetItem] = {}
        self._gestor: Optional[object] = None  # GestorProyectos inyectado
        self._construir_ui()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._arbol = _ArbolProyecto(self)
        self._arbol.setHeaderHidden(True)
        self._arbol.setAnimated(True)
        self._arbol.setExpandsOnDoubleClick(False)
        self._arbol.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._arbol.customContextMenuRequested.connect(self._mostrar_menu_contextual)
        self._arbol.itemClicked.connect(self._al_hacer_click)
        self._arbol.itemDoubleClicked.connect(self._al_doble_click)
        self._arbol.setIndentation(12)

        layout.addWidget(self._arbol)

    def establecer_gestor(self, gestor: object) -> None:
        """Inyecta el GestorProyectos para crear/eliminar elementos."""
        self._gestor = gestor

    # ─── Carga del proyecto ───────────────────────────────────────────────────

    def cargar_proyecto(self, proyecto: Proyecto) -> None:
        """Rellena el árbol con la estructura del proyecto."""
        self._proyecto = proyecto
        self._items_widget.clear()
        self._arbol.clear()

        if proyecto.raiz:
            self._agregar_nodo(proyecto.raiz, None)

        self._arbol.expandAll()

    def refrescar(self) -> None:
        """Recarga el árbol desde el proyecto activo."""
        if self._proyecto:
            self.cargar_proyecto(self._proyecto)

    def limpiar(self) -> None:
        """Vacía el árbol al cerrar un proyecto."""
        self._proyecto = None
        self._items_widget.clear()
        self._arbol.clear()

    # ─── Construcción del árbol ───────────────────────────────────────────────

    def _agregar_nodo(
        self,
        item: ItemProyecto,
        padre_widget: Optional[QTreeWidgetItem],
    ) -> QTreeWidgetItem:
        """Crea recursivamente un QTreeWidgetItem para el item dado."""
        icono = ICONO_POR_TIPO.get(item.tipo, "📄")
        texto = f"{icono}  {item.nombre}"

        if padre_widget is None:
            nodo = QTreeWidgetItem(self._arbol, [texto])
        else:
            nodo = QTreeWidgetItem(padre_widget, [texto])

        nodo.setData(0, Qt.ItemDataRole.UserRole, item.id)
        nodo.setExpanded(item.expandido)

        # Fuente más visible para el nodo raíz
        if item.tipo == TipoElemento.PROYECTO:
            fuente = nodo.font(0)
            fuente.setBold(True)
            nodo.setFont(0, fuente)

        self._items_widget[item.id] = nodo

        for hijo in sorted(item.hijos, key=lambda h: h.orden):
            self._agregar_nodo(hijo, nodo)

        return nodo

    def seleccionar_item(self, item_id: str) -> None:
        """Selecciona programáticamente un nodo por su ID."""
        nodo = self._items_widget.get(item_id)
        if nodo:
            self._arbol.setCurrentItem(nodo)

    # ─── Eventos de interacción ───────────────────────────────────────────────

    def _al_hacer_click(self, nodo: QTreeWidgetItem, columna: int) -> None:
        item = self._item_desde_nodo(nodo)
        if item:
            self.elemento_seleccionado.emit(item)

    def _al_doble_click(self, nodo: QTreeWidgetItem, columna: int) -> None:
        item = self._item_desde_nodo(nodo)
        if item and item.ruta_relativa:
            self.elemento_doble_click.emit(item)

    def _item_desde_nodo(self, nodo: QTreeWidgetItem) -> Optional[ItemProyecto]:
        if not self._proyecto:
            return None
        item_id = nodo.data(0, Qt.ItemDataRole.UserRole)
        return self._proyecto.buscar_item(item_id)

    def item_seleccionado(self) -> Optional[ItemProyecto]:
        """Devuelve el ItemProyecto del nodo seleccionado, si lo hay."""
        nodo = self._arbol.currentItem()
        return self._item_desde_nodo(nodo) if nodo else None

    # ─── Reordenación por arrastre ────────────────────────────────────────────

    def _puede_contener(self, padre: ItemProyecto, origen: ItemProyecto) -> bool:
        """Reglas de jerarquía: cada tipo solo vive en su sección."""
        rol = padre.metadatos.get("rol")
        if origen.tipo == TipoElemento.ESCENA:
            return padre.tipo == TipoElemento.CAPITULO
        if origen.tipo == TipoElemento.CAPITULO:
            return rol == ROL_MANUSCRITO
        if origen.tipo == TipoElemento.PERSONAJE:
            return rol == ROL_PERSONAJES
        if origen.tipo == TipoElemento.UBICACION:
            return rol == ROL_UBICACIONES
        if origen.tipo == TipoElemento.NOTA:
            return rol == ROL_NOTAS
        return False

    def _indice_en_padre(self, item: ItemProyecto) -> int:
        padre = self._proyecto.buscar_item(item.padre_id) if item.padre_id else None
        if not padre:
            return 0
        hijos = sorted(padre.hijos, key=lambda h: h.orden)
        return next((i for i, h in enumerate(hijos) if h.id == item.id), len(hijos))

    def _resolver_destino(self, origen_nodo, destino_nodo, indicador):
        """Devuelve (padre_item, indice) válido para soltar, o None."""
        if self._proyecto is None or origen_nodo is None or destino_nodo is None:
            return None
        origen = self._item_desde_nodo(origen_nodo)
        destino = self._item_desde_nodo(destino_nodo)
        if not origen or not destino or origen.id == destino.id:
            return None

        Pos = QAbstractItemView.DropIndicatorPosition
        if indicador == Pos.OnItem:
            # Soltar «dentro» del destino; si no admite a origen, ponerlo como
            # hermano justo después del destino.
            if self._puede_contener(destino, origen):
                return destino, len(destino.hijos)
            padre = self._proyecto.buscar_item(destino.padre_id) if destino.padre_id else None
            if padre and self._puede_contener(padre, origen):
                return padre, self._indice_en_padre(destino) + 1
            return None
        if indicador in (Pos.AboveItem, Pos.BelowItem):
            padre = self._proyecto.buscar_item(destino.padre_id) if destino.padre_id else None
            if not padre or not self._puede_contener(padre, origen):
                return None
            idx = self._indice_en_padre(destino)
            return padre, idx + (1 if indicador == Pos.BelowItem else 0)
        return None

    def _destino_valido(self, origen_nodo, destino_nodo, indicador) -> bool:
        return self._resolver_destino(origen_nodo, destino_nodo, indicador) is not None

    def _procesar_soltar(self, event, origen_nodo, destino_nodo, indicador) -> None:
        res = self._resolver_destino(origen_nodo, destino_nodo, indicador)
        origen = self._item_desde_nodo(origen_nodo) if origen_nodo else None
        if not res or not origen or not self._gestor:
            event.ignore()
            return
        padre_item, indice = res
        if self._gestor.mover_elemento(origen.id, padre_item.id, indice):  # type: ignore[union-attr]
            event.acceptProposedAction()
            self.refrescar()
            self.seleccionar_item(origen.id)
            self.elemento_movido.emit(origen.id)
        else:
            event.ignore()

    # ─── Menú contextual ──────────────────────────────────────────────────────

    def _mostrar_menu_contextual(self, posicion) -> None:
        nodo = self._arbol.itemAt(posicion)
        menu = QMenu(self)

        if nodo:
            item = self._item_desde_nodo(nodo)
            if item:
                if item.es_contenedor():
                    self._agregar_acciones_crear(menu, item)
                    menu.addSeparator()

                # Documentos: opción para abrir en área específica
                if item.ruta_relativa:
                    submenu_areas = menu.addMenu("Abrir en área")
                    for num, etiqueta in [(1, "Área 1"), (2, "Área 2"), (3, "Área 3")]:
                        ac = QAction(etiqueta, self)
                        ac.triggered.connect(
                            lambda checked=False, it=item, n=num:
                                self.abrir_en_panel.emit(it, n)
                        )
                        submenu_areas.addAction(ac)
                    menu.addSeparator()

                accion_renombrar = QAction("Renombrar", self)
                accion_renombrar.triggered.connect(lambda: self._renombrar(item))
                menu.addAction(accion_renombrar)

                if item.tipo != TipoElemento.PROYECTO:
                    accion_eliminar = QAction("Eliminar", self)
                    accion_eliminar.triggered.connect(lambda: self._eliminar(item))
                    menu.addAction(accion_eliminar)
        else:
            # Clic en área vacía
            if self._proyecto:
                self._agregar_acciones_crear(menu, self._proyecto.raiz)

        if not menu.isEmpty():
            menu.exec(self._arbol.viewport().mapToGlobal(posicion))

    def _agregar_acciones_crear(self, menu: QMenu, padre: ItemProyecto) -> None:
        """
        Añade las acciones de creación pertinentes según el contenedor:
        en «Manuscrito» se crean capítulos, dentro de un capítulo escenas, etc.
        """
        acciones: list[tuple[str, TipoElemento, ItemProyecto]] = []
        rol = padre.metadatos.get("rol")

        if padre.tipo == TipoElemento.CAPITULO:
            acciones.append(("Nueva escena", TipoElemento.ESCENA, padre))
        elif rol == ROL_MANUSCRITO:
            acciones.append(("Nuevo capítulo", TipoElemento.CAPITULO, padre))
        elif rol == ROL_PERSONAJES:
            acciones.append(("Nuevo personaje", TipoElemento.PERSONAJE, padre))
        elif rol == ROL_UBICACIONES:
            acciones.append(("Nueva ubicación", TipoElemento.UBICACION, padre))
        elif rol == ROL_NOTAS:
            acciones.append(("Nueva nota", TipoElemento.NOTA, padre))
        elif padre.tipo == TipoElemento.PROYECTO:
            # En la raíz, crear un capítulo directamente en el Manuscrito.
            manuscrito = self._proyecto.carpeta_por_rol(ROL_MANUSCRITO) if self._proyecto else None
            if manuscrito is not None:
                acciones.append(("Nuevo capítulo", TipoElemento.CAPITULO, manuscrito))

        for etiqueta, tipo, destino in acciones:
            accion = QAction(etiqueta, self)
            accion.triggered.connect(
                lambda checked=False, t=tipo, p=destino:
                    self._crear_elemento(t, p, "")
            )
            menu.addAction(accion)

    # ─── Acciones CRUD ────────────────────────────────────────────────────────

    def _crear_elemento(
        self,
        tipo: TipoElemento,
        padre: ItemProyecto,
        subdir: str,
    ) -> None:
        nombre_tipo = tipo.value.capitalize()
        nombre, ok = QInputDialog.getText(
            self, f"Nuevo {nombre_tipo}", f"Nombre del {nombre_tipo}:"
        )
        if ok and nombre.strip() and self._gestor:
            nuevo = self._gestor.crear_elemento(  # type: ignore[union-attr]
                nombre.strip(), tipo, padre.id, subdir
            )
            if nuevo:
                self.refrescar()
                self.seleccionar_item(nuevo.id)
                self.elemento_creado.emit(nuevo, padre.id)
                logger.info("Elemento creado desde explorador: %s", nombre)

    def _renombrar(self, item: ItemProyecto) -> None:
        nuevo_nombre, ok = QInputDialog.getText(
            self, "Renombrar", "Nuevo nombre:", text=item.nombre
        )
        if ok and nuevo_nombre.strip() and self._gestor:
            if self._gestor.renombrar_elemento(item.id, nuevo_nombre.strip()):  # type: ignore[union-attr]
                self.refrescar()
                self.elemento_renombrado.emit(item.id, nuevo_nombre.strip())

    def _eliminar(self, item: ItemProyecto) -> None:
        resp = QMessageBox.question(
            self,
            "Eliminar elemento",
            f"¿Eliminar «{item.nombre}»?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if resp == QMessageBox.StandardButton.Yes and self._gestor:
            if self._gestor.eliminar_elemento(item.id):  # type: ignore[union-attr]
                self.refrescar()
                self.elemento_eliminado.emit(item.id)
