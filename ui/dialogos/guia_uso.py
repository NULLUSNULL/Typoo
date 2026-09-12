# ui/dialogos/guia_uso.py
# Guía de uso integrada: explica por secciones las funciones de Typoo y cómo
# usarlas, con un buscador que filtra las secciones y resalta coincidencias.

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QTextDocument
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.constantes import NOMBRE_APP


@dataclass(frozen=True)
class Tema:
    id: str
    titulo: str
    emoji: str
    html: str


def _quitar_etiquetas(html: str) -> str:
    """Texto plano de un fragmento HTML, para poder buscar en su contenido."""
    return re.sub(r"<[^>]+>", " ", html)


# ─── Contenido de la guía ──────────────────────────────────────────────────────
# Cada tema es un fragmento de HTML (rich text de Qt: admite <h3>, <p>, <ul>,
# <b>, <code>…). Mantener en español y alineado con las funciones reales.

TEMAS: list[Tema] = [
    Tema("inicio", "Primeros pasos", "🚀", f"""
        <h2>Primeros pasos</h2>
        <p>{NOMBRE_APP} organiza cada novela como un <b>proyecto</b>: una carpeta en
        tu disco con un árbol de documentos (capítulos, escenas, personajes,
        ubicaciones y notas) y sus metadatos.</p>
        <p>Al abrir el programa aparece el <b>Gestor de proyectos</b>, desde donde
        puedes crear un proyecto nuevo o abrir uno existente. Consulta la sección
        «Gestor de proyectos» para más detalle.</p>
        <p>Una vez abierto un proyecto, la ventana se organiza en:</p>
        <ul>
        <li><b>Barra superior:</b> nombre de la app y barra de formato.</li>
        <li><b>Explorador</b> (izquierda): árbol del proyecto.</li>
        <li><b>Área de edición</b> (centro): hasta 3 zonas con pestañas.</li>
        <li><b>Detalles</b> y <b>Asistente de IA</b> (derecha): metadatos del
        elemento activo y chat con IA, si está habilitada.</li>
        </ul>
        <p>Todos los paneles se pueden mostrar u ocultar desde el menú
        <b>Ver</b>, cada uno con su atajo (<code>Ctrl+1</code> a
        <code>Ctrl+6</code>).</p>
    """),

    Tema("proyectos", "Gestor de proyectos", "📁", f"""
        <h2>Gestor de proyectos</h2>
        <p>Se abre al iniciar {NOMBRE_APP} y también desde
        <b>Archivo → Gestor de proyectos…</b> (<code>Ctrl+Shift+O</code>). Lista
        todos los proyectos que la aplicación conoce y permite:</p>
        <ul>
        <li><b>Abrir</b> un proyecto de la lista (doble clic o botón «Abrir»).</li>
        <li><b>Nuevo proyecto…</b>: crea uno pidiendo nombre, autor y carpeta
        destino.</li>
        <li><b>Añadir existente…</b>: registra una carpeta de proyecto que ya
        tienes en disco pero que no aparece en la lista.</li>
        <li><b>Eliminar…</b>: borra un proyecto <i>permanentemente</i> del disco.
        Por seguridad hay que escribir su nombre exacto para confirmar.</li>
        </ul>
        <p>Un proyecto que ya no se encuentra en su ruta se marca como
        «no encontrado»: no se puede abrir, pero sí quitar de la lista.</p>
        <p>También puedes crear (<code>Ctrl+Shift+N</code>) o abrir
        (<code>Ctrl+O</code>) un proyecto directamente desde el menú
        <b>Archivo</b>, sin pasar por el gestor.</p>
    """),

    Tema("dossier", "El dossier del proyecto", "🗂️", """
        <h2>El dossier del proyecto</h2>
        <p>El explorador (panel izquierdo) organiza cada proyecto en cuatro
        secciones fijas:</p>
        <ul>
        <li><b>Manuscrito:</b> capítulos (carpetas) que contienen escenas
        (los documentos con el texto de la novela).</li>
        <li><b>Personajes</b></li>
        <li><b>Ubicaciones</b></li>
        <li><b>Notas e investigación</b></li>
        </ul>
        <p>El <b>orden de lectura</b> de la novela es el del árbol de
        Manuscrito, leído de arriba abajo.</p>
        <h3>Crear elementos</h3>
        <p>Clic derecho sobre un elemento del árbol ofrece la creación
        pertinente según dónde estés (un capítulo dentro de Manuscrito, una
        escena dentro de un capítulo, etc.). También desde el menú
        <b>Proyecto</b>: Nuevo capítulo (<code>Ctrl+Shift+C</code>), Nueva
        escena (<code>Ctrl+Shift+E</code>), Nueva nota (<code>Ctrl+Shift+A</code>),
        Nuevo personaje y Nueva ubicación.</p>
        <h3>Reordenar arrastrando</h3>
        <p>Se puede reordenar y mover elementos <b>dentro de su misma
        sección</b> arrastrándolos en el árbol (reordenar capítulos, mover una
        escena de un capítulo a otro, ordenar personajes…). No se permite
        mezclar secciones ni anidar un capítulo dentro de otro.</p>
        <h3>Otras acciones</h3>
        <p>Clic derecho también permite <b>Renombrar</b>, <b>Eliminar</b> y,
        sobre un documento, <b>Abrir en área</b> (Área 1, 2 o 3) para verlo en
        una zona de edición concreta.</p>
    """),

    Tema("editor", "El editor y la barra de formato", "✍️", """
        <h2>El editor y la barra de formato</h2>
        <p>El editor usa tipografía con serifas, columna de lectura centrada
        e interlineado amplio, pensado para escritura larga. Se puede hacer
        zoom con <code>Ctrl</code> + rueda del ratón.</p>
        <h3>Barra de formato</h3>
        <p>Justo debajo del nombre de la app, con iconos que se adaptan al
        tema activo:</p>
        <ul>
        <li>Estilo de párrafo (título de capítulo, sección, subsección) y
        selector de tipografía/tamaño.</li>
        <li><b>Negrita</b> (<code>Ctrl+B</code>), <i>cursiva</i>
        (<code>Ctrl+I</code>), subrayado (<code>Ctrl+U</code>), tachado,
        sub/superíndice.</li>
        <li>Cita/epígrafe, listas con viñetas o numeradas, con sangría
        multinivel (<code>Tab</code> / <code>Mayús+Tab</code>).</li>
        <li>Separador de escena y caracteres especiales frecuentes en novela:
        rayas, guiones, comillas españolas «» e inglesas “”, puntos
        suspensivos… El botón <b>Ω</b> abre el menú completo.</li>
        </ul>
        <h3>Múltiples áreas de trabajo</h3>
        <p>Hasta <b>3 áreas de edición</b> independientes, cada una con sus
        propias pestañas. Se muestran/ocultan con <code>Ctrl+2</code> y
        <code>Ctrl+3</code> (el Área 1 siempre está visible). Para enviar un
        documento a otra área: clic derecho sobre él en el explorador →
        <b>Abrir en área</b>, o clic derecho sobre su pestaña →
        <b>Mover a Área X</b>.</p>
        <h3>Pestañas</h3>
        <p>Cada documento abierto es una pestaña con su botón «×» de cierre.
        Doble clic en un elemento del explorador lo abre (o lo activa, si ya
        estaba abierto).</p>
    """),

    Tema("detalles", "Panel de Detalles", "📝", """
        <h2>Panel de Detalles</h2>
        <p>Muestra y permite editar los <b>metadatos</b> del elemento activo
        (la pestaña con el foco), con campos propios según su tipo:</p>
        <ul>
        <li><b>Escenas:</b> resumen, estado, personajes presentes, punto de
        vista, ubicación y tramas vinculadas.</li>
        <li><b>Personajes</b> y <b>ubicaciones:</b> ficha con los campos de su
        esquema (descripción, motivación, rasgos…).</li>
        </ul>
        <p>Los cambios se guardan automáticamente tras un breve instante de
        inactividad. Los vínculos que estableces aquí (personajes, ubicación,
        tramas de una escena) son los que alimentan el <b>Visor de tramas</b>.</p>
        <p>Se muestra/oculta con <code>Ctrl+4</code>.</p>
    """),

    Tema("tramas", "Visor de tramas", "🧵", """
        <h2>Visor de tramas</h2>
        <p>Banda inferior plegable (<b>Ver → Visor de tramas</b>,
        <code>Ctrl+5</code>) con una rejilla tipo <i>story grid</i>:</p>
        <ul>
        <li><b>Columnas:</b> las escenas en su orden de lectura.</li>
        <li><b>Filas:</b> tramas, personajes o ubicaciones, según el selector
        «Ver por»; cada una con su color.</li>
        <li>Una celda coloreada indica que esa escena está relacionada con
        esa entidad.</li>
        </ul>
        <p>Responde a tres preguntas: qué escenas desarrollan cada
        <b>trama</b>, en qué escenas aparece cada <b>personaje</b> y dónde
        ocurre cada <b>ubicación</b>. Los datos vienen de los vínculos que
        rellenas en el panel de Detalles de cada escena.</p>
        <p>Las tramas (nombre y color) se gestionan desde el propio visor.</p>
    """),

    Tema("buscar", "Buscar y reemplazar", "🔍", """
        <h2>Buscar y reemplazar</h2>
        <p><code>Ctrl+F</code> o <code>Ctrl+H</code> abren el mismo diálogo,
        con tres pestañas: <b>Buscar</b>, <b>Reemplazar</b> y
        <b>En el proyecto</b>. Ambas búsquedas admiten <b>expresiones
        regulares</b> y la opción de ignorar mayúsculas/minúsculas.</p>
        <h3>En el documento activo</h3>
        <p>«Buscar» resalta la coincidencia y permite saltar a la
        siguiente/anterior; «Reemplazar» sustituye una coincidencia o todas
        a la vez, solo en el documento abierto.</p>
        <h3>En todo el proyecto</h3>
        <p>La pestaña <b>«En el proyecto»</b> busca en <i>todos</i> los
        documentos del proyecto (no solo el abierto) y muestra los
        resultados en una lista, <b>agrupados por documento</b>, con el
        número de línea y un fragmento de contexto donde la coincidencia
        aparece marcada entre <code>⟪⟫</code>.</p>
        <p>Doble clic (o <code>Intro</code>) sobre un resultado <b>abre ese
        documento</b> (o lo activa, si ya estaba abierto) y <b>selecciona
        exactamente</b> el texto encontrado, listo para editar.</p>
    """),

    Tema("exportar", "Exportación", "📤", """
        <h2>Exportación</h2>
        <p><b>Archivo → Exportar…</b> genera el manuscrito en:</p>
        <ul>
        <li><b>Word</b> (.docx) — requiere <code>python-docx</code>.</li>
        <li><b>PDF</b> — requiere <code>reportlab</code>.</li>
        <li><b>Texto plano</b> (.txt) — sin dependencias adicionales.</li>
        </ul>
        <p>Son dependencias <i>opcionales</i>: si falta alguna, el propio
        diálogo indica el comando exacto para instalarla
        (<code>pip install python-docx reportlab</code>).</p>
    """),

    Tema("temas", "Temas visuales", "🌗", """
        <h2>Temas visuales</h2>
        <p>Oscuro (por defecto, paleta One Dark) y claro (inspirado en
        macOS). Se alternan con <code>Ctrl+Shift+T</code> y se recuerdan
        entre sesiones. Los iconos de la barra de formato y de la barra de
        título se recolorean automáticamente al cambiar de tema.</p>
    """),

    Tema("respaldos", "Autoguardado y respaldos", "💾", """
        <h2>Autoguardado y respaldos</h2>
        <p>El documento activo se guarda solo mediante <code>Ctrl+S</code>
        (uno) o <code>Ctrl+Shift+S</code> (todos), además del autoguardado
        periódico configurable en <b>Preferencias</b>.</p>
        <h3>Respaldo automático</h3>
        <p>En <b>Preferencias → Respaldo automático</b>:</p>
        <ul>
        <li><b>Intervalo:</b> desactivado, o cada 5, 15, 30, 45 minutos o 1
        hora.</li>
        <li><b>Ruta de destino:</b> carpeta para los ZIP de respaldo; si se
        deja vacía, se crean en <code>.respaldos/</code> dentro del propio
        proyecto.</li>
        </ul>
        <p>También puedes forzar uno con <b>Proyecto → Crear respaldo</b>.</p>
    """),

    Tema("concentracion", "Modo concentración", "🧘", """
        <h2>Modo concentración</h2>
        <p><code>F12</code> deja <b>solo el texto centrado</b> en pantalla:
        oculta la barra de menú, todos los paneles (explorador, detalles,
        tramas, asistente) y la barra de edición, y pasa a pantalla completa.
        Arriba, centrado, un pequeño aviso recuerda «Pulsa Esc para salir».</p>
        <p><code>Esc</code> (o volver a pulsar <code>F12</code>) restaura
        exactamente los paneles que tenías visibles antes de entrar.</p>
        <p><code>F11</code> alterna solo la pantalla completa, sin ocultar
        nada más.</p>
    """),

    Tema("ia", "Asistente de IA (opcional)", "🤖", """
        <h2>Asistente de IA (opcional)</h2>
        <p>Está <b>desactivada por defecto</b> y no añade dependencias
        obligatorias. Se activa en <b>Herramientas → Preferencias → IA</b>.</p>
        <h3>Proveedores</h3>
        <ul>
        <li><b>Nube:</b> OpenAI, Anthropic, NVIDIA, Groq, Mistral (el texto
        que envíes sale de tu equipo hacia el proveedor).</li>
        <li><b>Local:</b> Ollama y LM Studio (sin conexión, requieren tener
        el servidor local en marcha).</li>
        <li><b>Embebido:</b> modelos GGUF descargables que corren en tu
        equipo (requiere la dependencia opcional <code>llama-cpp-python</code>).
        Su <b>contexto (n_ctx)</b> es ajustable en Preferencias: más contexto
        admite textos más largos a cambio de más RAM.</li>
        </ul>
        <h3>Qué puede hacer</h3>
        <ul>
        <li><b>Reescribir/corregir</b> la selección: clic derecho en el
        editor → pulir, condensar, expandir, cambiar de registro, «mostrar
        no contar», naturalizar diálogo, o corregir ortografía/gramática.</li>
        <li><b>Sinopsis</b> automática de una escena/capítulo (rellena el
        campo Resumen) y <b>fichas</b> sugeridas para personajes/ubicaciones.</li>
        <li><b>Guardián de coherencia:</b> informe que contrasta un personaje
        (o un capítulo entero) con sus escenas, buscando contradicciones.</li>
        <li><b>Tormenta de ideas:</b> propone 3 caminos para continuar la
        historia y desarrolla el que elijas.</li>
        <li><b>Enviar a Notas:</b> el informe de coherencia y el resultado de
        la tormenta de ideas se pueden guardar como una nota nueva, con
        título generado automáticamente.</li>
        <li><b>Asistente (chat):</b> panel lateral (<code>Ctrl+6</code>) que
        responde preguntas sobre el manuscrito citando sus fuentes.</li>
        </ul>
    """),

    Tema("atajos", "Todos los atajos de teclado", "⌨️", """
        <h2>Todos los atajos de teclado</h2>
        <table cellspacing="6">
        <tr><td><code>Ctrl+Shift+O</code></td><td>Gestor de proyectos</td></tr>
        <tr><td><code>Ctrl+Shift+N</code></td><td>Nuevo proyecto</td></tr>
        <tr><td><code>Ctrl+O</code></td><td>Abrir proyecto</td></tr>
        <tr><td><code>Ctrl+S</code></td><td>Guardar documento activo</td></tr>
        <tr><td><code>Ctrl+Shift+S</code></td><td>Guardar todos</td></tr>
        <tr><td><code>Ctrl+Q</code></td><td>Salir</td></tr>
        <tr><td><code>Ctrl+Z</code> / <code>Ctrl+Y</code></td><td>Deshacer / Rehacer</td></tr>
        <tr><td><code>Ctrl+X</code> / <code>Ctrl+C</code> / <code>Ctrl+V</code></td><td>Cortar / Copiar / Pegar</td></tr>
        <tr><td><code>Ctrl+F</code></td><td>Buscar</td></tr>
        <tr><td><code>Ctrl+H</code></td><td>Buscar y reemplazar</td></tr>
        <tr><td><code>Ctrl+B</code> / <code>Ctrl+I</code> / <code>Ctrl+U</code></td><td>Negrita / Cursiva / Subrayado</td></tr>
        <tr><td><code>Ctrl+1</code></td><td>Mostrar/ocultar el explorador</td></tr>
        <tr><td><code>Ctrl+2</code> / <code>Ctrl+3</code></td><td>Mostrar/ocultar Área 2 / Área 3</td></tr>
        <tr><td><code>Ctrl+4</code></td><td>Mostrar/ocultar Detalles</td></tr>
        <tr><td><code>Ctrl+5</code></td><td>Mostrar/ocultar el visor de tramas</td></tr>
        <tr><td><code>Ctrl+6</code></td><td>Mostrar/ocultar el asistente de IA</td></tr>
        <tr><td><code>Ctrl+Shift+T</code></td><td>Cambiar tema claro/oscuro</td></tr>
        <tr><td><code>Ctrl+Shift+C</code></td><td>Nuevo capítulo</td></tr>
        <tr><td><code>Ctrl+Shift+E</code></td><td>Nueva escena</td></tr>
        <tr><td><code>Ctrl+Shift+A</code></td><td>Nueva nota</td></tr>
        <tr><td><code>Ctrl+,</code></td><td>Preferencias</td></tr>
        <tr><td><code>F1</code></td><td>Esta guía de uso</td></tr>
        <tr><td><code>F11</code></td><td>Pantalla completa</td></tr>
        <tr><td><code>F12</code></td><td>Modo concentración</td></tr>
        <tr><td><code>Esc</code></td><td>Salir del modo concentración</td></tr>
        </table>
    """),
]


