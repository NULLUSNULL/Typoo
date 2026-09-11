# ai/contexto.py
# Utilidades para armar el contexto que se envía a la IA a partir del proyecto.

from __future__ import annotations

from core.metadatos import esquema_para
from models.documento import ItemProyecto


def truncar(texto: str, limite: int) -> str:
    """Recorta el texto a `limite` caracteres añadiendo una marca si se corta."""
    texto = texto or ""
    if len(texto) <= limite:
        return texto
    return texto[:limite].rstrip() + "\n[…]"


def estimar_max_tokens(
    texto: str, *, minimo: int = 1024, maximo: int = 4096,
    multiplicador: float = 1.7,
) -> int:
    """Estima un límite de tokens de salida proporcional a la longitud del
    texto de entrada, en vez de usar siempre un máximo fijo.

    Con un `max_tokens` fijo y bajo, la respuesta de la IA se corta a mitad
    en textos algo largos (reescribir/expandir una escena extensa, un informe
    de coherencia de un capítulo con varias escenas, continuar una historia…):
    el proveedor deja de generar en cuanto alcanza el límite, sin terminar la
    idea. Aquí se calcula un presupuesto acorde al texto de entrada (con
    margen, porque reescribir o continuar suele generar más texto del que se
    recibe) y se acota entre `minimo` y `maximo` para no disparar la
    latencia/coste sin límite en textos desproporcionados.

    La estimación de ~4 caracteres por token es aproximada (varía según
    idioma y proveedor); el objetivo es evitar el corte, no ser exacto.
    """
    texto = texto or ""
    if not texto:
        return minimo
    tokens_estimados = len(texto) / 4
    objetivo = int(tokens_estimados * multiplicador)
    return max(minimo, min(objetivo, maximo))


def ficha_a_texto(item: ItemProyecto) -> str:
    """Representación legible de los metadatos de una ficha (personaje/ubicación)."""
    lineas = [f"Nombre: {item.nombre}"]
    metadatos = item.metadatos or {}
    for campo in esquema_para(item.tipo):
        valor = metadatos.get(campo.clave)
        if isinstance(valor, str) and valor.strip():
            lineas.append(f"{campo.etiqueta}: {valor.strip()}")
    return "\n".join(lineas)
