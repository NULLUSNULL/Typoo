# ai/recuperacion.py
# Recuperación léxica ligera (estilo BM25) sobre el proyecto para dar contexto
# al chat del asistente. Sin dependencias externas: funciona sin conexión.

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Callable, Optional

from ai.contexto import ficha_a_texto, truncar
from core.constantes import TipoElemento
from models.proyecto import Proyecto

# Palabras vacías frecuentes en español (se ignoran al indexar/consultar).
_STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al",
    "a", "ante", "con", "contra", "en", "entre", "por", "para", "segun", "sin",
    "sobre", "tras", "y", "e", "o", "u", "que", "qué", "quien", "quién", "cual",
    "cuál", "como", "cómo", "cuando", "cuándo", "donde", "dónde", "es", "son",
    "ser", "estar", "esta", "este", "esto", "esa", "ese", "eso", "su", "sus",
    "se", "lo", "le", "les", "me", "te", "nos", "mi", "tu", "no", "si", "sí",
    "ya", "muy", "mas", "más", "pero", "porque", "cuanto", "hay", "ha", "han",
}

_PalabraRe = re.compile(r"[a-z0-9ñ]+")


def _normalizar(texto: str) -> list[str]:
    """Minúsculas, sin acentos, en tokens útiles (sin palabras vacías cortas)."""
    texto = texto.lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    palabras = _PalabraRe.findall(texto)
    return [p for p in palabras if len(p) >= 3 and p not in _STOPWORDS]


@dataclass
class Fragmento:
    titulo: str
    texto: str
    tokens: list[str] = field(default_factory=list)


def construir_corpus(
    proyecto: Proyecto,
    leer_documento: Callable[[object], str],
    max_chars_escena: int = 2000,
) -> list[Fragmento]:
    """Crea los fragmentos indexables del proyecto (escenas, capítulos, dossier)."""
    fragmentos: list[Fragmento] = []

    def añadir(titulo: str, texto: str) -> None:
        texto = (texto or "").strip()
        if texto:
            frag = Fragmento(titulo=titulo, texto=texto)
            frag.tokens = _normalizar(f"{titulo}\n{texto}")
            if frag.tokens:
                fragmentos.append(frag)

    # Escenas del manuscrito (sinopsis + texto).
    for escena in proyecto.escenas_en_orden():
        resumen = (escena.metadatos or {}).get("resumen", "")
        try:
            cuerpo = leer_documento(escena) or ""
        except Exception:
            cuerpo = ""
        texto = (f"{resumen}\n{cuerpo}" if resumen else cuerpo)
        añadir(f"Escena «{escena.nombre}»", truncar(texto, max_chars_escena))

    # Fichas de personajes y ubicaciones.
    for personaje in proyecto.personajes():
        añadir(f"Personaje «{personaje.nombre}»", ficha_a_texto(personaje))
    for ubicacion in proyecto.ubicaciones():
        añadir(f"Ubicación «{ubicacion.nombre}»", ficha_a_texto(ubicacion))

    return fragmentos


def recuperar(
    corpus: list[Fragmento],
    pregunta: str,
    *,
    k: int = 6,
    presupuesto_chars: int = 6000,
) -> list[Fragmento]:
    """Devuelve los fragmentos más relevantes para la pregunta (BM25 simplificado)."""
    if not corpus:
        return []
    consulta = set(_normalizar(pregunta))
    if not consulta:
        return corpus[:k]

    n = len(corpus)
    # Frecuencia de documento por término.
    df: dict[str, int] = {}
    for frag in corpus:
        for term in set(frag.tokens):
            df[term] = df.get(term, 0) + 1
    long_media = sum(len(f.tokens) for f in corpus) / n
    k1, b = 1.5, 0.75

    puntuados: list[tuple[float, Fragmento]] = []
    for frag in corpus:
        tf: dict[str, int] = {}
        for t in frag.tokens:
            tf[t] = tf.get(t, 0) + 1
        dl = len(frag.tokens) or 1
        score = 0.0
        for term in consulta:
            if term not in tf:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            f = tf[term]
            score += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / long_media))
        if score > 0:
            puntuados.append((score, frag))

    puntuados.sort(key=lambda p: p[0], reverse=True)

    seleccion: list[Fragmento] = []
    total = 0
    for _score, frag in puntuados[:k]:
        coste = len(frag.titulo) + len(frag.texto)
        if seleccion and total + coste > presupuesto_chars:
            break
        seleccion.append(frag)
        total += coste
    return seleccion


def formatear_contexto(fragmentos: list[Fragmento]) -> str:
    """Une los fragmentos recuperados en un bloque de contexto legible."""
    return "\n\n".join(f"### {f.titulo}\n{f.texto}" for f in fragmentos)