class DialogoGuiaUso(QDialog):
    """Guía de uso navegable por secciones, con buscador."""

    _COLOR_RESALTE = QColor(255, 213, 74, 130)  # amarillo translúcido

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Guía de uso — {NOMBRE_APP}")
        self.setMinimumSize(820, 560)
        self.resize(920, 620)
        self.setModal(False)
        self._indices_por_tema = {t.id: i for i, t in enumerate(TEMAS)}
        # Texto plano (sin etiquetas) de cada tema, precalculado para buscar.
        self._texto_plano = {
            t.id: (t.titulo + " " + _quitar_etiquetas(t.html)).casefold()
            for t in TEMAS
        }
        self._construir_ui()
        self._poblar_lista()
        if TEMAS:
            self._lista.setCurrentRow(0)

    # ─── UI ─────────────────────────────────────────────────────────────────
    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        cabecera = QHBoxLayout()
        titulo = QLabel(f"📖 Guía de uso de {NOMBRE_APP}")
        f = titulo.font()
        f.setBold(True)
        f.setPointSize(f.pointSize() + 3)
        titulo.setFont(f)
        cabecera.addWidget(titulo)
        cabecera.addStretch(1)
        layout.addLayout(cabecera)

        self._buscador = QLineEdit()
        self._buscador.setPlaceholderText("🔎 Buscar en la guía… (por ejemplo «tramas» o «atajo»)")
        self._buscador.setClearButtonEnabled(True)
        self._buscador.textChanged.connect(self._filtrar)
        layout.addWidget(self._buscador)

        self._lbl_resultados = QLabel()
        self._lbl_resultados.setStyleSheet("color: #8A8F98;")
        self._lbl_resultados.hide()
        layout.addWidget(self._lbl_resultados)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        self._lista = QListWidget()
        self._lista.setObjectName("ListaGuiaUso")
        self._lista.setMinimumWidth(220)
        self._lista.setMaximumWidth(320)
        self._lista.setStyleSheet(
            "#ListaGuiaUso::item { padding: 7px 8px; border-radius: 6px; }"
            "#ListaGuiaUso::item:selected,"
            "#ListaGuiaUso::item:selected:!active {"
            " background: #2F6FE0; color: #FFFFFF; }"
        )
        self._lista.currentRowChanged.connect(self._al_cambiar_seleccion)
        splitter.addWidget(self._lista)

        self._contenido = QTextBrowser()
        self._contenido.setOpenExternalLinks(False)
        splitter.addWidget(self._contenido)
        splitter.setSizes([240, 680])

        layout.addWidget(splitter, 1)

        fila = QHBoxLayout()
        fila.addStretch(1)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setDefault(True)
        btn_cerrar.clicked.connect(self.close)
        fila.addWidget(btn_cerrar)
        layout.addLayout(fila)

        self._buscador.setFocus()

    def _poblar_lista(self) -> None:
        self._lista.clear()
        for tema in TEMAS:
            item = QListWidgetItem(f"{tema.emoji}  {tema.titulo}")
            item.setData(Qt.ItemDataRole.UserRole, tema.id)
            self._lista.addItem(item)

    # ─── Búsqueda ───────────────────────────────────────────────────────────
    def _filtrar(self, consulta: str) -> None:
        consulta_norm = consulta.strip().casefold()
        alguna_visible = False
        primera_visible = -1
        for fila in range(self._lista.count()):
            item = self._lista.item(fila)
            tema_id = item.data(Qt.ItemDataRole.UserRole)
            coincide = (not consulta_norm) or (consulta_norm in self._texto_plano[tema_id])
            item.setHidden(not coincide)
            if coincide:
                alguna_visible = True
                if primera_visible < 0:
                    primera_visible = fila

        if consulta_norm:
            n = sum(1 for i in range(self._lista.count()) if not self._lista.item(i).isHidden())
            self._lbl_resultados.setText(
                f"{n} sección(es) con «{consulta.strip()}»" if n else
                f"Sin resultados para «{consulta.strip()}»")
            self._lbl_resultados.setVisible(True)
        else:
            self._lbl_resultados.hide()

        actual = self._lista.currentItem()
        if not alguna_visible:
            self._resaltar("")
            return
        if actual is None or actual.isHidden():
            self._lista.setCurrentRow(primera_visible)
        else:
            # Ya está en el tema correcto: solo actualizar el resaltado.
            self._resaltar(consulta.strip())

    def _al_cambiar_seleccion(self, fila: int) -> None:
        if fila < 0:
            self._contenido.clear()
            return
        tema_id = self._lista.item(fila).data(Qt.ItemDataRole.UserRole)
        tema = TEMAS[self._indices_por_tema[tema_id]]
        self._contenido.setHtml(tema.html)
        self._resaltar(self._buscador.text().strip())

    def _resaltar(self, consulta: str) -> None:
        """Resalta todas las apariciones de `consulta` en el tema mostrado."""
        selecciones = []
        if consulta:
            fmt = QTextCharFormat()
            fmt.setBackground(self._COLOR_RESALTE)
            documento = self._contenido.document()
            cursor = documento.find(consulta)
            while not cursor.isNull():
                sel = QTextBrowser.ExtraSelection()
                sel.cursor = cursor
                sel.format = fmt
                selecciones.append(sel)
                cursor = documento.find(consulta, cursor)
        self._contenido.setExtraSelections(selecciones)

    def mostrar_tema(self, tema_id: str) -> None:
        """Abre la guía directamente en un tema concreto (uso programático)."""
        idx = self._indices_por_tema.get(tema_id)
        if idx is not None:
            fila = next((i for i in range(self._lista.count())
                        if self._lista.item(i).data(Qt.ItemDataRole.UserRole) == tema_id), -1)
            if fila >= 0:
                self._lista.setCurrentRow(fila)
