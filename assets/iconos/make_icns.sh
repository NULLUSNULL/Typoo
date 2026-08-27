#!/usr/bin/env bash
# make_icns.sh — Genera assets/iconos/typoo-icon.icns para el paquete .app de
# macOS a partir de un PNG cuadrado de alta resolución (idealmente 1024×1024).
#
# Requiere macOS (usa las herramientas nativas «sips» e «iconutil»).
#
# Uso:
#   ./make_icns.sh ruta/al/logo-1024.png
#
# Si no indicas un PNG, intenta usar «typoo-icon-1024.png» de esta carpeta.
# El SVG de la marca está en typoo-icon.svg: expórtalo a PNG 1024×1024 con la
# herramienta que prefieras (Preview/Vista Previa, Figma, Inkscape…) antes de
# ejecutar este script.

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:-$DIR/typoo-icon-1024.png}"
OUT="$DIR/typoo-icon.icns"

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "Este script solo funciona en macOS (necesita sips e iconutil)." >&2
    exit 1
fi
if [[ ! -f "$SRC" ]]; then
    echo "No se encontró el PNG de origen: $SRC" >&2
    echo "Pásalo como argumento:  ./make_icns.sh logo-1024.png" >&2
    exit 1
fi

WORK="$(mktemp -d)/typoo.iconset"
mkdir -p "$WORK"

# Tamaños que exige un .icns (normal y @2x).
for size in 16 32 128 256 512; do
    sips -z "$size"  "$size"  "$SRC" --out "$WORK/icon_${size}x${size}.png"      >/dev/null
    dbl=$(( size * 2 ))
    sips -z "$dbl"   "$dbl"   "$SRC" --out "$WORK/icon_${size}x${size}@2x.png"   >/dev/null
done

iconutil -c icns "$WORK" -o "$OUT"
rm -rf "$(dirname "$WORK")"

echo "Icono generado: $OUT"
echo "Ahora ejecuta ./build.sh para compilar Typoo.app con este icono."
