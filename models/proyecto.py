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

# Paleta por defecto para nuevas tramas (colores de sistema, buen contraste).
COLORES_TRAMA = [
    "#FF3B30", "#FF9500", "#FFCC00", "#34C759", "#00C7BE",
    "#30B0C7", "#007AFF", "#5856D6", "#AF52DE", "#FF2D55",
]

# Roles de las carpetas estándar del dossier (independientes del nombre visible).
ROL_MANUSCRITO  = "manuscrito"
ROL_PERSONAJES  = "personajes"
ROL_UBICACIONES = "ubicaciones"
ROL_NOTAS       = "notas"


@dataclass
class Trama:
    """Una trama o hilo argumental, con un color para el visor."""
    nombre: str
    color: str = "#007AFF"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def a_dict(self) -> dict:
        return {"id": self.id, "nombre": self.nombre, "color": self.color}

    @classmethod
    def desde_dict(cls, d: dict) -> "Trama":
        return cls(
            id=d.get("id", str(uuid.uuid4())),
            nombre=d.get("nombre", "Trama"),
            color=d.get("color", "#007AFF"),
        )


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
    tramas: list[Trama] = field(default_factory=list)

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

    # ─── Carpetas estándar del dossier ────────────────────────────────────────

    def carpeta_por_rol(self, rol: str) -> Optional[ItemProyecto]:
        """Devuelve la carpeta estándar identificada por su rol."""
        if not self.raiz:
            return None
        for hijo in self.raiz.hijos:
            if hijo.metadatos.get("rol") == rol:
                return hijo
        return None

    # ─── Consultas del manuscrito y elementos ─────────────────────────────────

    def escenas_en_orden(self) -> list[ItemProyecto]:
        """
        Devuelve las escenas del manuscrito en orden de lectura
        (recorrido en profundidad de la sección «Manuscrito»).
        """
        manuscrito = self.carpeta_por_rol(ROL_MANUSCRITO)
        if not manuscrito:
            return []
        escenas: list[ItemProyecto] = []

        def recorrer(nodo: ItemProyecto) -> None:
            for hijo in sorted(nodo.hijos, key=lambda h: h.orden):
                if hijo.tipo == TipoElemento.ESCENA:
                    escenas.append(hijo)
                recorrer(hijo)

        recorrer(manuscrito)
        return escenas

    def _hojas_de(self, rol: str, tipo: TipoElemento) -> list[ItemProyecto]:
        carpeta = self.carpeta_por_rol(rol)
        if not carpeta:
            return []
        resultado: list[ItemProyecto] = []

        def recorrer(nodo: ItemProyecto) -> None:
            for hijo in sorted(nodo.hijos, key=lambda h: h.orden):
                if hijo.tipo == tipo:
                    resultado.append(hijo)
                recorrer(hijo)

        recorrer(carpeta)
        return resultado

    def personajes(self) -> list[ItemProyecto]:
        return self._hojas_de(ROL_PERSONAJES, TipoElemento.PERSONAJE)

    def ubicaciones(self) -> list[ItemProyecto]:
        return self._hojas_de(ROL_UBICACIONES, TipoElemento.UBICACION)

    # ─── Tramas ───────────────────────────────────────────────────────────────

    def trama_por_id(self, trama_id: str) -> Optional[Trama]:
        for t in self.tramas:
            if t.id == trama_id:
                return t
        return None

    def agregar_trama(self, nombre: str, color: str = "") -> Trama:
        if not color:
            color = COLORES_TRAMA[len(self.tramas) % len(COLORES_TRAMA)]
        trama = Trama(nombre=nombre, color=color)
        self.tramas.append(trama)
        return trama

    def eliminar_trama(self, trama_id: str) -> None:
        """Elimina una trama y la desvincula de todas las escenas."""
        self.tramas = [t for t in self.tramas if t.id != trama_id]
        for escena in self.escenas_en_orden():
            refs = escena.metadatos.get("tramas")
            if isinstance(refs, list) and trama_id in refs:
                refs.remove(trama_id)

    # ─── Persistencia ─────────────────────────────────────────────────────────

    def guardar(self) -> None:
        """Serializa y guarda el proyecto en proyecto.json."""
        datos = {
            "id":          self.id,
            "nombre":      self.nombre,
            "version":     self.version,
            "descripcion": self.descripcion,
            "autor":       self.autor,
            "tramas":      [t.a_dict() for t in self.tramas],
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
            tramas=[Trama.desde_dict(t) for t in datos.get("tramas", [])],
        )
        arbol_dict = datos.get("arbol", {})
        if arbol_dict:
            proyecto.raiz = ItemProyecto.desde_dict(arbol_dict)
        return proyecto

    @classmethod
    def nuevo(cls, nombre: str, ruta: Path, autor: str = "") -> "Proyecto":
        """Crea un nuevo proyecto con la estructura de dossier estándar."""
        ruta.mkdir(parents=True, exist_ok=True)

        proyecto = cls(nombre=nombre, ruta=ruta, autor=autor)

        # Subdirectorios en disco (los documentos viven aquí; el árbol da jerarquía)
        for subdir in ("manuscrito", "personajes", "ubicaciones", "notas"):
            (ruta / subdir).mkdir(exist_ok=True)

        # Carpetas raíz del dossier, con su rol para identificarlas siempre.
        carpetas = [
            ("Manuscrito",            ROL_MANUSCRITO,  "manuscrito"),
            ("Personajes",            ROL_PERSONAJES,  "personajes"),
            ("Ubicaciones",           ROL_UBICACIONES, "ubicaciones"),
            ("Notas e investigación", ROL_NOTAS,       "notas"),
        ]
        for nombre_carpeta, rol, subdir in carpetas:
            carpeta = ItemProyecto(
                nombre=nombre_carpeta,
                tipo=TipoElemento.CARPETA,
                ruta_relativa=subdir,
                metadatos={"rol": rol},
            )
            proyecto.raiz.agregar_hijo(carpeta)  # type: ignore[union-attr]

        proyecto.guardar()
        return proyecto
