# ai/tareas.py
# Construcción de los mensajes (prompts) para las tareas de IA de alto nivel.
# Se mantienen en español y orientados a edición literaria.

from __future__ import annotations

import re
from dataclasses import dataclass

from ai.proveedores import Mensaje
from core.constantes import TipoElemento
from core.metadatos import esquema_para

_SISTEMA_EDITOR = (
    "Eres un editor literario experto que trabaja en español. Mejoras la prosa "
    "conservando la voz del autor, el sentido y el punto de vista. Respondes "
    "ÚNICAMENTE con el texto resultante, sin comentarios, sin comillas y sin "
    "explicaciones."
)


@dataclass(frozen=True)
class Intencion:
    id: str
    etiqueta: str
    instruccion: str


# Intenciones de reescritura ofrecidas en el menú.
INTENCIONES_REESCRITURA: list[Intencion] = [
    Intencion("pulir", "Pulir",
              "Pule y mejora la redacción del texto: corrige torpezas, mejora el "
              "ritmo y la elección de palabras, sin cambiar el contenido ni alargarlo."),
    Intencion("condensar", "Condensar",
              "Reescribe el texto de forma más concisa, eliminando redundancias y "
              "palabras superfluas, conservando la información esencial."),
    Intencion("expandir", "Expandir",
              "Desarrolla y enriquece el texto con más detalle sensorial y matices, "
              "manteniendo el estilo y sin inventar hechos que lo contradigan."),
    Intencion("formal", "Registro más formal",
              "Reescribe el texto en un registro más formal y culto."),
    Intencion("coloquial", "Registro más coloquial",
              "Reescribe el texto en un registro más coloquial y natural."),
    Intencion("mostrar", "Mostrar, no contar",
              "Reescribe el texto aplicando el principio «muestra, no cuentes»: "
              "convierte afirmaciones y resúmenes en acción, gesto y detalle concreto."),
    Intencion("dialogo", "Naturalizar diálogo",
              "Reescribe el diálogo para que suene más natural y verosímil, "
              "diferenciando la voz de cada personaje si los hay."),
]


def intencion_por_id(id_intencion: str) -> Intencion:
    for it in INTENCIONES_REESCRITURA:
        if it.id == id_intencion:
            return it
    return INTENCIONES_REESCRITURA[0]


def mensajes_reescritura(texto: str, intencion: Intencion,
                         contexto: str = "") -> list[Mensaje]:
    """Construye los mensajes para reescribir una selección con una intención."""
    partes = [intencion.instruccion]
    if contexto:
        partes.append(f"\nContexto de la escena (no lo reescribas, solo tenlo en cuenta):\n{contexto}")
    partes.append(f"\nTexto a reescribir:\n{texto}")
    return [
        {"role": "system", "content": _SISTEMA_EDITOR},
        {"role": "user", "content": "\n".join(partes)},
    ]


# ─── Fase 2: dossier (sinopsis, fichas, coherencia) ──────────────────────────

_SISTEMA_SINOPSIS = (
    "Eres un editor literario que trabaja en español. Escribes sinopsis breves "
    "y claras. Respondes ÚNICAMENTE con la sinopsis, sin comentarios ni comillas."
)

_SISTEMA_ANALISTA = (
    "Eres un editor literario meticuloso que trabaja en español. Analizas el "
    "material de una novela y respondes de forma concreta, sin inventar datos "
    "que no aparezcan en el texto."
)


def mensajes_sinopsis(nombre: str, texto: str) -> list[Mensaje]:
    """Sinopsis de 1–3 frases de una escena o capítulo, para el campo Resumen."""
    return [
        {"role": "system", "content": _SISTEMA_SINOPSIS},
        {"role": "user", "content":
            f"Resume en 1 a 3 frases lo esencial de «{nombre}» (qué ocurre, a "
            f"quién y con qué consecuencia). Responde solo con la sinopsis.\n\n"
            f"Texto:\n{texto}"},
    ]


# Campos de ficha que la IA puede rellenar (solo texto libre; se excluyen los
# desplegables/numéricos, que el usuario elige a mano).
def campos_ficha(tipo: TipoElemento) -> list[tuple[str, str]]:
    campos = []
    for c in esquema_para(tipo):
        if c.tipo in ("line", "multiline"):
            campos.append((c.clave, c.etiqueta))
    return campos


