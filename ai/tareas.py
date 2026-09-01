# ai/tareas.py
# Construcción de los mensajes (prompts) para las tareas de IA de alto nivel.
# Se mantienen en español y orientados a edición literaria.

from __future__ import annotations

from dataclasses import dataclass

from ai.proveedores import Mensaje

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
