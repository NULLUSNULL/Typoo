# Typoo — notas para Claude Code

App de escritura de novelas en Python 3 + PySide6. Punto de entrada: `main.py`
(módulos de nivel superior: `core/`, `ui/`, `widgets/`, `editors/`, `services/`,
`models/`, `ai/`, `exporters/`). El paquete `typoo/` es una versión heredada
usada por `run.py`; el código activo es el de nivel superior.

## Versionado (semver) — subir en CADA cambio

Al terminar un cambio que se vaya a commitear, **subir la versión** siguiendo
versionado semántico y dejarla igual en todos estos sitios:

- `core/constantes.py` → `VERSION_APP`  (fuente principal)
- `typoo/__init__.py` → `__version__`
- `typoo/config.py` → `APP_VERSION`
- `README.md` → línea «**Versión:** …»

Regla:
- **patch** (x.y.**Z**) para correcciones de errores.
- **minor** (x.**Y**.0) para nuevas funciones.
- **major** (**X**.0.0) para cambios incompatibles.

Versión actual: **1.3.1**.

## Comprobaciones antes de commitear

- Compilar: `python -m compileall -q ai ui widgets editors core services models`
- Pruebas rápidas en headless: `QT_QPA_PLATFORM=offscreen python …`

## Atribución de commits

Los mensajes de commit terminan con el pie de coautoría indicado por la sesión.
No incluir identificadores de modelo en artefactos del repositorio.
