# Typoo — Suite Profesional de Escritura de Novelas

> Suite de escritura para proyectos literarios.
> Construida con Python 3 y PySide6. Código abierto (MIT).

**Autoría:** NULLUSNULL | **Licencia:** MIT | **Versión:** 1.1.0

---

## Funcionalidades

| Área | Descripción |
|------|-------------|
| Gestión de proyectos | Árbol jerárquico: capítulos, escenas, notas, personajes, ubicaciones |
| Editor Markdown | Resaltado de sintaxis, numeración de líneas, zoom con Ctrl+rueda |
| Múltiples áreas de trabajo | Hasta 3 editores simultáneos con splitters redimensionables |
| Vista previa HTML | Renderizado Markdown en tiempo real en el panel derecho |
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
| `Ctrl+1..4` | Mostrar/ocultar paneles |
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
│   └── logger.py                # Sistema de logging
│
├── models/
│   ├── documento.py             # ItemProyecto (nodo del árbol)
│   └── proyecto.py              # Proyecto (raíz, carga/guardado JSON)
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
│   ├── explorador_proyecto.py   # Árbol lateral (QTreeWidget)
│   ├── barra_herramientas.py    # Barra de formato Markdown con separador inferior
│   ├── panel_pestanas.py        # Contenedor de pestañas con botón × de cierre
│   ├── vista_previa.py          # Vista HTML (QTextBrowser)
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
├── proyecto.json          # Metadatos y árbol del proyecto
├── capitulos/
│   └── capitulo_001.md
├── escenas/
│   └── escena_001.md
├── notas/
├── personajes/
├── ubicaciones/
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
