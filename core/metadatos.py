# core/metadatos.py
# Esquema de metadatos propios de cada tipo de elemento del proyecto.
#
# Cada tipo de elemento (escena, personaje, ubicación…) define sus propios
# campos. El panel lateral de detalles construye el formulario a partir de
# este esquema y guarda los valores en `ItemProyecto.metadatos`, que se
# persiste en `proyecto.json`.

from __future__ import annotations

from dataclasses import dataclass, field

from core.constantes import TipoElemento


@dataclass(frozen=True)
class CampoMeta:
    """Definición de un campo de metadatos."""
    clave: str
    etiqueta: str
    tipo: str = "line"          # line | multiline | combo | int
    opciones: tuple[str, ...] = ()
    marcador: str = ""          # placeholder / texto de ayuda


# Etiqueta legible para cada tipo de elemento.
ETIQUETAS_TIPO = {
    TipoElemento.PROYECTO:  "Proyecto",
    TipoElemento.CARPETA:   "Carpeta",
    TipoElemento.CAPITULO:  "Capítulo",
    TipoElemento.ESCENA:    "Escena",
    TipoElemento.NOTA:      "Nota",
    TipoElemento.PERSONAJE: "Personaje",
    TipoElemento.UBICACION: "Ubicación",
}


# Esquema de campos por tipo de elemento.
ESQUEMAS: dict[TipoElemento, list[CampoMeta]] = {
    TipoElemento.CAPITULO: [
        CampoMeta("resumen", "Resumen", "multiline", marcador="¿Qué ocurre en este capítulo?"),
        CampoMeta("estado", "Estado", "combo",
                  ("Esbozado", "Borrador", "En revisión", "Terminado")),
        CampoMeta("objetivo_palabras", "Objetivo de palabras", "int"),
        CampoMeta("avance_trama", "Avance de la trama", "multiline"),
    ],
    TipoElemento.ESCENA: [
        CampoMeta("resumen", "Resumen", "multiline", marcador="Sinopsis breve de la escena"),
        CampoMeta("estado", "Estado", "combo",
                  ("Borrador", "En revisión", "Terminada")),
        CampoMeta("pov", "Punto de vista", "line", marcador="Personaje narrador"),
        CampoMeta("ubicacion", "Ubicación", "line"),
        CampoMeta("personajes", "Personajes presentes", "line", marcador="Separados por comas"),
        CampoMeta("momento", "Momento / fecha", "line"),
        CampoMeta("objetivo", "Objetivo de la escena", "multiline",
                  marcador="¿Qué debe conseguir esta escena?"),
    ],
    TipoElemento.PERSONAJE: [
        CampoMeta("nombre_completo", "Nombre completo", "line"),
        CampoMeta("alias", "Alias / apodo", "line"),
        CampoMeta("rol", "Rol", "combo",
                  ("Protagonista", "Antagonista", "Secundario", "Figurante")),
        CampoMeta("edad", "Edad", "line"),
        CampoMeta("ocupacion", "Ocupación", "line"),
        CampoMeta("apariencia", "Apariencia", "multiline"),
        CampoMeta("personalidad", "Personalidad", "multiline"),
        CampoMeta("motivacion", "Motivación / objetivo", "multiline"),
        CampoMeta("arco", "Arco de personaje", "multiline"),
    ],
    TipoElemento.UBICACION: [
        CampoMeta("tipo_lugar", "Tipo de lugar", "combo",
                  ("Ciudad", "Pueblo", "Edificio", "Interior", "Natural", "Otro")),
        CampoMeta("region", "Región / mundo", "line"),
        CampoMeta("descripcion", "Descripción", "multiline"),
        CampoMeta("atmosfera", "Atmósfera", "line", marcador="Tono, clima, sensación"),
        CampoMeta("relevancia", "Relevancia en la trama", "multiline"),
    ],
    TipoElemento.NOTA: [
        CampoMeta("categoria", "Categoría", "line", marcador="Investigación, idea, pendiente…"),
        CampoMeta("resumen", "Resumen", "multiline"),
        CampoMeta("etiquetas", "Etiquetas", "line", marcador="Separadas por comas"),
    ],
}


def esquema_para(tipo: TipoElemento) -> list[CampoMeta]:
    """Devuelve la lista de campos de metadatos para un tipo de elemento."""
    return ESQUEMAS.get(tipo, [])


def etiqueta_tipo(tipo: TipoElemento) -> str:
    """Nombre legible del tipo de elemento."""
    return ETIQUETAS_TIPO.get(tipo, tipo.value.capitalize())
