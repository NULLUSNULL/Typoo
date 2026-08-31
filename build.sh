#!/usr/bin/env bash
# build.sh — Compila Typoo con PyInstaller en macOS y Linux.
#   macOS → dist/Typoo.app   (paquete de aplicación)
#   Linux → dist/Typoo       (ejecutable)
#
# Uso:   ./build.sh
# (En Windows usa build.bat en su lugar.)

set -euo pipefail

PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJ"

SO="$(uname -s)"

# ── 1) Intérprete de Python y dependencias de compilación ────────────────────
# PyInstaller necesita poder importar las dependencias del proyecto (PySide6,
# etc.) para empaquetarlas. Se usa el intérprete actual si ya tiene todo; si
# no, se prepara un entorno virtual local (.venv). Así se evita el error
# «externally-managed-environment» (PEP 668) del Python de Homebrew en macOS,
# sin tocar el Python del sistema.
echo "[1/4] Preparando el entorno de compilación..."

PY="${VIRTUAL_ENV:+$VIRTUAL_ENV/bin/python}"
if [[ -z "${PY:-}" ]]; then
    PY="python3"
    command -v "$PY" >/dev/null 2>&1 || PY="python"
fi

_tiene() { "$PY" -c "import $1" >/dev/null 2>&1; }

if _tiene PySide6 && "$PY" -m PyInstaller --version >/dev/null 2>&1; then
    echo "      Usando el intérprete actual: $PY"
else
    VENV="$PROJ/.venv"
    if [[ ! -d "$VENV" ]]; then
        echo "      Creando entorno virtual local en .venv ..."
        "$PY" -m venv "$VENV"
    fi
    PY="$VENV/bin/python"
    echo "      Instalando dependencias en .venv (PySide6, exportadores, PyInstaller)..."
    "$PY" -m pip install --upgrade pip >/dev/null
    if [[ -f "$PROJ/requirements.txt" ]]; then
        "$PY" -m pip install -r "$PROJ/requirements.txt"
    fi
    "$PY" -m pip install pyinstaller
fi

# ── 3) Icono (opcional) ──────────────────────────────────────────────────────
# En macOS el icono del paquete .app debe ser un .icns. Si existe, se usa; si
# no, se compila sin icono personalizado (ver assets/iconos/make_icns.sh y el
# README para generarlo). En Linux PyInstaller ignora el icono del ejecutable.
ICON_ARGS=()
ICNS="$PROJ/assets/iconos/typoo-icon.icns"
if [[ "$SO" == "Darwin" ]]; then
    if [[ -f "$ICNS" ]]; then
        ICON_ARGS=(--icon "$ICNS")
        echo "      Usando icono: $ICNS"
    else
        echo "      (Aviso) No hay typoo-icon.icns; se compila sin icono propio."
        echo "               Genera uno con assets/iconos/make_icns.sh (ver README)."
    fi
fi

# ── 4) Compilación ───────────────────────────────────────────────────────────
# En macOS/Linux el separador de --add-data es ':' (en Windows es ';').
echo "[2/4] Compilando Typoo para $SO..."
"$PY" -m PyInstaller \
    --onefile \
    --windowed \
    --name Typoo \
    --add-data "$PROJ/assets:assets" \
    "${ICON_ARGS[@]}" \
    --distpath "$PROJ/dist" \
    --workpath "$PROJ/build_tmp" \
    --specpath "$PROJ/build_tmp" \
    --noconfirm \
    "$PROJ/main.py"

# ── 5) Limpieza ──────────────────────────────────────────────────────────────
echo "[3/4] Limpiando archivos temporales..."
rm -rf "$PROJ/build_tmp"

echo "[4/4] Hecho."
echo
if [[ "$SO" == "Darwin" ]]; then
    echo "Compilación completada: dist/Typoo.app"
    echo "Para distribuir puedes comprimirla:  ditto -c -k --keepParent dist/Typoo.app dist/Typoo-mac.zip"
else
    echo "Compilación completada: dist/Typoo"
fi
