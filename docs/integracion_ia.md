# Integración con IA — Diseño

> Documento de diseño para la rama `claude/integracion-ia`. Recoge la
> arquitectura propuesta, el catálogo de proveedores/modelos y las funciones de
> valor. **Nada de esto está implementado todavía**: es el plan a revisar antes
> de construir.

## Principios

1. **Totalmente opcional y desactivada por defecto.** Sin habilitarla, la
   interfaz no muestra ninguna opción de IA (solo la entrada para configurarla).
2. **Privacidad primero.** El manuscrito es material sensible. El usuario elige
   explícitamente si su texto sale del equipo. Las opciones **local** y
   **embebida** funcionan 100 % sin conexión; las de **pago/nube** avisan de que
   el texto se envía a un tercero.
3. **Proveedor intercambiable.** Una única capa de abstracción; añadir un
   proveedor nuevo no toca la interfaz ni las funciones.
4. **Degradación elegante.** Si falta una dependencia opcional o el servicio no
   responde, la app sigue funcionando igual; la IA nunca bloquea la escritura.

## Modos de proveedor

| Modo | Ejemplos | Conexión | Coste | Notas |
|------|----------|----------|-------|-------|
| **Nube (pago)** | OpenAI, Anthropic, NVIDIA NIM, Groq, Mistral… | Sí | API key del usuario | El texto sale del equipo. Muchos exponen API compatible con OpenAI. |
| **Local (servidor)** | Ollama, LM Studio | Sí (localhost) | Gratis | El usuario ya tiene el motor corriendo; hablamos por HTTP local. |
| **Embebida (descargable)** | GGUF vía `llama.cpp` | No | Gratis | La app descarga y ejecuta el modelo. `llama-cpp-python` se empaqueta al compilar. |
| **Apple Foundation (macOS)** | Modelo del sistema (Apple Intelligence) | No | Gratis | Solo macOS 26+ / Apple Silicon. Vía ayudante nativo `typoo-apple-llm` (ver `extras/apple_foundation`). |

### Capa de abstracción

```
ai/
├── proveedores/
│   ├── base.py          # ProveedorIA: generar(prompt, sistema, *, stream) -> texto
│   ├── openai_compat.py # OpenAI, NVIDIA, Groq, Mistral, LM Studio (mismo protocolo)
│   ├── anthropic.py     # API de Anthropic (Messages)
│   ├── ollama.py        # API local de Ollama
│   └── embebido.py      # llama-cpp-python sobre un .gguf local
├── modelos.py           # catálogo de modelos embebidos + descarga/verificación
├── contexto.py          # arma el contexto del proyecto (escena, dossier, tramas)
├── tareas.py            # prompts de alto nivel (continuar, reescribir, sinopsis…)
└── servicio_ia.py       # fachada: elige proveedor según config y ejecuta tareas
```

- Casi todos los proveedores de nube y LM Studio hablan el **protocolo OpenAI**
  (`/v1/chat/completions`), así que un solo `openai_compat.py` cubre OpenAI,
  NVIDIA, Groq, Mistral y LM Studio cambiando solo `base_url` y `api_key`.
  Anthropic y Ollama llevan su propio adaptador.
- Todo se ejecuta en un **hilo/worker** con salida en *streaming* para no
  congelar la interfaz; se puede cancelar.
- Las **API keys** se guardan con el almacén de credenciales del sistema
  (`keyring`) cuando esté disponible; nunca en `proyecto.json` ni en el repo.

## Modelos embebidos (descargables)

Tres niveles según el equipo, en formato **GGUF** (cuantizados, vía `llama.cpp`).
Prioridad: buena prosa en **español** e instrucción fiable. Son sugerencias
iniciales, ajustables (el catálogo vive en `ai/modelos.py`):

| Nivel | Equipo objetivo | Tamaño aprox. | Candidatos |
|-------|-----------------|---------------|------------|
| **Ligero** | Portátil, ~1,2 GB RAM libre | ~1,1 GB (Q4_K_M) | Qwen3 1.7B |
| **Medio** (recomendado) | ~2,5–3 GB RAM libre | ~2,5 GB (Q4_K_M) | Qwen3 4B |
| **Grande** | ~9–10 GB RAM libre / GPU | ~9 GB (Q4_K_M) | Qwen3 14B |

Los repositorios/archivos GGUF (repos oficiales de Qwen en Hugging Face) están
en `ai/modelos.py`; si alguna descarga devuelve 404 por un cambio de nombre de
archivo, se corrige ahí en una línea.

Descarga desde Hugging Face con barra de progreso y posibilidad de borrar el
modelo para liberar espacio. La dependencia `llama-cpp-python` se **empaqueta
automáticamente al compilar** (`build.sh`/`build.bat` la instalan y PyInstaller
la incluye con `--collect-all llama_cpp`), así que en la app distribuida los
modelos embebidos funcionan sin que el usuario instale nada. En ejecución desde
código sigue siendo opcional (solo se necesita para el modo embebido). Se puede
excluir del build con la variable `TYPOO_SIN_EMBEBIDO=1`.

