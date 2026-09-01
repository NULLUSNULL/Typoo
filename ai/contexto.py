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


def ficha_a_texto(item: ItemProyecto) -> str:
    """Representación legible de los metadatos de una ficha (personaje/ubicación)."""
    lineas = [f"Nombre: {item.nombre}"]
    metadatos = item.metadatos or {}
    for campo in esquema_para(item.tipo):
        valor = metadatos.get(campo.clave)
        if isinstance(valor, str) and valor.strip():
            lineas.append(f"{campo.etiqueta}: {valor.strip()}")
    return "\n".join(lineas)
