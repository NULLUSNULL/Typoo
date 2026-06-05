# Typoo — Suite Profesional de Escritura de Novelas

> Suite de escritura para proyectos literarios.
> Construida con Python 3 y PySide6. Código abierto (MIT).

**Autoría:** NULLUSNULL | **Licencia:** MIT | **Versión:** 1.1.0

---

## Funcionalidades

| Área | Descripción |
|------|-------------|
| Dossier del proyecto | Estructura tipo dossier: **Manuscrito** (capítulos→escenas), **Personajes**, **Ubicaciones** y **Notas e investigación**. El orden de lectura es el del Manuscrito de arriba abajo |
| Editor Markdown | Resaltado de sintaxis, numeración de líneas, zoom con Ctrl+rueda |
| Múltiples áreas de trabajo | Hasta 3 editores simultáneos con splitters redimensionables |
| Panel de detalles | Metadatos propios de cada tipo de elemento según la pestaña con foco; las escenas se vinculan a personajes, ubicaciones y tramas con selectores explícitos |
| Visor de tramas | Rejilla *story grid* (escenas × entidad) coloreada por trama: muestra qué escenas desarrollan cada **trama**, en qué escenas aparece cada **personaje** y dónde ocurre cada **ubicación** |
| Barra de formato | Negrita, cursiva, encabezados, listas, citas, código, símbolos literarios |
| Búsqueda | Simple, con regex y búsqueda en todo el proyecto |
| Exportación | Word (.docx), PDF y texto plano (.txt) |
| Temas | Oscuro (defecto) y claro tipo macOS, intercambiables con Ctrl+Shift+T |
| Autoguardado | Configurable, con copias de seguridad ZIP automáticas |
| Respaldos | Ruta personalizada e intervalo configurable (5 min – 1 h) |
| Modo concentración | F12 oculta paneles y activa pantalla completa |

---

## Requisitos

- **Python 3.9+**
- **PySide6** (Qt for Python 6)
- Sistema operativo: Windows 10+, Ubuntu 20.04+, macOS 12+

---

## Instalación rápida

```bash
# 1. Clonar o descargar el repositorio
git clone https://github.com/NULLUSNULL/Typoo.git
cd Typoo

# 2. Crear entorno virtual (recomendado)
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python main.py
```

---

## Atajos de teclado principales

| Atajo | Acción |
|-------|--------|
| `Ctrl+Shift+N` | Nuevo proyecto |
| `Ctrl+O` | Abrir proyecto |
| `Ctrl+S` | Guardar documento activo |
| `Ctrl+Shift+S` | Guardar todos |
| `Ctrl+F` | Buscar en documento |
| `Ctrl+H` | Buscar y reemplazar |
| `Ctrl+B` | Negrita |
| `Ctrl+I` | Cursiva |
| `Ctrl+U` | Subrayado |
| `Ctrl+1..4` | Mostrar/ocultar paneles (explorador, áreas, detalles) |
| `Ctrl+5` | Mostrar/ocultar el visor de tramas |
| `Ctrl+Shift+T` | Cambiar tema claro/oscuro |
| `F11` | Pantalla completa |
| `F12` | Modo concentración |
| `Ctrl+,` | Preferencias |
| `Ctrl+Q` | Salir |

---

## Áreas de trabajo

Typoo dispone de hasta **3 áreas de trabajo** independientes, cada una con sus propias pestañas de documentos abiertos.

- **Abrir en área**: clic derecho sobre un documento en el explorador → *Abrir en área* → selecciona Área 1, 2 o 3.
- **Mover entre áreas**: clic derecho sobre una pestaña abierta → *Mover a Área X*.
- Las áreas se pueden mostrar u ocultar desde el menú *Ver*.

---

## Dossier del proyecto

El árbol del proyecto sigue una estructura de **dossier** con cuatro secciones fijas:

```
- Manuscrito
  - Capítulo 1
    - Escena 1.1
    - Escena 1.2
  - Capítulo 2
    - Escena 2.1
- Personajes
  - Protagonista
  - Antagonista
- Ubicaciones
  - El faro
- Notas e investigación
```

- Los **capítulos** son carpetas (sin texto propio) y las **escenas** son los documentos que viven dentro de ellos.
- El **orden de lectura** de la novela es el del árbol del *Manuscrito* leído de arriba abajo.
- El menú contextual del explorador ofrece la creación pertinente según el contenedor (capítulos en *Manuscrito*, escenas dentro de un capítulo, etc.).

---

## Tramas y relaciones

Cada **trama** (hilo argumental) tiene un nombre y un color, y se gestiona desde el
**visor de tramas** (menú *Ver → Visor de tramas*, `Ctrl+5`), una banda inferior con una
rejilla *story grid*:

- **Columnas**: las escenas en orden de lectura del manuscrito.
- **Filas**: tramas, personajes o ubicaciones (selector *Ver por:*), cada una con su color.
- Una celda coloreada indica que esa escena está relacionada con esa entidad.

Las relaciones se alimentan de los **vínculos explícitos** del panel de Detalles de cada
escena (personajes presentes, ubicación, punto de vista y tramas), de modo que el visor
responde a tres consultas:

| Flujo | Significado |
|-------|-------------|
| **Trama → escenas** | Qué escenas desarrollan cada trama (clic en la celda para marcar) |
| **Personaje → escenas** | En qué escenas aparece cada personaje |
| **Ubicación → escenas** | Qué escenas ocurren en cada ubicación |

Las tramas se guardan en `proyecto.json` y los vínculos en los metadatos de cada escena.

---

## Respaldos automáticos

En *Preferencias* (Ctrl+,) → sección **Respaldo automático**:

- **Intervalo**: desactivado, 5 min, 15 min, 30 min, 45 min o 1 hora.
- **Ruta de destino**: carpeta personalizada para guardar los ZIP de respaldo. Si se deja vacía, los respaldos se crean en `.respaldos/` dentro de la carpeta del proyecto.

---

## Exportación

Requiere dependencias opcionales instaladas:

```bash
pip install python-docx reportlab
```

El diálogo de exportación (menú *Archivo → Exportar*) indica el comando exacto si falta alguna dependencia.

---

## Temas visuales

| Tema | Descripción |
|------|-------------|
| **Oscuro** (defecto) | Paleta One Dark. Fondo `#282C34`, texto `#ABB2BF`, acento `#528BFF`. |
| **Claro** | Inspirado en macOS. Fondo `#F5F5F7`, editor blanco, acento `#007AFF`. |

El tema se alterna con `Ctrl+Shift+T` y se recuerda entre sesiones.

---

## Estructura del proyecto

```
Typoo/
├── main.py                      # Punto de entrada
├── requirements.txt
├── LICENSE
├── README.md
│
├── core/
│   ├── constantes.py            # Constantes y enumeraciones globales
│   ├── configuracion.py         # Configuración persistente (QSettings)
│   ├── metadatos.py             # Esquema de metadatos por tipo de elemento
│   └── logger.py                # Sistema de logging
│
├── models/
│   ├── documento.py             # ItemProyecto (nodo del árbol)
│   └── proyecto.py              # Proyecto (dossier, tramas, carga/guardado JSON)
│
├── services/
│   ├── gestor_proyectos.py      # CRUD de proyectos y elementos
│   ├── gestor_archivos.py       # Operaciones de sistema de archivos y respaldos
│   ├── autoguardado.py          # Timer de autoguardado (QTimer)
│   └── busqueda.py              # Búsqueda y reemplazo (regex)
│
├── editors/
│   ├── resaltador_sintaxis.py   # QSyntaxHighlighter para Markdown
│   └── editor_markdown.py       # QPlainTextEdit con números de línea
│
├── widgets/
│   ├── explorador_proyecto.py   # Árbol lateral del dossier (QTreeWidget)
│   ├── barra_herramientas.py    # Barra de formato Markdown con separador inferior
│   ├── panel_pestanas.py        # Contenedor de pestañas con botón × de cierre
│   ├── panel_metadatos.py       # Panel lateral de detalles/metadatos del elemento
│   ├── selector_multiple.py     # Selector multiselección (personajes, tramas…)
│   ├── panel_tramas.py          # Visor de tramas (rejilla story grid)
│   └── barra_estado.py          # Barra de estado inferior (QStatusBar)
│
├── ui/
│   ├── ventana_principal.py     # Ventana principal (QMainWindow)
│   ├── temas/
│   │   └── gestor_temas.py      # Hojas de estilo QSS claro/oscuro
│   └── dialogos/
│       ├── nuevo_proyecto.py    # Diálogo de nuevo proyecto
│       ├── buscar_reemplazar.py # Diálogo buscar/reemplazar
│       ├── exportar.py          # Diálogo de exportación
│       └── preferencias.py      # Diálogo de preferencias (fuente, respaldo, tema)
│
├── exporters/
│   ├── exportador_docx.py       # Exportación a Word (python-docx)
│   ├── exportador_pdf.py        # Exportación a PDF (reportlab)
│   └── exportador_txt.py        # Exportación a texto plano
│
└── assets/
    └── iconos/                  # SVGs para flechas de SpinBox y árbol de proyecto
```

---

## Formato de proyecto en disco

```
MiNovela/
├── proyecto.json          # Árbol del dossier, metadatos de cada elemento y tramas
├── manuscrito/            # Documentos de las escenas (los capítulos son carpetas del árbol)
│   ├── escena_1_1.md
│   └── escena_1_2.md
├── personajes/
│   └── protagonista.md
├── ubicaciones/
│   └── el_faro.md
├── notas/
└── .respaldos/            # Copias de seguridad ZIP automáticas
```

---

## Empaquetado para distribución

Usa el script incluido `build.bat` (Windows) para generar un `.exe` en la carpeta `dist/`:

```bat
build.bat
```

O manualmente:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name Typoo ^
    --add-data "assets;assets" ^
    --distpath dist ^
    --workpath build_tmp ^
    --specpath build_tmp ^
    main.py
```

El ejecutable resultante (`dist/Typoo.exe`) incluye todos los assets y no requiere Python instalado.

---

## Licencia

MIT License — Copyright (c) 2026 NULLUSNULL

Consulta el archivo [LICENSE](LICENSE) para más información.

---

## Contribuciones

Las contribuciones son bienvenidas mediante pull requests o issues en el repositorio.