## Experiencia de usuario (opt-in)

1. **Menú `IA` → «Configurar asistente…»** (única entrada visible al principio).
2. Asistente de configuración: elegir modo → (nube: API key + modelo; local:
   URL + modelo detectado; embebido: elegir nivel y descargar) → **Probar
   conexión**.
3. Al quedar habilitada y verificada, aparecen:
   - Nuevas acciones en el **menú `IA`** y en el **menú contextual del editor**
     (sobre la selección).
   - Un **panel lateral «Asistente»** (dock) para chat con contexto y para
     revisar/insertar sugerencias.
   - Indicador de estado (proveedor/modelo activo) en la barra de estado.
4. Un interruptor global para deshabilitarla vuelve a ocultarlo todo.

## Funciones de valor propuestas

Aprovechan lo que Typoo ya modela: manuscrito por escenas, POV, sinopsis,
fichas de personajes/ubicaciones y tramas.

### Escritura y edición (sobre el editor)
- **Continuar la escena** a partir del texto y su contexto (POV, personajes
  presentes, sinopsis, trama).
- **Reescribir la selección** con intención: pulir, condensar, expandir,
  cambiar de registro/tono, «muéstralo, no lo cuentes».
- **Corrección de estilo literario**: repeticiones, muletillas, adverbios en
  «-mente», voz pasiva, frases largas; con sugerencias aplicables.
- **Diálogo**: naturalizar, diferenciar la voz de cada personaje.

### Dossier y coherencia
- **Sinopsis automática** de escena/capítulo → rellena el campo `Resumen`.
- **Fichas asistidas**: proponer/enriquecer metadatos de personaje o ubicación a
  partir del manuscrito (apariencia, motivación, arco).
- **Guardián de coherencia**: contrastar lo que hace/dice un personaje con su
  ficha y señalar contradicciones (edad, rasgos, cronología con `Momento`).

### Estructura y tramas
- **Lluvia de ideas de trama**: siguientes escenas, huecos argumentales, giros,
  a partir del `story grid` y las sinopsis.
- **Análisis de ritmo/tensión** por capítulo.

### Consulta (panel «Asistente», con contexto del proyecto)
- **Chat sobre el manuscrito**: «¿dónde aparece por primera vez el faro?»,
  «resume el arco de Mara», usando recuperación sobre escenas y dossier.
- **Nombres**: sugerir nombres de personaje/lugar según género y época.

## Plan por fases

- **Fase 0 — Cimientos ✅ (hecho):** capa de proveedores (nube OpenAI-compat +
  Anthropic; local Ollama/LM Studio), config opt-in, asistente de configuración
  y «Probar conexión».
- **Fase 1 — Reescritura ✅ (hecho):** *Reescribir selección* con intenciones y
  diálogo de resultado en streaming (reemplazar / insertar debajo / detener).
- **Fase 2 — Dossier ✅ (hecho):** sinopsis automática (rellena `Resumen`),
  fichas asistidas (rellena campos vacíos de personaje/ubicación) y guardián de
  coherencia (informe que contrasta la ficha con las escenas del personaje).
- **Fase 3 — Embebido ✅ (hecho):** catálogo de 3 modelos GGUF (ligero/medio/
  grande), descarga con progreso/cancelación en `ai/modelos.py`, gestor visual
  (`Modelos embebidos`) y proveedor `embebido` que ejecuta con `llama-cpp-python`
  (dependencia opcional, carga perezosa y cacheada).
- **Fase 4 — Chat con contexto (RAG) ✅ (hecho):** panel lateral «Asistente»
  que responde preguntas sobre el manuscrito. Recuperación léxica ligera
  (BM25, `ai/recuperacion.py`, sin dependencias) sobre escenas y dossier; cita
  las fuentes usadas y mantiene el historial de la conversación.
- **Tormenta de ideas ✅ (hecho):** desde el menú IA, propone maneras concretas
  de continuar la historia (antiestancamiento) a partir del esquema de escenas,
  las tramas y la escena activa.

### Ubicación en la interfaz (revisión de UX)
- **Reescribir**: en el **menú contextual del editor** (clic derecho sobre la
  selección), no en la barra de menús.
- **Dossier** (sinopsis / ficha / coherencia): en el **menú contextual del
  explorador**, contextual al tipo de elemento (escena, personaje, ubicación).
- **Menú IA** (barra superior): solo acciones globales — configurar, tormenta de
  ideas y abrir el asistente.

## Dependencias (todas opcionales, por modo)

- Nube/local: solo `requests`/`httpx` (o `openai`/`anthropic` si se prefiere).
- Embebido: `llama-cpp-python` + `huggingface_hub` para la descarga.
- Credenciales: `keyring` (con degradación a fichero cifrado si no está).

Nada de esto se añade a `requirements.txt` como obligatorio; se instala bajo
demanda según el modo elegido.
