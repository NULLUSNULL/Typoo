# ui/ventana_principal.py
# Ventana principal de la aplicación Typoo

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QFont,
    QIcon,
    QKeySequence,
    QShortcut,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.configuracion import Configuracion
from core.constantes import (
    NOMBRE_APP, VERSION_APP, Tema, TipoElemento,
    ANCHO_MINIMO_EXPLORADOR, ANCHO_MINIMO_VISTA_PREVIA,
    RUTA_ICONO,
)
from core.logger import logger
from models.documento import ItemProyecto
from models.proyecto import Proyecto
from services.autoguardado import ServicioAutoguardado
from services.busqueda import ServicioBusqueda
from services.gestor_archivos import GestorArchivos
from services.gestor_proyectos import GestorProyectos
from ui.dialogos.buscar_reemplazar import DialogoBuscarReemplazar
from ui.dialogos.exportar import DialogoExportar
from ui.dialogos.gestor_proyectos import DialogoGestorProyectos
from ui.dialogos.nuevo_proyecto import DialogoNuevoProyecto
from ui.dialogos.preferencias import DialogoPreferencias
from ui.temas.gestor_temas import GestorTemas
from widgets.barra_estado import BarraEstado
from widgets.barra_herramientas import BarraHerramientas
from widgets.barra_titulo import BarraTitulo, RedimensionadorSinBorde, ES_LINUX
from widgets.explorador_proyecto import ExploradorProyecto
from widgets.panel_pestanas import PanelPestanas
from widgets.panel_metadatos import PanelMetadatos
from widgets.panel_tramas import PanelTramas
from widgets.panel_asistente import PanelAsistente