def mensajes_ficha(tipo_etiqueta: str, nombre: str,
                   campos: list[tuple[str, str]], contexto: str) -> list[Mensaje]:
    """Propone valores para los campos de una ficha de personaje/ubicación."""
    lista = "\n".join(f"- {etiqueta}" for _clave, etiqueta in campos)
    return [
        {"role": "system", "content": _SISTEMA_ANALISTA},
        {"role": "user", "content":
            f"A partir del material siguiente sobre {tipo_etiqueta.lower()} "
            f"«{nombre}», propón el contenido de estos campos de su ficha:\n{lista}\n\n"
            "Devuelve una línea por campo con el formato «Campo: valor». Rellena "
            "solo los campos para los que el texto aporte información; omite los "
            "demás. No inventes datos que contradigan el material.\n\n"
            f"Material:\n{contexto}"},
    ]


def parsear_campos(respuesta: str, campos: list[tuple[str, str]]) -> dict[str, str]:
    """Convierte la respuesta «Campo: valor» en {clave: valor} para los campos dados."""
    etiqueta_a_clave = {etiqueta.lower(): clave for clave, etiqueta in campos}
    resultado: dict[str, str] = {}
    clave_actual: str | None = None
    buffer: list[str] = []

    def _volcar() -> None:
        if clave_actual is not None:
            valor = "\n".join(buffer).strip()
            if valor:
                resultado[clave_actual] = valor

    for linea in respuesta.splitlines():
        m = re.match(r"^\s*[-*]?\s*([\wÁÉÍÓÚÑáéíóúñ /()·-]+?)\s*:\s*(.*)$", linea)
        etiqueta = m.group(1).strip().lower() if m else None
        if m and etiqueta in etiqueta_a_clave:
            _volcar()
            clave_actual = etiqueta_a_clave[etiqueta]
            buffer = [m.group(2)]
        elif m:
            # Línea con forma «Etiqueta: …» pero de un campo desconocido: cierra el
            # campo en curso para no absorber contenido ajeno (p. ej. desplegables).
            _volcar()
            clave_actual = None
            buffer = []
        elif clave_actual is not None:
            buffer.append(linea)
    _volcar()
    return resultado


def mensajes_coherencia(nombre: str, ficha_texto: str,
                        escenas_texto: str) -> list[Mensaje]:
    """Contrasta la ficha de un personaje con sus apariciones en las escenas."""
    return [
        {"role": "system", "content": _SISTEMA_ANALISTA},
        {"role": "user", "content":
            f"Revisa la coherencia del personaje «{nombre}». Compara su ficha con "
            "lo que hace y dice en las escenas y señala posibles contradicciones "
            "(rasgos físicos, edad, personalidad, cronología, nombres). Enumera "
            "cada hallazgo en una línea empezando por «- » y cita brevemente la "
            "evidencia. Si no detectas incoherencias, dilo claramente.\n\n"
            f"FICHA:\n{ficha_texto}\n\nESCENAS:\n{escenas_texto}"},
    ]


# ─── Fase 4: chat con contexto (RAG) ─────────────────────────────────────────

_SISTEMA_CHAT = (
    "Eres el asistente de escritura de una novela. Respondes en español, de "
    "forma concreta y útil, basándote en el CONTEXTO del manuscrito que se te "
    "proporciona. Si la respuesta no está en el contexto, dilo con claridad en "
    "lugar de inventarla. Cuando cites algo, menciona el nombre de la escena, "
    "personaje o ubicación."
)


def mensajes_chat(pregunta: str, contexto: str,
                  historial: list[Mensaje] | None = None) -> list[Mensaje]:
    """Mensajes para una pregunta del chat, con el contexto recuperado y el
    historial reciente de la conversación."""
    mensajes: list[Mensaje] = [{"role": "system", "content": _SISTEMA_CHAT}]
    if historial:
        mensajes.extend(historial)
    if contexto:
        contenido = (f"CONTEXTO del manuscrito:\n{contexto}\n\n"
                     f"---\nPregunta: {pregunta}")
    else:
        contenido = f"Pregunta: {pregunta}"
    mensajes.append({"role": "user", "content": contenido})
    return mensajes


# ─── Tormenta de ideas ───────────────────────────────────────────────────────

_SISTEMA_IDEAS = (
    "Eres un asesor creativo de escritura de novela, en español. Ayudas al autor "
    "a desbloquearse con ideas concretas, variadas y accionables, respetando lo "
    "que ya está escrito. No reescribes el texto: propones caminos posibles."
)


