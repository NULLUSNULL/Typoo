# Ayudante «Apple Foundation» para Typoo

Permite usar como IA **local** el modelo integrado en macOS (Apple
Intelligence), sin descargas ni conexión. Como el framework
`FoundationModels` solo tiene API en Swift, Typoo se comunica con un pequeño
ejecutable —`typoo-apple-llm`— que genera la respuesta en streaming.

## Requisitos

- **macOS 26 (Tahoe) o superior**, en un **Mac con Apple Silicon**.
- **Apple Intelligence activado** (Ajustes → Apple Intelligence y Siri).
- **Xcode 26 / Swift 6** para compilar el ayudante.

## Compilar

```bash
cd extras/apple_foundation
swift build -c release
```

Esto genera `.build/release/typoo-apple-llm`. Typoo lo busca automáticamente en
esa ruta (en desarrollo), junto al ejecutable/Resources de la app empaquetada, o
en el `PATH`. Para instalarlo en el sistema:

```bash
cp .build/release/typoo-apple-llm /usr/local/bin/
```

## Activar en Typoo

**IA → Configurar asistente… → Proveedor: Apple Foundation (macOS) → Probar
conexión → OK.** (Esta opción solo aparece en macOS.)

## Empaquetado en el `.app`

`build.sh` no compila este ayudante automáticamente (requiere Xcode). Si quieres
distribuir el `.app` con Apple Foundation ya listo, compílalo antes y cópialo a
`dist/Typoo.app/Contents/Resources/` tras ejecutar `build.sh`.

## Notas

- La API de `FoundationModels` puede cambiar entre versiones del SDK; si al
  compilar alguna firma no coincide, revisa `Sources/typoo-apple-llm/main.swift`
  (están señaladas las llamadas relevantes: `SystemLanguageModel`,
  `LanguageModelSession`, `streamResponse`).
- El modelo del sistema es pequeño (~3B) y está pensado para tareas acotadas;
  para textos largos o análisis complejos, un modelo de nube o embebido mediano
  dará mejores resultados.