class VentanaPrincipal(QMainWindow):
    """
    Ventana principal de Typoo.

    Distribución:
    ┌──────────────────────────────────────────────────────────────┐
    │  Barra de menú                                               │
    ├──────────────────────────────────────────────────────────────┤
    │  Barra de herramientas de formato                            │
    ├─────────────────┬──────────────────────────────┬────────────┤
    │ ExploradorProyecto │  PanelPestanas (1-3 paneles) │ Detalles   │
    ├─────────────────┴──────────────────────────────┴────────────┤
    │  Barra de estado                                             │
    └──────────────────────────────────────────────────────────────┘
    """

    def __init__(self) -> None:
        super().__init__()
        self._config         = Configuracion()
        self._gestor         = GestorProyectos()
        self._dialogo_buscar: Optional[DialogoBuscarReemplazar] = None
        self._busqueda_actual: list[tuple[int, int]] = []
        self._indice_busqueda: int = 0
        self._patron_busqueda: str = ""
        self._resultados_proyecto: list = []

        self._timer_respaldo: Optional[QTimer] = None

        self._hint_concentracion: Optional[QLabel] = None
        self._atajo_salir_concentracion: Optional[QShortcut] = None
        self._estado_concentracion: dict = {}

        self._redimensionador = None
        self._configurar_marco_sin_borde()

        self._construir_ui()
        self._crear_menus()
        self._crear_barra_herramientas()
        self._conectar_señales()
        self._restaurar_geometria()
        self._iniciar_autoguardado()
        self._iniciar_timer_respaldo()
        self._aplicar_tema_inicial()
        self._aplicar_icono()

        self.setWindowTitle(NOMBRE_APP)
        logger.info("%s %s iniciado", NOMBRE_APP, VERSION_APP)

        # Al arrancar, mostrar el gestor de proyectos (tras pintar la ventana).
        QTimer.singleShot(0, lambda: self._abrir_gestor_proyectos(al_inicio=True))

    # ─── Construcción de la interfaz ──────────────────────────────────────────

    def _construir_ui(self) -> None:
        self.setMinimumSize(900, 600)

        # Widget central: contenedor vertical con la barra superior (título +
        # formato) fija encima del splitter horizontal principal. Al no ser un
        # dock, la barra superior no se puede redimensionar arrastrando.
        self._central = QWidget()
        self._central_layout = QVBoxLayout(self._central)
        self._central_layout.setContentsMargins(0, 0, 0, 0)
        self._central_layout.setSpacing(0)
        self.setCentralWidget(self._central)

        self._splitter_principal = QSplitter(Qt.Orientation.Horizontal)
        self._splitter_principal.setChildrenCollapsible(False)
        self._central_layout.addWidget(self._splitter_principal)

        # 1. Explorador de proyecto (izquierda)
        self._explorador = ExploradorProyecto()
        self._explorador.establecer_gestor(self._gestor)
        self._explorador.setMinimumWidth(ANCHO_MINIMO_EXPLORADOR)
        self._explorador.setMaximumWidth(450)

        # 2. Zona de edición central: splitter vertical para hasta 3 paneles
        self._splitter_paneles = QSplitter(Qt.Orientation.Vertical)
        self._splitter_paneles.setChildrenCollapsible(False)

        self._panel1 = PanelPestanas()
        self._panel2 = PanelPestanas()
        self._panel3 = PanelPestanas()

        self._splitter_paneles.addWidget(self._panel1)
        self._splitter_paneles.addWidget(self._panel2)
        self._splitter_paneles.addWidget(self._panel3)

        # Ocultar paneles 2 y 3 por defecto
        self._panel2.hide()
        self._panel3.hide()

        # 3. Panel de detalles / metadatos (derecha)
        self._panel_metadatos = PanelMetadatos()
        self._panel_metadatos.setMinimumWidth(ANCHO_MINIMO_VISTA_PREVIA)

        self._splitter_principal.addWidget(self._explorador)
        self._splitter_principal.addWidget(self._splitter_paneles)
        self._splitter_principal.addWidget(self._panel_metadatos)
        self._splitter_principal.setSizes([220, 650, 280])

        # Barra de estado
        self._barra_estado = BarraEstado(self)
        self.setStatusBar(self._barra_estado)

    def _crear_barra_herramientas(self) -> None:
        """Construye la barra superior fija (título de la app + barra de formato)
        e la inserta encima del área de edición. No es un dock, por lo que no se
        puede redimensionar arrastrando su borde."""
        self._barra_titulo = BarraTitulo(self, NOMBRE_APP)
        # Compatibilidad: el indicador de IA vive ahora en la barra de título.
        self._icono_ia = self._barra_titulo.icono_ia

        self._barra_formato = BarraHerramientas()
        self._barra_formato.setObjectName("BarraHerramientas")

        self._barra_superior = QWidget()
        self._barra_superior.setObjectName("BarraSuperior")
        vbox = QVBoxLayout(self._barra_superior)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(self._barra_titulo)
        vbox.addWidget(self._barra_formato)

        # La barra superior debe ceñirse a su contenido (no expandirse en
        # vertical): así el área de edición ocupa todo el alto restante.
        for w in (self._barra_superior, self._barra_titulo, self._barra_formato):
            w.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self._central_layout.insertWidget(0, self._barra_superior)
        self._actualizar_banner_ia()

    def _actualizar_banner_ia(self) -> None:
        """Muestra el icono de IA en el banner cuando el asistente está activo."""
        if not hasattr(self, "_icono_ia"):
            return
        if self._config.ia_habilitada:
            from PySide6.QtGui import QIcon
            from core.constantes import RUTA_ICONO
            ruta = RUTA_ICONO.parent / "ia.svg"
            if ruta.exists():
                self._icono_ia.setPixmap(QIcon(str(ruta)).pixmap(18, 18))
                self._icono_ia.setToolTip("Asistente de IA activo")
                self._icono_ia.show()
            else:
                self._icono_ia.hide()
        else:
            self._icono_ia.hide()

        # Visor de tramas: banda inferior a lo ancho, plegable.
        self._panel_tramas = PanelTramas()
        dock_tramas = QDockWidget("Tramas", self)
        dock_tramas.setObjectName("DockTramas")
        dock_tramas.setWidget(self._panel_tramas)
        dock_tramas.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea |
            Qt.DockWidgetArea.TopDockWidgetArea
        )
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock_tramas)
        dock_tramas.hide()
        self._dock_tramas = dock_tramas

        # Asistente de IA (chat con contexto): panel lateral derecho, plegable.
        self._panel_asistente = PanelAsistente()
        self._panel_asistente.establecer_gestor(self._gestor)
        dock_asistente = QDockWidget("Asistente", self)
        dock_asistente.setObjectName("DockAsistente")
        dock_asistente.setWidget(self._panel_asistente)
        dock_asistente.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea |
            Qt.DockWidgetArea.LeftDockWidgetArea
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_asistente)
        dock_asistente.hide()
        dock_asistente.visibilityChanged.connect(self._al_cambiar_visibilidad_asistente)
        self._dock_asistente = dock_asistente

    # ─── Sistema de menús ─────────────────────────────────────────────────────

    def _crear_menus(self) -> None:
        barra = self.menuBar()

        # ── Menú Archivo ──────────────────────────────────────────────────────
        m_archivo = barra.addMenu("&Archivo")

        ac = self._accion("&Gestor de proyectos…", "Ctrl+Shift+O",
                          self._abrir_gestor_proyectos)
        m_archivo.addAction(ac)

        ac = self._accion("&Nuevo proyecto…", "Ctrl+Shift+N", self._nuevo_proyecto)
        m_archivo.addAction(ac)

        ac = self._accion("&Abrir proyecto…", "Ctrl+O", self._abrir_proyecto)
        m_archivo.addAction(ac)

        m_archivo.addSeparator()

        ac = self._accion("&Guardar", "Ctrl+S", self._guardar_activo)
        m_archivo.addAction(ac)

        ac = self._accion("Guardar &todos", "Ctrl+Shift+S", self._guardar_todos)
        m_archivo.addAction(ac)

        m_archivo.addSeparator()

        ac = self._accion("&Exportar…", "", self._exportar)
        m_archivo.addAction(ac)

        m_archivo.addSeparator()

        ac = self._accion("&Salir", "Ctrl+Q", self.close)
        m_archivo.addAction(ac)

        # ── Menú Editar ───────────────────────────────────────────────────────
        m_editar = barra.addMenu("&Editar")

        ac = self._accion("&Deshacer", "Ctrl+Z", self._deshacer)
        m_editar.addAction(ac)

        ac = self._accion("&Rehacer", "Ctrl+Y", self._rehacer)
        m_editar.addAction(ac)

        m_editar.addSeparator()

        ac = self._accion("&Cortar",  "Ctrl+X", self._cortar)
        m_editar.addAction(ac)

        ac = self._accion("&Copiar",  "Ctrl+C", self._copiar)
        m_editar.addAction(ac)

        ac = self._accion("&Pegar",   "Ctrl+V", self._pegar)
        m_editar.addAction(ac)

        m_editar.addSeparator()

        ac = self._accion("&Buscar…", "Ctrl+F", self._abrir_buscar)
        m_editar.addAction(ac)

        ac = self._accion("Buscar y &reemplazar…", "Ctrl+H", self._abrir_buscar)
        m_editar.addAction(ac)

        # ── Menú Ver ──────────────────────────────────────────────────────────
        m_ver = barra.addMenu("&Ver")

        self._ac_explorador = self._accion(
            "Explorador de proyecto", "Ctrl+1",
            lambda: self._alternar_panel_explorador(),
            checkable=True, checked=True,
        )
        m_ver.addAction(self._ac_explorador)

        self._ac_panel2 = self._accion(
            "Panel de edición 2", "Ctrl+2",
            lambda: self._alternar_panel(self._panel2, self._ac_panel2),
            checkable=True, checked=False,
        )
        m_ver.addAction(self._ac_panel2)

        self._ac_panel3 = self._accion(
            "Panel de edición 3", "Ctrl+3",
            lambda: self._alternar_panel(self._panel3, self._ac_panel3),
            checkable=True, checked=False,
        )
        m_ver.addAction(self._ac_panel3)

        self._ac_detalles = self._accion(
            "Panel de detalles", "Ctrl+4",
            lambda: self._alternar_panel(self._panel_metadatos, self._ac_detalles),
            checkable=True, checked=True,
        )
        m_ver.addAction(self._ac_detalles)

        self._ac_tramas = self._accion(
            "Visor de tramas", "Ctrl+5",
            self._alternar_tramas,
            checkable=True, checked=False,
        )
        m_ver.addAction(self._ac_tramas)

        self._ac_asistente = self._accion(
            "Asistente de IA", "Ctrl+6",
            self._alternar_asistente,
            checkable=True, checked=False,
        )
        m_ver.addAction(self._ac_asistente)

        m_ver.addSeparator()

        self._ac_tema = self._accion(
            "Cambiar a tema claro", "Ctrl+Shift+T",
            self._alternar_tema,
        )
        m_ver.addAction(self._ac_tema)
        self._actualizar_etiqueta_tema()

        m_ver.addSeparator()

        ac = self._accion("Pantalla completa", "F11", self._alternar_pantalla_completa)
        m_ver.addAction(ac)

        # ── Menú Proyecto ─────────────────────────────────────────────────────
        m_proyecto = barra.addMenu("&Proyecto")

        ac = self._accion("Nuevo &capítulo",   "Ctrl+Shift+C",
                          lambda: self._crear_elemento(TipoElemento.CAPITULO))
        m_proyecto.addAction(ac)

        ac = self._accion("Nueva &escena",     "Ctrl+Shift+E",
                          lambda: self._crear_elemento(TipoElemento.ESCENA))
        m_proyecto.addAction(ac)

        ac = self._accion("Nueva &nota",       "Ctrl+Shift+A",
                          lambda: self._crear_elemento(TipoElemento.NOTA))
        m_proyecto.addAction(ac)

        ac = self._accion("Nuevo &personaje",  "",
                          lambda: self._crear_elemento(TipoElemento.PERSONAJE))
        m_proyecto.addAction(ac)

        ac = self._accion("Nueva &ubicación",  "",
                          lambda: self._crear_elemento(TipoElemento.UBICACION))
        m_proyecto.addAction(ac)

        m_proyecto.addSeparator()

        ac = self._accion("Crear &respaldo",   "",
                          self._crear_respaldo)
        m_proyecto.addAction(ac)

        # ── Menú Herramientas ─────────────────────────────────────────────────
        m_herr = barra.addMenu("&Herramientas")

        ac = self._accion("&Preferencias…", "Ctrl+,",
                          lambda: self._abrir_preferencias())
        # En macOS, Qt lo mueve al menú de la app (Typoo → Preferencias).
        ac.setMenuRole(QAction.MenuRole.PreferencesRole)
        m_herr.addAction(ac)

        m_herr.addSeparator()

        self._ac_concentracion = self._accion(
            "Modo concentración", "F12",
            self._alternar_concentracion,
            checkable=True, checked=False,
        )
        m_herr.addAction(self._ac_concentracion)

        # ── Menú Ayuda ────────────────────────────────────────────────────────
        m_ayuda = barra.addMenu("A&yuda")
        ac = self._accion(f"Acerca de {NOMBRE_APP}", "", self._acerca_de)
        m_ayuda.addAction(ac)

    def _accion(
        self,
        texto: str,
        atajo: str,
        slot,
        checkable: bool = False,
        checked: bool = False,
    ) -> QAction:
        """
        Factoría de QAction con atajo de teclado opcional.
        El padre es siempre self (la ventana), así Qt gestiona la vida
        del objeto C++ y Python no lo destruye al salir del ámbito local.
        """
        accion = QAction(texto, self)
        if atajo:
            accion.setShortcut(QKeySequence(atajo))
        accion.triggered.connect(slot)
        if checkable:
            accion.setCheckable(True)
            accion.setChecked(checked)
        return accion

    # ─── Conexión de señales ──────────────────────────────────────────────────

    def _conectar_señales(self) -> None:
        # Explorador
        self._explorador.elemento_doble_click.connect(self._abrir_item_en_editor)
        self._explorador.elemento_seleccionado.connect(self._al_seleccionar_item)
        self._explorador.abrir_en_panel.connect(self._abrir_item_en_panel)

        # Paneles de edición
        for num, panel in enumerate((self._panel1, self._panel2, self._panel3), start=1):
            panel.editor_cambiado.connect(
                lambda editor, p=panel: self._al_cambiar_editor(editor, p)
            )
            # Los Detalles siguen siempre al item activo (None si el panel se vacía)
            panel.item_activo_cambiado.connect(self._panel_metadatos.mostrar_item)
            panel.palabras_actualizadas.connect(self._barra_estado.actualizar_palabras)
            panel.documento_modificado.connect(self._al_documento_modificado)
            panel.mover_a_panel.connect(
                lambda item, destino, origen=panel:
                    self._mover_a_panel(item, origen, destino)
            )
            # Reescritura con IA desde el menú contextual del editor.
            panel.ia_reescribir_solicitada.connect(self._reescribir_seleccion)
            panel.ia_tormenta_solicitada.connect(self._ia_tormenta)

        # Panel de detalles: guardar los metadatos editados (con retardo)
        self._timer_metadatos = QTimer(self)
        self._timer_metadatos.setSingleShot(True)
        self._timer_metadatos.setInterval(800)
        self._timer_metadatos.timeout.connect(self._persistir_metadatos)
        self._panel_metadatos.metadatos_modificados.connect(self._timer_metadatos.start)
        # Si cambian los vínculos de una escena, refrescar el visor de tramas
        self._panel_metadatos.metadatos_modificados.connect(self._panel_tramas.refrescar)
        # Reflejar en el árbol el color de estado al editarlo (sin reconstruirlo)
        self._panel_metadatos.metadatos_modificados.connect(self._explorador.refrescar_estados)
        # Al persistir metadatos puede haber cambiado un nombre/alias del dossier
        self._timer_metadatos.timeout.connect(self._aplicar_nombres_editores)

        # Visor de tramas
        self._panel_tramas.relaciones_modificadas.connect(self._timer_metadatos.start)
        self._panel_tramas.relaciones_modificadas.connect(self._panel_metadatos.refrescar)
        self._panel_tramas.tramas_modificadas.connect(self._timer_metadatos.start)
        self._panel_tramas.tramas_modificadas.connect(self._panel_metadatos.refrescar)
        self._panel_tramas.escena_activada.connect(self._abrir_item_en_editor)

        # Al crear o reordenar elementos refrescar los paneles dependientes
        self._explorador.elemento_creado.connect(self._al_crear_elemento)
        self._explorador.elemento_movido.connect(self._al_reorganizar)
        # Mantener al día la lista de nombres para autocompletar con «@»
        self._explorador.elemento_renombrado.connect(
            lambda *_: self._aplicar_nombres_editores()
        )
        self._explorador.elemento_eliminado.connect(
            lambda *_: self._aplicar_nombres_editores()
        )
        # Acciones de dossier con IA desde el menú contextual del explorador.
        self._explorador.accion_ia_solicitada.connect(self._al_accion_ia_explorador)

        # Barra de formato (orientada a novela)
        bh = self._barra_formato
        # Tipografía
        bh.fuente_cambiada.connect(self._cambiar_fuente_editor)
        bh.tamano_cambiado.connect(self._cambiar_tamano_editor)
        # Énfasis de carácter
        bh.negrita_solicitada.connect(lambda: self._formato("**", "**"))
        bh.cursiva_solicitada.connect(lambda: self._formato("*", "*"))
        bh.subrayado_solicitado.connect(lambda: self._formato("<u>", "</u>"))
        bh.tachado_solicitado.connect(lambda: self._formato("<s>", "</s>"))
        bh.subindice_solicitado.connect(lambda: self._formato("<sub>", "</sub>"))
        bh.superindice_solicitado.connect(lambda: self._formato("<sup>", "</sup>"))
        # Estructura
        bh.encabezado_solicitado.connect(self._insertar_encabezado)
        bh.cita_solicitada.connect(self._insertar_cita)
        # Listas y sangría
        bh.lista_viñeta_solicitada.connect(self._lista_vinetas)
        bh.lista_num_solicitada.connect(self._lista_numerada)
        bh.sangria_aumentar_sol.connect(self._sangrar)
        bh.sangria_disminuir_sol.connect(self._desangrar)
        # Separador de escena
        bh.separador_solicitado.connect(self._insertar_separador)
        # Caracteres especiales: insertar literal o envolver la selección
        bh.caracter_solicitado.connect(self._insertar_texto)
        bh.envolver_solicitado.connect(self._formato)

    # ─── Autoguardado ─────────────────────────────────────────────────────────

    def _iniciar_autoguardado(self) -> None:
        self._autoguardado = ServicioAutoguardado(self._guardar_todos)
        self._autoguardado.iniciar()

    # ─── Timer de respaldo automático ─────────────────────────────────────────

    def _iniciar_timer_respaldo(self) -> None:
        intervalo = self._config.intervalo_respaldo_ms
        if intervalo <= 0:
            return
        self._timer_respaldo = QTimer(self)
        self._timer_respaldo.timeout.connect(self._crear_respaldo)
        self._timer_respaldo.start(intervalo)

    def _reiniciar_timer_respaldo(self) -> None:
        if self._timer_respaldo:
            self._timer_respaldo.stop()
            self._timer_respaldo = None
        self._iniciar_timer_respaldo()

    # ─── Áreas de trabajo ─────────────────────────────────────────────────────

    def _panel_por_numero(self, num: int) -> Optional[PanelPestanas]:
        return {1: self._panel1, 2: self._panel2, 3: self._panel3}.get(num)

    def _accion_visibilidad_panel(self, num: int) -> Optional[QAction]:
        return {2: self._ac_panel2, 3: self._ac_panel3}.get(num)

    def _localizar_item_abierto(self, item_id: str):
        """Devuelve (panel, num, indice) si el item ya está abierto en algún área."""
        for num, panel in enumerate((self._panel1, self._panel2, self._panel3), start=1):
            for i in range(panel.count()):
                editor = panel.widget(i)
                it = getattr(editor, "item", None)
                if it is not None and it.id == item_id:
                    return panel, num, i
        return None

    def _activar_item_abierto(self, item: ItemProyecto) -> bool:
        """
        Si el documento ya está abierto en cualquier área, lo trae al frente y
        devuelve True (evita cargarlo por duplicado en otra área).
        """
        localizacion = self._localizar_item_abierto(item.id)
        if not localizacion:
            return False
        panel, num, indice = localizacion
        if panel.isHidden():
            panel.show()
            ac = self._accion_visibilidad_panel(num)
            if ac:
                ac.setChecked(True)
        panel.setCurrentIndex(indice)
        editor = panel.widget(indice)
        if editor:
            editor.setFocus()
        self._panel_metadatos.mostrar_item(item)
        self._barra_estado.actualizar_archivo(item.nombre)
        self._barra_estado.mostrar_mensaje(
            f"«{item.nombre}» ya está abierto en el Área {num}.", 2500
        )
        return True

    def _abrir_item_en_panel(self, item: ItemProyecto, panel_num: int) -> None:
        """Abre un documento en el panel indicado (1, 2 o 3)."""
        panel = self._panel_por_numero(panel_num)
        if not panel:
            return
        if not item.ruta_relativa:
            return
        # Un documento solo puede estar abierto en un área: si ya lo está, se activa.
        if self._activar_item_abierto(item):
            return
        contenido = self._gestor.leer_documento(item)
        if panel.isHidden():
            panel.show()
            ac = self._accion_visibilidad_panel(panel_num)
            if ac:
                ac.setChecked(True)
        editor = panel.abrir_documento(item, contenido)
        editor.cursorPositionChanged.connect(
            lambda: self._actualizar_posicion_cursor(editor)
        )
        editor.tamano_zoom_cambiado.connect(self._al_zoom_editor)
        editor.establecer_nombres(self._nombres_dossier())
        self._panel_metadatos.mostrar_item(item)
        self._barra_estado.actualizar_archivo(item.nombre)

    def _mover_a_panel(
        self,
        item: ItemProyecto,
        origen: PanelPestanas,
        destino_num: int,
    ) -> None:
        """Mueve una pestaña del panel origen al panel destino_num."""
        destino = self._panel_por_numero(destino_num)
        if not destino or destino is origen:
            return
        resultado = origen.extraer_item(item.id)
        if not resultado:
            return
        _, contenido = resultado
        if destino.isHidden():
            destino.show()
            ac = self._accion_visibilidad_panel(destino_num)
            if ac:
                ac.setChecked(True)
        editor = destino.abrir_documento(item, contenido)
        editor.cursorPositionChanged.connect(
            lambda: self._actualizar_posicion_cursor(editor)
        )
        editor.tamano_zoom_cambiado.connect(self._al_zoom_editor)
        editor.establecer_nombres(self._nombres_dossier())
        self._panel_metadatos.mostrar_item(item)

    # ─── Fuente del editor ────────────────────────────────────────────────────

    def _aplicar_fuente_editores(self) -> None:
        """Aplica la fuente configurada a todos los editores abiertos."""
        familia = self._config.fuente_familia
        tamano = self._config.fuente_tamanio
        for panel in (self._panel1, self._panel2, self._panel3):
            for i in range(panel.count()):
                editor = panel.widget(i)
                if editor and hasattr(editor, "aplicar_fuente"):
                    editor.aplicar_fuente(familia, tamano)

    # ─── Autocompletado de nombres del dossier ────────────────────────────────

    def _nombres_dossier(self) -> list[str]:
        """Nombres de personajes y ubicaciones (con alias) para autocompletar @."""
        if not self._gestor.hay_proyecto:
            return []
        proy = self._gestor.proyecto_activo
        nombres: list[str] = []
        for p in proy.personajes():
            nombres.append(p.nombre)
            for clave in ("nombre_completo", "alias"):
                valor = p.metadatos.get(clave)
                if isinstance(valor, str) and valor.strip():
                    nombres.append(valor.strip())
        for u in proy.ubicaciones():
            nombres.append(u.nombre)
        return nombres

    def _aplicar_nombres_editores(self) -> None:
        """Envía la lista de nombres a todos los editores abiertos."""
        nombres = self._nombres_dossier()
        for panel in (self._panel1, self._panel2, self._panel3):
            for i in range(panel.count()):
                editor = panel.widget(i)
                if editor and hasattr(editor, "establecer_nombres"):
                    editor.establecer_nombres(nombres)

    # ─── Gestión de proyectos ─────────────────────────────────────────────────

    def _abrir_gestor_proyectos(self, al_inicio: bool = False) -> None:
        """Muestra el gestor de proyectos (al inicio y desde el menú)."""
        if not al_inicio and not self._confirmar_cierre_proyecto():
            return
        dialogo = DialogoGestorProyectos(
            self._gestor, self._config, self, al_inicio=al_inicio)
        dialogo.exec()

        # Si se eliminó el proyecto abierto actualmente, cerrar su vista.
        activo = self._gestor.proyecto_activo
        if activo is not None and str(activo.ruta) in dialogo.rutas_eliminadas:
            self._gestor.cerrar_proyecto()
            self._limpiar_ui_sin_proyecto()

        if dialogo.proyecto is not None:
            self._cargar_proyecto_en_ui(dialogo.proyecto)
            self._config.agregar_proyecto_reciente(str(dialogo.proyecto.ruta))
            self._barra_estado.mostrar_mensaje(
                f"Proyecto «{dialogo.proyecto.nombre}» abierto.")

    def _limpiar_ui_sin_proyecto(self) -> None:
        """Deja la interfaz sin proyecto cargado."""
        self._panel1.cerrar_todas_pestanas()
        self._panel2.cerrar_todas_pestanas()
        self._panel3.cerrar_todas_pestanas()
        self._explorador.limpiar()
        self._panel_metadatos.mostrar_item(None)
        self.setWindowTitle(NOMBRE_APP)

    def _nuevo_proyecto(self) -> None:
        if not self._confirmar_cierre_proyecto():
            return
        dialogo = DialogoNuevoProyecto(self)
        if dialogo.exec():
            try:
                proyecto = self._gestor.nuevo_proyecto(
                    nombre=dialogo.nombre_proyecto,
                    ruta=dialogo.ruta_destino,
                    autor=dialogo.nombre_autor,
                )
                self._cargar_proyecto_en_ui(proyecto)
                self._config.agregar_proyecto_reciente(str(proyecto.ruta))
                self._barra_estado.mostrar_mensaje(
                    f"Proyecto «{proyecto.nombre}» creado correctamente."
                )
            except Exception as e:
                self._mostrar_error("Error al crear proyecto", str(e))

    def _abrir_proyecto(self) -> None:
        if not self._confirmar_cierre_proyecto():
            return
        ruta = QFileDialog.getExistingDirectory(
            self, "Abrir proyecto existente", str(Path.home())
        )
        if not ruta:
            return
        try:
            proyecto = self._gestor.abrir_proyecto(Path(ruta))
            self._cargar_proyecto_en_ui(proyecto)
            self._config.agregar_proyecto_reciente(ruta)
            self._config.ultimo_proyecto = ruta
            self._barra_estado.mostrar_mensaje(
                f"Proyecto «{proyecto.nombre}» abierto."
            )
        except FileNotFoundError:
            self._mostrar_error(
                "Proyecto no encontrado",
                f"No se encontró un proyecto Typoo válido en:\n{ruta}",
            )
        except Exception as e:
            self._mostrar_error("Error al abrir proyecto", str(e))

    def _cargar_proyecto_en_ui(self, proyecto: Proyecto) -> None:
        """Actualiza todos los widgets con el proyecto cargado."""
        self._panel1.cerrar_todas_pestanas()
        self._panel2.cerrar_todas_pestanas()
        self._panel3.cerrar_todas_pestanas()
        self._explorador.cargar_proyecto(proyecto)
        self._panel_metadatos.establecer_proyecto(proyecto)
        self._panel_metadatos.mostrar_item(None)
        self._panel_tramas.establecer_proyecto(proyecto)
        self.setWindowTitle(f"{proyecto.nombre} — {NOMBRE_APP}")
        self._barra_estado.actualizar_archivo(proyecto.nombre)

    def _al_crear_elemento(self, item, padre_id: str) -> None:
        """Refresca los paneles que dependen del catálogo de elementos."""
        self._panel_metadatos.refrescar()
        self._panel_tramas.refrescar()
        self._aplicar_nombres_editores()

    def _al_reorganizar(self, item_id: str) -> None:
        """Tras reordenar en el explorador, el orden de lectura puede cambiar."""
        self._panel_tramas.refrescar()
        self._aplicar_nombres_editores()

    # ─── Guardado ─────────────────────────────────────────────────────────────

    def _guardar_activo(self) -> None:
        panel = self._panel_activo()
        if panel:
            exito = panel.guardar_editor_activo(self._gestor.guardar_documento)
            if exito:
                self._barra_estado.mostrar_mensaje("Guardado correctamente.")
            else:
                self._barra_estado.mostrar_mensaje("No hay documento activo para guardar.")

    def _guardar_todos(self) -> None:
        for panel in (self._panel1, self._panel2, self._panel3):
            panel.guardar_todos(self._gestor.guardar_documento)
        if self._gestor.hay_proyecto:
            self._gestor.guardar_proyecto()

    # ─── Exportación ──────────────────────────────────────────────────────────

    def _exportar(self) -> None:
        if not self._gestor.hay_proyecto:
            self._mostrar_advertencia("Sin proyecto", "Abre un proyecto para exportarlo.")
            return

        proyecto = self._gestor.proyecto_activo
        dialogo = DialogoExportar(proyecto.nombre, self)
        if dialogo.exec():
            self._guardar_todos()
            ruta = dialogo.ruta_destino
            fmt  = dialogo.formato

            exito = False
            error_dep: str = ""
            if fmt == "docx":
                try:
                    import docx  # noqa: F401
                except ImportError:
                    error_dep = "pip install python-docx"
                else:
                    from exporters.exportador_docx import ExportadorDocx
                    exito = ExportadorDocx.exportar(proyecto, ruta, dialogo.incluir_portada)
            elif fmt == "pdf":
                try:
                    import reportlab  # noqa: F401
                except ImportError:
                    error_dep = "pip install reportlab"
                else:
                    from exporters.exportador_pdf import ExportadorPdf
                    exito = ExportadorPdf.exportar(proyecto, ruta)
            elif fmt == "txt":
                from exporters.exportador_txt import ExportadorTxt
                exito = ExportadorTxt.exportar(proyecto, ruta)

            if error_dep:
                self._mostrar_error(
                    "Dependencia no instalada",
                    f"Para exportar a este formato es necesario instalar una librería.\n\n"
                    f"Ejecuta en la terminal:\n    {error_dep}"
                )
            elif exito:
                QMessageBox.information(
                    self, "Exportación completada",
                    f"Manuscrito exportado correctamente:\n{ruta}"
                )
            else:
                self._mostrar_error(
                    "Error al exportar",
                    "Ocurrió un error durante la exportación.\n"
                    "Revisa el log de la aplicación para más detalles."
                )

    # ─── Apertura de documentos en el editor ──────────────────────────────────

    def _abrir_item_en_editor(self, item: ItemProyecto) -> None:
        if not item.ruta_relativa:
            return
        # Las carpetas (secciones como «Notas e investigación») no son documentos:
        # no deben abrirse como una pestaña de edición.
        if item.tipo in (TipoElemento.CARPETA, TipoElemento.PROYECTO):
            return
        # Un documento solo puede estar abierto en un área: si ya lo está, se activa.
        if self._activar_item_abierto(item):
            return
        contenido = self._gestor.leer_documento(item)
        editor = self._panel1.abrir_documento(item, contenido)
        editor.cursorPositionChanged.connect(
            lambda: self._actualizar_posicion_cursor(editor)
        )
        editor.tamano_zoom_cambiado.connect(self._al_zoom_editor)
        editor.establecer_nombres(self._nombres_dossier())
        self._panel_metadatos.mostrar_item(item)
        self._barra_estado.actualizar_archivo(item.nombre)

    def _al_seleccionar_item(self, item: ItemProyecto) -> None:
        pass  # La selección en el árbol no cambia el panel de detalles (lo hace la pestaña con foco)

    def _al_cambiar_editor(self, editor, panel=None) -> None:
        # El panel de Detalles se sincroniza vía item_activo_cambiado; aquí
        # solo actualizamos el conteo de palabras de la barra de estado.
        self._barra_estado.actualizar_palabras(editor.contar_palabras())

    def _al_documento_modificado(self, nombre: str, modificado: bool) -> None:
        self._barra_estado.actualizar_modificado(modificado)

    def _actualizar_posicion_cursor(self, editor) -> None:
        cursor = editor.textCursor()
        linea  = cursor.blockNumber() + 1
        col    = cursor.columnNumber() + 1
        self._barra_estado.actualizar_posicion(linea, col)

    def _persistir_metadatos(self) -> None:
        """Guarda el proyecto para conservar los metadatos editados."""
        if self._gestor.hay_proyecto:
            self._gestor.guardar_proyecto()
            self._barra_estado.mostrar_mensaje("Detalles guardados.", 1500)

    # ─── Acciones de edición ──────────────────────────────────────────────────

    def _deshacer(self) -> None:
        editor = self._editor_activo()
        if editor:
            editor.undo()

    def _rehacer(self) -> None:
        editor = self._editor_activo()
        if editor:
            editor.redo()

    def _cortar(self) -> None:
        editor = self._editor_activo()
        if editor:
            editor.cut()

    def _copiar(self) -> None:
        editor = self._editor_activo()
        if editor:
            editor.copy()

    def _pegar(self) -> None:
        editor = self._editor_activo()
        if editor:
            editor.paste()

    # ─── Acciones de formato ──────────────────────────────────────────────────

    def _formato(self, inicio: str, fin: str) -> None:
        editor = self._editor_activo()
        if editor:
            editor.insertar_formato(inicio, fin)

    def _insertar_encabezado(self, nivel: int) -> None:
        editor = self._editor_activo()
        if editor:
            editor.insertar_encabezado(nivel)

    def _lista_vinetas(self) -> None:
        editor = self._editor_activo()
        if editor:
            editor.alternar_lista_vinetas()

    def _lista_numerada(self) -> None:
        editor = self._editor_activo()
        if editor:
            editor.alternar_lista_numerada()

    def _sangrar(self) -> None:
        editor = self._editor_activo()
        if editor:
            editor.aumentar_sangria()

    def _desangrar(self) -> None:
        editor = self._editor_activo()
        if editor:
            editor.disminuir_sangria()

    def _cambiar_fuente_editor(self, familia: str) -> None:
        self._config.fuente_familia = familia
        self._aplicar_fuente_editores()

    def _cambiar_tamano_editor(self, tamano: int) -> None:
        self._config.fuente_tamanio = tamano
        self._aplicar_fuente_editores()

    def _al_zoom_editor(self, tamano: int) -> None:
        """Zoom con Ctrl+rueda: persistir y reflejar en la barra de formato."""
        self._config.fuente_tamanio = tamano
        self._barra_formato.reflejar_fuente(self._config.fuente_familia, tamano)

    def _insertar_cita(self) -> None:
        editor = self._editor_activo()
        if editor:
            editor.insertar_cita()

    def _insertar_separador(self) -> None:
        editor = self._editor_activo()
        if editor:
            editor.insertar_separador()

    def _insertar_enlace(self) -> None:
        editor = self._editor_activo()
        if editor:
            editor.insertar_enlace()

    def _insertar_texto(self, texto: str) -> None:
        editor = self._editor_activo()
        if editor:
            cursor = editor.textCursor()
            cursor.insertText(texto)
            editor.setTextCursor(cursor)

    # ─── Búsqueda ─────────────────────────────────────────────────────────────

    def _abrir_buscar(self) -> None:
        if self._dialogo_buscar is None:
            self._dialogo_buscar = DialogoBuscarReemplazar(self)
            self._dialogo_buscar.buscar_solicitado.connect(self._buscar)
            self._dialogo_buscar.buscar_siguiente.connect(self._siguiente_coincidencia)
            self._dialogo_buscar.buscar_anterior.connect(self._anterior_coincidencia)
            self._dialogo_buscar.reemplazar_solicitado.connect(self._reemplazar)
            self._dialogo_buscar.reemplazar_todo.connect(self._reemplazar_todo)
            self._dialogo_buscar.buscar_proyecto.connect(self._buscar_en_proyecto)

        # Pre-rellenar con la selección actual
        editor = self._editor_activo()
        if editor:
            seleccion = editor.textCursor().selectedText()
            if seleccion:
                self._dialogo_buscar.establecer_texto_busqueda(seleccion)

        self._dialogo_buscar.show()
        self._dialogo_buscar.raise_()

    def _buscar(self, patron: str, regex: bool, ignorar: bool) -> None:
        editor = self._editor_activo()
        if not editor or not patron:
            return
        texto = editor.toPlainText()
        self._busqueda_actual = ServicioBusqueda.buscar_en_texto(
            texto, patron, regex, ignorar
        )
        self._patron_busqueda = patron
        self._indice_busqueda = 0
        if self._busqueda_actual:
            self._resaltar_coincidencia(editor, 0)
            msg = f"{len(self._busqueda_actual)} coincidencia(s) encontrada(s)."
        else:
            msg = "No se encontraron coincidencias."
        if self._dialogo_buscar:
            self._dialogo_buscar.mostrar_resultado(msg)

    def _siguiente_coincidencia(self) -> None:
        if not self._busqueda_actual:
            return
        self._indice_busqueda = (self._indice_busqueda + 1) % len(self._busqueda_actual)
        editor = self._editor_activo()
        if editor:
            self._resaltar_coincidencia(editor, self._indice_busqueda)

    def _anterior_coincidencia(self) -> None:
        if not self._busqueda_actual:
            return
        self._indice_busqueda = (self._indice_busqueda - 1) % len(self._busqueda_actual)
        editor = self._editor_activo()
        if editor:
            self._resaltar_coincidencia(editor, self._indice_busqueda)

    def _resaltar_coincidencia(self, editor, indice: int) -> None:
        inicio, fin = self._busqueda_actual[indice]
        cursor = editor.textCursor()
        cursor.setPosition(inicio)
        cursor.setPosition(fin, QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        editor.ensureCursorVisible()

    def _reemplazar(self, patron: str, reemplazo: str, regex: bool, ignorar: bool) -> None:
        editor = self._editor_activo()
        if not editor:
            return
        texto_nuevo = ServicioBusqueda.reemplazar_en_texto(
            editor.toPlainText(), patron, reemplazo, regex, ignorar, solo_primera=True
        )
        editor.setPlainText(texto_nuevo)

    def _reemplazar_todo(self, patron: str, reemplazo: str, regex: bool, ignorar: bool) -> None:
        editor = self._editor_activo()
        if not editor:
            return
        texto_nuevo = ServicioBusqueda.reemplazar_en_texto(
            editor.toPlainText(), patron, reemplazo, regex, ignorar
        )
        editor.setPlainText(texto_nuevo)
        if self._dialogo_buscar:
            self._dialogo_buscar.mostrar_resultado("Reemplazo completado.")

    def _buscar_en_proyecto(self, patron: str, regex: bool, ignorar: bool) -> None:
        if not self._gestor.hay_proyecto:
            return
        resultados = ServicioBusqueda.buscar_en_proyecto(
            self._gestor.proyecto_activo.ruta, patron, regex, ignorar
        )
        msg = (
            f"{len(resultados)} coincidencia(s) en todo el proyecto."
            if resultados else
            "Sin coincidencias en el proyecto."
        )
        if self._dialogo_buscar:
            self._dialogo_buscar.mostrar_resultado(msg)
        self._barra_estado.mostrar_mensaje(msg, 5000)

    # ─── Gestión de paneles ───────────────────────────────────────────────────

    def _panel_activo(self) -> Optional[PanelPestanas]:
        """Devuelve el panel que tiene el foco actualmente."""
        for panel in (self._panel1, self._panel2, self._panel3):
            editor = panel.editor_activo()
            if editor and editor.hasFocus():
                return panel
        return self._panel1 if not self._panel1.isHidden() else None

    def _editor_activo(self):
        panel = self._panel_activo()
        return panel.editor_activo() if panel else None

    def _alternar_panel(self, widget: QWidget, accion: QAction) -> None:
        if widget.isHidden():
            widget.show()
            accion.setChecked(True)
        else:
            widget.hide()
            accion.setChecked(False)

    def _alternar_panel_explorador(self) -> None:
        if self._explorador.isHidden():
            self._explorador.show()
            self._ac_explorador.setChecked(True)
        else:
            self._explorador.hide()
            self._ac_explorador.setChecked(False)

    # ─── Creación de elementos desde menú ────────────────────────────────────

    def _crear_elemento(self, tipo: TipoElemento) -> None:
        from models.proyecto import (
            ROL_MANUSCRITO, ROL_PERSONAJES, ROL_UBICACIONES, ROL_NOTAS,
        )
        if not self._gestor.hay_proyecto:
            self._mostrar_advertencia("Sin proyecto", "Abre un proyecto primero.")
            return
        proyecto = self._gestor.proyecto_activo

        # Determinar el contenedor de destino según el tipo y el contexto.
        padre = None
        if tipo == TipoElemento.CAPITULO:
            padre = proyecto.carpeta_por_rol(ROL_MANUSCRITO)
        elif tipo == TipoElemento.ESCENA:
            manuscrito = proyecto.carpeta_por_rol(ROL_MANUSCRITO)
            capitulos = sorted(
                [h for h in manuscrito.hijos if h.tipo == TipoElemento.CAPITULO],
                key=lambda c: c.orden,
            ) if manuscrito else []
            if not capitulos:
                self._mostrar_advertencia(
                    "Sin capítulo",
                    "Crea primero un capítulo en el Manuscrito para añadir escenas.",
                )
                return
            padre = self._elegir_capitulo(capitulos, proyecto)
            if padre is None:
                return  # el usuario canceló
        elif tipo == TipoElemento.PERSONAJE:
            padre = proyecto.carpeta_por_rol(ROL_PERSONAJES)
        elif tipo == TipoElemento.UBICACION:
            padre = proyecto.carpeta_por_rol(ROL_UBICACIONES)
        elif tipo == TipoElemento.NOTA:
            padre = proyecto.carpeta_por_rol(ROL_NOTAS)

        if padre is None:
            padre = proyecto.raiz
        self._explorador._crear_elemento(tipo, padre, "")

    def _elegir_capitulo(self, capitulos, proyecto) -> Optional[ItemProyecto]:
        """Pregunta a qué capítulo añadir la escena (predefine el contextual)."""
        if len(capitulos) == 1:
            return capitulos[0]
        defecto = self._capitulo_destino(proyecto)
        idx = next((i for i, c in enumerate(capitulos)
                    if defecto and c.id == defecto.id), 0)
        nombres = [c.nombre for c in capitulos]
        nombre, ok = QInputDialog.getItem(
            self, "Nueva escena", "Añadir al capítulo:", nombres, idx, False
        )
        if not ok:
            return None
        return capitulos[nombres.index(nombre)]

    def _capitulo_destino(self, proyecto) -> Optional[ItemProyecto]:
        """Capítulo donde crear una escena: el seleccionado o el último del manuscrito."""
        from models.proyecto import ROL_MANUSCRITO
        # 1) Si hay un capítulo (o una escena dentro de uno) seleccionado, usarlo.
        sel = self._explorador.item_seleccionado()
        nodo = sel
        while nodo is not None:
            if nodo.tipo == TipoElemento.CAPITULO:
                return nodo
            nodo = proyecto.buscar_item(nodo.padre_id) if nodo.padre_id else None
        # 2) Si no, el último capítulo del manuscrito.
        manuscrito = proyecto.carpeta_por_rol(ROL_MANUSCRITO)
        if manuscrito:
            capitulos = [h for h in manuscrito.hijos if h.tipo == TipoElemento.CAPITULO]
            if capitulos:
                return sorted(capitulos, key=lambda c: c.orden)[-1]
        return None

    # ─── Tema ─────────────────────────────────────────────────────────────────

    def _alternar_tema(self) -> None:
        nuevo_tema = GestorTemas.alternar(self._config.tema)
        self._config.tema = nuevo_tema
        GestorTemas.aplicar(nuevo_tema)
        # Actualizar resaltador de todos los editores abiertos
        oscuro = nuevo_tema == Tema.OSCURO
        for panel in (self._panel1, self._panel2, self._panel3):
            for i in range(panel.count()):
                editor = panel.widget(i)
                if hasattr(editor, "aplicar_tema"):
                    editor.aplicar_tema(oscuro)
        self._barra_formato.aplicar_tema(oscuro)
        self._sincronizar_iconos_titulo()
        self._actualizar_etiqueta_tema()

    def _actualizar_etiqueta_tema(self) -> None:
        if self._config.tema == Tema.OSCURO:
            self._ac_tema.setText("Cambiar a tema claro")
        else:
            self._ac_tema.setText("Cambiar a tema oscuro")

    def _aplicar_tema_inicial(self) -> None:
        GestorTemas.aplicar(self._config.tema)
        self._sincronizar_iconos_titulo()

    def _sincronizar_iconos_titulo(self) -> None:
        """Recolorea los iconos de la barra de título según el tema activo."""
        if hasattr(self, "_barra_titulo"):
            oscuro = self._config.tema == Tema.OSCURO
            self._barra_titulo.aplicar_tema("#E7E7EA" if oscuro else "#33343A")

    def _aplicar_icono(self) -> None:
        """Establece el icono de la ventana (y de la barra de título) desde el
        SVG del proyecto."""
        if RUTA_ICONO.exists():
            icono = QIcon(str(RUTA_ICONO))
            self.setWindowIcon(icono)
            if hasattr(self, "_barra_titulo"):
                self._barra_titulo.establecer_icono(icono)

    # ─── Marco propio (sin barra de título del sistema) en Linux ──────────────

    def _configurar_marco_sin_borde(self) -> None:
        """En Linux, oculta la barra de título del sistema y habilita el
        redimensionado por los bordes; nuestra BarraTitulo la sustituye."""
        if not ES_LINUX:
            return
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self._redimensionador = RedimensionadorSinBorde(self)
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self._redimensionador)

    def changeEvent(self, evento) -> None:  # type: ignore[override]
        super().changeEvent(evento)
        if evento.type() == QEvent.Type.WindowStateChange and \
                hasattr(self, "_barra_titulo"):
            self._barra_titulo.actualizar_boton_maximizar()

    # ─── Pantalla completa / modo concentración ───────────────────────────────

    def _alternar_pantalla_completa(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _alternar_tramas(self) -> None:
        """Muestra u oculta el visor de tramas (banda inferior)."""
        mostrar = self._ac_tramas.isChecked()
        self._dock_tramas.setVisible(mostrar)
        if mostrar:
            self._panel_tramas.refrescar()

    def _alternar_concentracion(self) -> None:
        """Modo concentración: deja únicamente el texto centrado en pantalla.

        Oculta la barra de menú, la de estado, la barra de edición y todos los
        paneles (explorador, detalles, tramas, asistente de IA). Muestra solo un
        pequeño aviso centrado arriba: «Pulsa Esc para salir»."""
        if self._ac_concentracion.isChecked():
            self._entrar_concentracion()
        else:
            self._salir_concentracion()

    def _entrar_concentracion(self) -> None:
        # Recordar el estado visible actual para restaurarlo al salir.
        self._estado_concentracion = {
            "explorador": self._explorador.isVisible(),
            "metadatos": self._panel_metadatos.isVisible(),
            "formato": self._barra_superior.isVisible(),
            "tramas": self._dock_tramas.isVisible(),
            "asistente": self._dock_asistente.isVisible(),
        }
        # Ocultar todo menos el texto.
        self._explorador.hide()
        self._panel_metadatos.hide()
        self._barra_superior.hide()
        self._dock_tramas.hide()
        self._dock_asistente.hide()
        self.menuBar().hide()
        self._barra_estado.hide()
        for panel in (self._panel1, self._panel2, self._panel3):
            panel.establecer_modo_concentracion(True)
        # Sincronizar acciones de menú (por si se reabre desde otra vía).
        self._ac_explorador.setChecked(False)
        self._ac_detalles.setChecked(False)
        self._ac_tramas.setChecked(False)

        self._mostrar_hint_concentracion()
        if self._atajo_salir_concentracion is None:
            self._atajo_salir_concentracion = QShortcut(
                QKeySequence(Qt.Key.Key_Escape), self
            )
            self._atajo_salir_concentracion.activated.connect(
                self._salir_por_atajo
            )
        self._atajo_salir_concentracion.setEnabled(True)
        self.showFullScreen()

    def _salir_concentracion(self) -> None:
        estado = getattr(self, "_estado_concentracion", None) or {}
        self.showNormal()
        self.menuBar().show()
        self._barra_estado.show()
        for panel in (self._panel1, self._panel2, self._panel3):
            panel.establecer_modo_concentracion(False)
        self._explorador.setVisible(estado.get("explorador", True))
        self._panel_metadatos.setVisible(estado.get("metadatos", True))
        self._barra_superior.setVisible(estado.get("formato", True))
        self._dock_tramas.setVisible(estado.get("tramas", False))
        self._dock_asistente.setVisible(estado.get("asistente", False))
        self._ac_explorador.setChecked(estado.get("explorador", True))
        self._ac_detalles.setChecked(estado.get("metadatos", True))
        self._ac_tramas.setChecked(estado.get("tramas", False))
        if self._atajo_salir_concentracion is not None:
            self._atajo_salir_concentracion.setEnabled(False)
        if self._hint_concentracion is not None:
            self._hint_concentracion.hide()

    def _salir_por_atajo(self) -> None:
        """Salir del modo concentración con Esc (actualiza la acción del menú)."""
        if self._ac_concentracion.isChecked():
            self._ac_concentracion.setChecked(False)
            self._salir_concentracion()

    def _mostrar_hint_concentracion(self) -> None:
        if self._hint_concentracion is None:
            hint = QLabel("Pulsa Esc para salir", self)
            hint.setObjectName("HintConcentracion")
            hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hint.setStyleSheet(
                "#HintConcentracion {"
                " background: rgba(20, 20, 22, 180);"
                " color: #F2F2F7;"
                " border-radius: 11px;"
                " padding: 5px 14px;"
                " font-size: 12px; }"
            )
            hint.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self._hint_concentracion = hint
        self._hint_concentracion.show()
        self._hint_concentracion.adjustSize()
        self._hint_concentracion.raise_()
        self._posicionar_hint()

    def _posicionar_hint(self) -> None:
        hint = getattr(self, "_hint_concentracion", None)
        if hint is None or not hint.isVisible():
            return
        hint.adjustSize()
        x = (self.width() - hint.width()) // 2
        hint.move(max(0, x), 12)

    def resizeEvent(self, evento) -> None:  # type: ignore[override]
        super().resizeEvent(evento)
        self._posicionar_hint()

    # ─── Respaldo ─────────────────────────────────────────────────────────────

    def _crear_respaldo(self) -> None:
        if not self._gestor.hay_proyecto:
            self._mostrar_advertencia("Sin proyecto", "Abre un proyecto primero.")
            return
        self._guardar_todos()
        ruta_custom = self._config.ruta_respaldos
        ruta_destino = Path(ruta_custom) if ruta_custom else None
        exito = GestorArchivos.crear_respaldo(
            self._gestor.proyecto_activo.ruta,
            self._config.max_respaldos,
            ruta_destino,
        )
        if exito:
            self._barra_estado.mostrar_mensaje("Respaldo creado correctamente.")
        else:
            self._mostrar_error("Error", "No se pudo crear el respaldo.")

    # ─── Acerca de ────────────────────────────────────────────────────────────

    def _acerca_de(self) -> None:
        from core.constantes import AUTOR_APP, LICENCIA_APP, DESCRIPCION
        QMessageBox.about(
            self,
            f"Acerca de {NOMBRE_APP}",
            f"<h2>{NOMBRE_APP} {VERSION_APP}</h2>"
            f"<p>{DESCRIPCION}</p>"
            f"<p><b>Autoría:</b> {AUTOR_APP}</p>"
            f"<p><b>Licencia:</b> {LICENCIA_APP}</p>"
            "<p>Suite profesional de escritura de novelas "
            "construida con Python y PySide6.</p>",
        )

    # ─── Preferencias ─────────────────────────────────────────────────────────

    def _abrir_preferencias(self, pestaña: str = "general") -> None:
        dialogo = DialogoPreferencias(self, pestaña=pestaña)
        if dialogo.exec():
            self._autoguardado.detener()
            self._autoguardado.iniciar()
            self._reiniciar_timer_respaldo()
            self._aplicar_fuente_editores()
            # Si la IA se desactivó, ocultar su panel.
            if not self._config.ia_habilitada and self._dock_asistente.isVisible():
                self._dock_asistente.hide()
            self._actualizar_banner_ia()
            self._barra_estado.mostrar_mensaje("Preferencias guardadas.")

    # ─── Asistente de IA ──────────────────────────────────────────────────────

    def _alternar_asistente(self) -> None:
        """Muestra/oculta el panel del asistente (menú Ver)."""
        mostrar = self._ac_asistente.isChecked()
        if mostrar and not self._config.ia_habilitada:
            # Aún no configurado: abrir Preferencias en la pestaña de IA.
            self._abrir_preferencias(pestaña="ia")
            if not self._config.ia_habilitada:
                self._ac_asistente.setChecked(False)
                return
        self._dock_asistente.setVisible(mostrar)
        if mostrar:
            self._dock_asistente.raise_()
            self._panel_asistente.poner_foco()

    def _al_cambiar_visibilidad_asistente(self, visible: bool) -> None:
        """Mantiene sincronizada la marca del menú Ver con el dock."""
        if hasattr(self, "_ac_asistente"):
            self._ac_asistente.setChecked(visible)

    def _reescribir_seleccion(self, intencion_id: str) -> None:
        if not self._config.ia_habilitada:
            return
        editor = self._editor_activo()
        if not editor:
            self._mostrar_advertencia("Sin documento", "Abre un documento primero.")
            return
        cursor = editor.textCursor()
        texto = cursor.selectedText()
        if not texto.strip():
            self._mostrar_advertencia(
                "Sin selección", "Selecciona el texto que quieres reescribir.")
            return
        # selectedText() usa U+2029 como separador de párrafo; normalizar a \n.
        texto = texto.replace(" ", "\n")

        from ai.proveedores import crear_proveedor_desde_config
        from ui.dialogos.resultado_ia import DialogoResultadoIA

        proveedor = crear_proveedor_desde_config(self._config)
        if intencion_id == "correccion":
            from ai.tareas import mensajes_correccion
            mensajes = mensajes_correccion(texto)
            titulo = "Corregir ortografía y gramática"
        else:
            from ai.tareas import intencion_por_id, mensajes_reescritura
            intencion = intencion_por_id(intencion_id)
            mensajes = mensajes_reescritura(texto, intencion)
            titulo = f"Reescribir: {intencion.etiqueta}"
        dialogo = DialogoResultadoIA(
            proveedor, mensajes, texto, titulo=titulo, parent=self)
        if dialogo.exec() and dialogo.accion and dialogo.texto_resultado.strip():
            cur = editor.textCursor()
            if dialogo.accion == "reemplazar":
                cur.insertText(dialogo.texto_resultado)
            elif dialogo.accion == "insertar":
                cur.setPosition(cur.selectionEnd())
                cur.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                cur.insertText("\n\n" + dialogo.texto_resultado)
            editor.setTextCursor(cur)

    # -- Dossier asistido por IA ---------------------------------------------

    def _proveedor_ia(self):
        from ai.proveedores import crear_proveedor_desde_config
        return crear_proveedor_desde_config(self._config)

    def _item_editor_activo(self):
        editor = self._editor_activo()
        if not editor:
            return None, None
        return editor, getattr(editor, "item", None)

    def _escenas_de_personaje(self, personaje_id: str, max_total: int = 6000) -> str:
        """Texto de las escenas donde aparece el personaje (por metadatos)."""
        if not self._gestor.hay_proyecto:
            return ""
        proyecto = self._gestor.proyecto_activo
        partes: list[str] = []
        total = 0
        for escena in proyecto.escenas_en_orden():
            meta = escena.metadatos or {}
            refs = meta.get("personajes") or []
            relacionada = (isinstance(refs, list) and personaje_id in refs) \
                or meta.get("pov") == personaje_id
            if not relacionada:
                continue
            try:
                texto = (self._gestor.leer_documento(escena) or "").strip()
            except Exception:
                texto = ""
            if not texto:
                continue
            bloque = f"[{escena.nombre}]\n{texto[:700]}"
            if total + len(bloque) > max_total:
                partes.append("[…]")
                break
            partes.append(bloque)
            total += len(bloque)
        return "\n\n".join(partes)

    def _texto_de_item(self, item) -> str:
        """Texto de un documento: del editor abierto si lo está, o del disco."""
        loc = self._localizar_item_abierto(item.id)
        if loc:
            _panel, _num, indice = loc
            editor = loc[0].widget(indice)
            if editor is not None:
                return editor.toPlainText()
        try:
            return self._gestor.leer_documento(item) or ""
        except Exception:
            return ""

    def _al_accion_ia_explorador(self, accion: str, item) -> None:
        """Despacha las acciones de dossier lanzadas desde el explorador."""
        if accion == "sinopsis":
            self._ia_sinopsis(item)
        elif accion == "ficha":
            self._ia_ficha(item)
        elif accion == "coherencia":
            self._ia_coherencia(item)
        elif accion == "coherencia_cap":
            self._ia_coherencia_capitulo(item)

    def _ia_sinopsis(self, item=None) -> None:
        if not self._config.ia_habilitada:
            return
        if item is None:
            item = self._item_editor_activo()[1]
        if not item:
            self._mostrar_advertencia("Sin documento", "Abre o selecciona una escena o capítulo.")
            return
        if item.tipo not in (TipoElemento.ESCENA, TipoElemento.CAPITULO):
            self._mostrar_advertencia(
                "No aplicable", "La sinopsis se genera para escenas o capítulos.")
            return
        texto = self._texto_de_item(item).strip()
        if not texto:
            self._mostrar_advertencia("Vacío", "El documento no tiene texto.")
            return
        from ai.contexto import truncar
        from ai.tareas import mensajes_sinopsis
        from ui.dialogos.resultado_ia import DialogoResultadoIA
        mensajes = mensajes_sinopsis(item.nombre, truncar(texto, 8000))
        dialogo = DialogoResultadoIA(
            self._proveedor_ia(), mensajes, truncar(texto, 4000),
            titulo=f"Sinopsis: {item.nombre}",
            acciones=[("aplicar", "Usar como resumen")],
            etiqueta_original="Escena", etiqueta_sugerencia="Sinopsis propuesta",
            parent=self)
        if dialogo.exec() and dialogo.accion == "aplicar" and dialogo.texto_resultado.strip():
            item.metadatos["resumen"] = dialogo.texto_resultado.strip()
            self._persistir_metadatos()
            self._panel_metadatos.mostrar_item(item)
            self._barra_estado.mostrar_mensaje("Resumen actualizado con la sinopsis.", 3000)

    def _ia_ficha(self, item=None) -> None:
        if not self._config.ia_habilitada:
            return
        if item is None:
            item = self._item_editor_activo()[1]
        if not item or item.tipo not in (TipoElemento.PERSONAJE, TipoElemento.UBICACION):
            self._mostrar_advertencia(
                "No aplicable", "Selecciona o abre un personaje o una ubicación.")
            return
        from core.metadatos import etiqueta_tipo
        from ai.contexto import truncar, ficha_a_texto
        from ai.tareas import campos_ficha, mensajes_ficha, parsear_campos
        from ui.dialogos.resultado_ia import DialogoResultadoIA

        descripcion = self._texto_de_item(item).strip()
        partes = [f"Ficha actual:\n{ficha_a_texto(item)}"]
        if descripcion:
            partes.append(f"Descripción / notas:\n{descripcion}")
        if item.tipo == TipoElemento.PERSONAJE:
            escenas = self._escenas_de_personaje(item.id, max_total=4000)
            if escenas:
                partes.append(f"Apariciones en escenas:\n{escenas}")
        contexto = truncar("\n\n".join(partes), 8000)
        campos = campos_ficha(item.tipo)
        mensajes = mensajes_ficha(etiqueta_tipo(item.tipo), item.nombre, campos, contexto)
        dialogo = DialogoResultadoIA(
            self._proveedor_ia(), mensajes, ficha_a_texto(item),
            titulo=f"Ficha sugerida: {item.nombre}",
            acciones=[("aplicar", "Aplicar a campos vacíos")],
            etiqueta_original="Ficha actual", etiqueta_sugerencia="Sugerencia",
            parent=self)
        if dialogo.exec() and dialogo.accion == "aplicar" and dialogo.texto_resultado.strip():
            propuesto = parsear_campos(dialogo.texto_resultado, campos)
            aplicados = 0
            for clave, valor in propuesto.items():
                actual = item.metadatos.get(clave)
                if not (isinstance(actual, str) and actual.strip()):
                    item.metadatos[clave] = valor
                    aplicados += 1
            if aplicados:
                self._persistir_metadatos()
                self._panel_metadatos.mostrar_item(item)
                self._barra_estado.mostrar_mensaje(
                    f"Ficha actualizada: {aplicados} campo(s) vacío(s) rellenado(s).", 4000)
            else:
                self._mostrar_advertencia(
                    "Sin cambios",
                    "No había campos vacíos que rellenar (los ya escritos se conservan).")

    def _ia_coherencia(self, item=None) -> None:
        if not self._config.ia_habilitada:
            return
        if item is None:
            item = self._item_editor_activo()[1]
        if not item or item.tipo != TipoElemento.PERSONAJE:
            self._mostrar_advertencia(
                "No aplicable", "Selecciona o abre un personaje para revisar su coherencia.")
            return
        from ai.contexto import truncar, ficha_a_texto
        from ai.tareas import mensajes_coherencia
        from ui.dialogos.resultado_ia import DialogoResultadoIA

        escenas = self._escenas_de_personaje(item.id, max_total=6000)
        if not escenas.strip():
            self._mostrar_advertencia(
                "Sin escenas",
                "Este personaje no está vinculado a ninguna escena. Usa los campos "
                "«Personajes presentes» o «Punto de vista» de las escenas.")
            return
        mensajes = mensajes_coherencia(item.nombre, ficha_a_texto(item), truncar(escenas, 8000))
        dialogo = DialogoResultadoIA(
            self._proveedor_ia(), mensajes, ficha_a_texto(item),
            titulo=f"Coherencia: {item.nombre}",
            acciones=[("notas", "Enviar a Notas")],
            etiqueta_original="Ficha", etiqueta_sugerencia="Informe de coherencia",
            parent=self)
        if dialogo.exec() and dialogo.accion == "notas" and dialogo.texto_resultado.strip():
            self._guardar_en_notas(
                f"Coherencia de «{item.nombre}»\n\n{dialogo.texto_resultado.strip()}")

    def _texto_de_capitulo(self, capitulo, max_total: int = 8000) -> str:
        """Concatena el texto de las escenas de un capítulo, en orden."""
        partes: list[str] = []
        total = 0
        for hijo in sorted(capitulo.hijos, key=lambda h: h.orden):
            if hijo.tipo != TipoElemento.ESCENA:
                continue
            texto = self._texto_de_item(hijo).strip()
            if not texto:
                continue
            bloque = f"[{hijo.nombre}]\n{texto}"
            if total + len(bloque) > max_total:
                partes.append("[…]")
                break
            partes.append(bloque)
            total += len(bloque)
        return "\n\n".join(partes)

    def _ia_coherencia_capitulo(self, item=None) -> None:
        if not self._config.ia_habilitada:
            return
        if item is None:
            item = self._item_editor_activo()[1]
        if not item or item.tipo != TipoElemento.CAPITULO:
            self._mostrar_advertencia(
                "No aplicable", "Selecciona un capítulo para revisar su coherencia.")
            return
        texto = self._texto_de_capitulo(item)
        if not texto.strip():
            self._mostrar_advertencia(
                "Sin contenido", "El capítulo no tiene escenas con texto.")
            return
        from ai.tareas import mensajes_coherencia_capitulo
        from ui.dialogos.resultado_ia import DialogoResultadoIA
        mensajes = mensajes_coherencia_capitulo(item.nombre, texto)
        dialogo = DialogoResultadoIA(
            self._proveedor_ia(), mensajes, texto,
            titulo=f"Coherencia del capítulo: {item.nombre}",
            acciones=[("notas", "Enviar a Notas")],
            etiqueta_original="Capítulo", etiqueta_sugerencia="Informe de coherencia",
            parent=self)
        if dialogo.exec() and dialogo.accion == "notas" and dialogo.texto_resultado.strip():
            self._guardar_en_notas(
                f"Coherencia del capítulo «{item.nombre}»\n\n{dialogo.texto_resultado.strip()}")

    # ─── Guardar contenido generado en Notas ─────────────────────────────────

    def _guardar_en_notas(self, contenido: str) -> None:
        """Guarda el contenido como una nota nueva en «Notas e investigación».

        La nota se crea de inmediato con un título provisional derivado del
        propio texto; después, si el asistente de IA está disponible, se intenta
        refinar el título en segundo plano. Así la nota siempre se guarda aunque
        el modelo tarde o no esté disponible."""
        from models.proyecto import ROL_NOTAS
        if not self._gestor.hay_proyecto:
            self._mostrar_advertencia("Sin proyecto", "Abre un proyecto primero.")
            return
        proyecto = self._gestor.proyecto_activo
        notas = proyecto.carpeta_por_rol(ROL_NOTAS)
        if notas is None:
            self._mostrar_advertencia("Sin carpeta de notas",
                                      "El proyecto no tiene la sección de Notas.")
            return

        titulo = self._titulo_provisional(contenido)
        nota = self._gestor.crear_elemento(titulo, TipoElemento.NOTA, notas.id, "")
        if not nota:
            self._mostrar_advertencia("No se pudo guardar",
                                      "No fue posible crear la nota.")
            return
        self._gestor.guardar_documento(nota, contenido)
        self._explorador.refrescar()
        self._aplicar_nombres_editores()
        self._barra_estado.mostrar_mensaje(f"Guardado en Notas: «{titulo}».", 4000)

        # Refinar el título con IA (opcional, en segundo plano).
        if self._config.ia_habilitada:
            try:
                from ai.tareas import mensajes_titulo
                from ai.servicio import TrabajadorIA
                self._worker_titulo = TrabajadorIA(
                    self._proveedor_ia(), mensajes_titulo(contenido[:2000]),
                    max_tokens=48, parent=self)
                self._worker_titulo.terminado.connect(
                    lambda t, nid=nota.id: self._renombrar_nota_ia(nid, t))
                self._worker_titulo.start()
            except Exception:
                pass

    def _titulo_provisional(self, contenido: str) -> str:
        """Título a partir de la primera línea con texto del contenido."""
        for linea in (contenido or "").splitlines():
            linea = linea.strip().lstrip("#").strip().strip('"«»').strip()
            if linea:
                return linea[:70]
        return "Nota de IA"

    def _renombrar_nota_ia(self, nota_id: str, titulo: str) -> None:
        """Aplica el título generado por IA a una nota ya creada."""
        titulo = (titulo or "").strip().strip('"«»').strip()
        titulo = titulo.splitlines()[0][:70] if titulo else ""
        if not titulo:
            return
        if self._gestor.renombrar_elemento(nota_id, titulo):
            self._explorador.refrescar()
            self._aplicar_nombres_editores()
            self._barra_estado.mostrar_mensaje(f"Nota guardada como «{titulo}».", 4000)

    def _ia_tormenta(self) -> None:
        """Sugiere formas de continuar la historia a partir del punto actual."""
        if not self._config.ia_habilitada:
            return
        if not self._gestor.hay_proyecto:
            self._mostrar_advertencia("Sin proyecto", "Abre un proyecto primero.")
            return
        from ai.contexto import truncar
        from ui.dialogos.tormenta_ia import DialogoTormenta

        proyecto = self._gestor.proyecto_activo
        lineas = []
        for escena in proyecto.escenas_en_orden():
            resumen = (escena.metadatos or {}).get("resumen", "")
            lineas.append(f"- {escena.nombre}" + (f": {resumen}" if resumen else ""))
        esquema = "\n".join(lineas) or "(todavía no hay escenas)"
        tramas = ", ".join(t.nombre for t in proyecto.tramas) or "(sin tramas definidas)"

        partes = [f"Tramas: {tramas}", f"Escenas hasta ahora:\n{esquema}"]
        foco = ""
        editor, item = self._item_editor_activo()
        if item is not None and item.tipo == TipoElemento.ESCENA:
            texto = self._texto_de_item(item).strip()
            if texto:
                partes.append(f"Escena actual «{item.nombre}»:\n{truncar(texto, 2000)}")
                foco = f"cómo continuar tras «{item.nombre}»"
        contexto = truncar("\n\n".join(partes), 8000)

        dialogo = DialogoTormenta(self._proveedor_ia(), contexto, foco, parent=self)
        if not dialogo.exec() or not dialogo.texto_resultado.strip():
            return
        resultado = dialogo.texto_resultado.strip()
        if dialogo.accion == "insertar":
            destino = editor or self._editor_activo()
            if destino is not None:
                cur = destino.textCursor()
                cur.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                cur.insertText("\n\n" + resultado + "\n")
                destino.setTextCursor(cur)
                self._barra_estado.mostrar_mensaje("Idea insertada en el editor.", 3000)
        elif dialogo.accion == "notas":
            self._guardar_en_notas(f"Tormenta de ideas\n\n{resultado}")

    # ─── Cierre de la ventana ─────────────────────────────────────────────────

    def closeEvent(self, evento: QCloseEvent) -> None:
        hay_cambios = any(
            p.hay_cambios_pendientes()
            for p in (self._panel1, self._panel2, self._panel3)
        )
        if hay_cambios:
            resp = QMessageBox.question(
                self,
                "Cambios sin guardar",
                "Hay documentos con cambios sin guardar.\n¿Guardar antes de salir?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
            )
            if resp == QMessageBox.StandardButton.Cancel:
                evento.ignore()
                return
            if resp == QMessageBox.StandardButton.Save:
                self._guardar_todos()

        self._autoguardado.detener()
        self._guardar_geometria()
        self._config.sincronizar()
        # Retirar el filtro de redimensionado del marco propio (evita accesos a
        # la ventana durante el cierre).
        if self._redimensionador is not None:
            app = QApplication.instance()
            if app is not None:
                app.removeEventFilter(self._redimensionador)
            self._redimensionador = None
        logger.info("Typoo cerrado correctamente.")
        evento.accept()

    def _guardar_geometria(self) -> None:
        self._config.geometria_ventana = bytes(self.saveGeometry())
        self._config.estado_ventana    = bytes(self.saveState())

    def _restaurar_geometria(self) -> None:
        geometria = self._config.geometria_ventana
        estado    = self._config.estado_ventana
        if geometria:
            try:
                self.restoreGeometry(geometria)
            except Exception:
                pass
        if estado:
            try:
                self.restoreState(estado)
            except Exception:
                pass

    # ─── Confirmación de cierre de proyecto ───────────────────────────────────

    def _confirmar_cierre_proyecto(self) -> bool:
        """
        Si hay un proyecto activo con cambios, pregunta si guardar.
        Retorna True si se puede continuar, False si el usuario canceló.
        """
        if not self._gestor.hay_proyecto:
            return True
        hay_cambios = any(
            p.hay_cambios_pendientes()
            for p in (self._panel1, self._panel2, self._panel3)
        )
        if hay_cambios:
            resp = QMessageBox.question(
                self,
                "Proyecto activo",
                "Hay cambios sin guardar en el proyecto actual.\n¿Guardar antes de continuar?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
            )
            if resp == QMessageBox.StandardButton.Cancel:
                return False
            if resp == QMessageBox.StandardButton.Save:
                self._guardar_todos()
        return True

    # ─── Utilidades ──────────────────────────────────────────────────────────

    @staticmethod
    def _mostrar_error(titulo: str, mensaje: str) -> None:
        QMessageBox.critical(None, titulo, mensaje)

    @staticmethod
    def _mostrar_advertencia(titulo: str, mensaje: str) -> None:
        QMessageBox.warning(None, titulo, mensaje)
