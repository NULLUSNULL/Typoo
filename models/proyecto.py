# models/proyecto.py
# Modelo principal del proyecto literario

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from core.constantes import NOMBRE_ARCHIVO_PROYECTO, TipoElemento, VERSION_APP
from models.documento import ItemProyecto


@dataclass
class Proyecto:
    """
    Representa un proyecto literario completo.
    Almacena la ruta del directorio y el árbol jerárquico de documentos.
    """

    nombre: str
    ruta: Path
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: str = VERSION_APP
    descripcion: str = ""
    autor: str = ""
    raiz: Optional[ItemProyecto] = None

    def __post_init__(self) -> None:
        if self.raiz is None:
            self.raiz = ItemProyecto(
                nombre=self.nombre,
                tipo=TipoElemento.PROYECTO,
                ruta_relativa="",
                id=self.id,
            )

    @property
    def archivo_proyecto(self) -> Path:
        return self.ruta / NOMBRE_ARCHIVO_PROYECTO

    def buscar_item(self, id_buscado: str) -> Optional[ItemProyecto]:
        if self.raiz:
            return self.raiz.buscar_descendiente(id_buscado)
        return None

    def ruta_absoluta_item(self, item: ItemProyecto) -> Path:
        return self.ruta / item.ruta_relativa

    def guardar(self) -> None:
        """Serializa y guarda el proyecto en proyecto.json."""
        datos = {
            "id":          self.id,
            "nombre":      self.nombre,
            "version":     self.version,
            "descripcion": self.descripcion,
            "autor":       self.autor,
            "arbol":       self.raiz.a_dict() if self.raiz else {},
        }
        self.archivo_proyecto.write_text(
            json.dumps(datos, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    @classmethod
    def cargar(cls, ruta: Path) -> "Proyecto":
        """Carga un proyecto desde su directorio."""
        archivo = ruta / NOMBRE_ARCHIVO_PROYECTO
        datos = json.loads(archivo.read_text(encoding="utf-8"))
        proyecto = cls(
            id=datos.get("id", str(uuid.uuid4())),
            nombre=datos["nombre"],
            ruta=ruta,
            version=datos.get("version", VERSION_APP),
            descripcion=datos.get("descripcion", ""),
            autor=datos.get("autor", ""),
        )
        arbol_dict = datos.get("arbol", {})
        if arbol_dict:
            proyecto.raiz = ItemProyecto.desde_dict(arbol_dict)
        return proyecto

    @classmethod
    def nuevo(cls, nombre: str, ruta: Path, autor: str = "") -> "Proyecto":
        """Crea un nuevo proyecto vacío en la ruta especificada."""
        ruta.mkdir(parents=True, exist_ok=True)

        proyecto = cls(nombre=nombre, ruta=ruta, autor=autor)

        # Crear subdirectorios estándar
        for subdir in ("capitulos", "escenas", "notas", "personajes", "ubicaciones"):
            (ruta / subdir).mkdir(exist_ok=True)

        # Crear carpetas en el árbol
        carpetas_tipo = {
            "Capítulos":    (TipoElemento.CARPETA, "capitulos"),
            "Escenas":      (TipoElemento.CARPETA, "escenas"),
            "Notas":        (TipoElemento.CARPETA, "notas"),
            "Personajes":   (TipoElemento.CARPETA, "personajes"),
            "Ubicaciones":  (TipoElemento.CARPETA, "ubicaciones"),
        }
        for nombre_carpeta, (tipo, subdir) in carpetas_tipo.items():
            carpeta = ItemProyecto(nombre=nombre_carpeta, tipo=tipo, ruta_relativa=subdir)
            proyecto.raiz.agregar_hijo(carpeta)  # type: ignore[union-attr]

        proyecto.guardar()
        return proyecto
