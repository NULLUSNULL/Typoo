# models/documento.py
# Modelo de datos para un elemento (documento/nodo) dentro de un proyecto literario

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional

from core.constantes import TipoElemento


@dataclass
class ItemProyecto:
    """
    Representa un nodo del árbol del proyecto: capítulo, escena, nota, etc.
    Cada item tiene una ruta a un archivo .md en disco.
    """

    nombre: str
    tipo: TipoElemento
    ruta_relativa: str = ""          # Ruta relativa al directorio del proyecto
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    padre_id: Optional[str] = None
    orden: int = 0
    hijos: list["ItemProyecto"] = field(default_factory=list)
    expandido: bool = True           # Estado del nodo en el árbol de la UI
    metadatos: dict = field(default_factory=dict)

    def es_contenedor(self) -> bool:
        """Indica si este elemento puede contener hijos."""
        return self.tipo in (
            TipoElemento.PROYECTO,
            TipoElemento.CARPETA,
            TipoElemento.CAPITULO,
        )

    def es_hoja(self) -> bool:
        """Indica si este elemento es un archivo editable (sin hijos)."""
        return not self.es_contenedor()

    def agregar_hijo(self, hijo: "ItemProyecto") -> None:
        hijo.padre_id = self.id
        hijo.orden = len(self.hijos)
        self.hijos.append(hijo)

    def eliminar_hijo(self, hijo_id: str) -> bool:
        for i, hijo in enumerate(self.hijos):
            if hijo.id == hijo_id:
                self.hijos.pop(i)
                # Reajustar orden
                for j, h in enumerate(self.hijos):
                    h.orden = j
                return True
        return False

    def buscar_descendiente(self, id_buscado: str) -> Optional["ItemProyecto"]:
        """Búsqueda recursiva por ID en el subárbol."""
        if self.id == id_buscado:
            return self
        for hijo in self.hijos:
            encontrado = hijo.buscar_descendiente(id_buscado)
            if encontrado:
                return encontrado
        return None

    def a_dict(self) -> dict:
        """Serializa el item a un diccionario para guardar en JSON."""
        return {
            "id":           self.id,
            "nombre":       self.nombre,
            "tipo":         self.tipo.value,
            "ruta_relativa": self.ruta_relativa,
            "padre_id":     self.padre_id,
            "orden":        self.orden,
            "expandido":    self.expandido,
            "metadatos":    self.metadatos,
            "hijos":        [h.a_dict() for h in self.hijos],
        }

    @classmethod
    def desde_dict(cls, datos: dict) -> "ItemProyecto":
        """Deserializa un item desde un diccionario JSON."""
        item = cls(
            id=datos.get("id", str(uuid.uuid4())),
            nombre=datos["nombre"],
            tipo=TipoElemento(datos["tipo"]),
            ruta_relativa=datos.get("ruta_relativa", ""),
            padre_id=datos.get("padre_id"),
            orden=datos.get("orden", 0),
            expandido=datos.get("expandido", True),
            metadatos=datos.get("metadatos", {}),
        )
        for hijo_dict in datos.get("hijos", []):
            item.hijos.append(cls.desde_dict(hijo_dict))
        return item