def mensajes_tormenta(contexto: str, foco: str = "") -> list[Mensaje]:
    """Ideas para continuar la historia desde el punto actual (antiestancamiento)."""
    peticion = (
        "Propón entre 5 y 8 ideas concretas para continuar la historia desde este "
        "punto: próximas escenas posibles, complicaciones, giros, decisiones de los "
        "personajes y maneras de hacer avanzar las tramas. Enumera cada idea en una "
        "línea que empiece por «- », de forma específica y variada (evita ideas "
        "genéricas)."
    )
    if foco:
        peticion += f"\nCéntrate especialmente en: {foco}."
    return [
        {"role": "system", "content": _SISTEMA_IDEAS},
        {"role": "user", "content": f"{peticion}\n\nCONTEXTO DE LA NOVELA:\n{contexto}"},
    ]


# ─── Tormenta de ideas guiada (3 caminos → explorar uno) ─────────────────────

def mensajes_tres_caminos(contexto: str, foco: str = "") -> list[Mensaje]:
    """Pide EXACTAMENTE 3 caminos radicalmente distintos para continuar."""
    peticion = (
        "El autor está atascado. Propón EXACTAMENTE 3 caminos posibles para "
        "continuar la historia, RADICALMENTE DISTINTOS entre sí en dirección, "
        "tono o consecuencias (evita variaciones de la misma idea). Formato "
        "estricto: una línea por camino, así:\n"
        "1) Título breve — una frase que lo describa\n"
        "2) Título breve — una frase que lo describa\n"
        "3) Título breve — una frase que lo describa\n"
        "No añadas nada más."
    )
    if foco:
        peticion += f"\nTen en cuenta: {foco}."
    return [
        {"role": "system", "content": _SISTEMA_IDEAS},
        {"role": "user", "content": f"{peticion}\n\nCONTEXTO DE LA NOVELA:\n{contexto}"},
    ]


def parsear_opciones(respuesta: str) -> list[tuple[str, str]]:
    """Extrae [(título, descripción)] de la respuesta de los 3 caminos."""
    opciones: list[tuple[str, str]] = []
    for linea in respuesta.splitlines():
        m = re.match(r"^\s*\(?[1-3][)\.\-:]\s*(.+)$", linea)
        if not m:
            continue
        cuerpo = m.group(1).strip().lstrip("*").strip()
        titulo, desc = cuerpo, ""
        for sep in (" — ", " – ", " - ", ": "):
            if sep in cuerpo:
                titulo, desc = cuerpo.split(sep, 1)
                break
        opciones.append((titulo.strip(" *"), desc.strip()))
        if len(opciones) == 3:
            break
    return opciones


def mensajes_desarrollar_camino(contexto: str, titulo: str, descripcion: str,
                                foco: str = "") -> list[Mensaje]:
    """Desarrolla el camino elegido para ayudar a seguir escribiendo."""
    camino = titulo + (f" — {descripcion}" if descripcion else "")
    peticion = (
        f"El autor ha elegido continuar por este camino:\n«{camino}»\n\n"
        "Ayúdale a escribir por ahí. Devuelve, en español y sin encabezados "
        "de sección:\n"
        "1) Un párrafo de continuación en el estilo del manuscrito que arranque "
        "ese camino (listo para pegar en el texto).\n"
        "2) Después, una línea «— Hacia dónde puede ir —» y 3 o 4 viñetas «- » "
        "con posibles desarrollos y una complicación.\n"
        "No reescribas lo ya escrito; continúa a partir de ahí."
    )
    if foco:
        peticion += f"\nContexto del punto de atasco: {foco}."
    return [
        {"role": "system", "content": _SISTEMA_IDEAS},
        {"role": "user", "content": f"{peticion}\n\nCONTEXTO DE LA NOVELA:\n{contexto}"},
    ]


# ─── Revisión y corrección (ortotipográfica + gramatical) ────────────────────

_SISTEMA_CORRECTOR = (
    "Eres un corrector profesional de español. Corriges ortografía, tildes, "
    "puntuación y ortotipografía (comillas angulares «», rayas de diálogo —, "
    "guiones, espacios, mayúsculas y minúsculas) y gramática (concordancia, "
    "tiempos verbales, preposiciones, queísmo/dequeísmo). NO cambias el estilo, "
    "el vocabulario ni el contenido, ni reescribes: solo corriges errores y "
    "conservas la voz del autor y el formato. Respondes ÚNICAMENTE con el texto "
    "corregido, sin comentarios ni comillas de encuadre."
)


def mensajes_correccion(texto: str) -> list[Mensaje]:
    """Revisión y corrección ortotipográfica y gramatical de la selección."""
    return [
        {"role": "system", "content": _SISTEMA_CORRECTOR},
        {"role": "user", "content": f"Corrige el siguiente texto:\n\n{texto}"},
    ]
