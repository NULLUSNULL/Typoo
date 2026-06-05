# services/gestor_proyectos.py
# Servicio que gestiona el ciclo de vida de proyectos literarios

from __future__ import annotations

from pathlib import Path
from typing import Optional

from core.constantes import NOMBRE_ARCHIVO_PROYECTO, TipoElemento, EXTENSION_DOCUMENTO
from core.logger import logger
from models.documento import ItemProyecto
from models.proyecto import Proyecto


class GestorProyectos:
    """
    Servicio central para crear, abrir, guardar y manipular proyectos.
    Mantiene el proyecto actualmente activo en memoria.
    """

    def __init__(self) -> None:
        self._proyecto_activo: Optional[Proyecto] = None

    @property
    def proyecto_activo(self) -> Optional[Proyecto]:
        return self._proyecto_activo

    @property
    def hay_proyecto(self) -> bool:
        return self._proyecto_activo is not None

    # ─── Ciclo de vida del proyecto ───────────────────────────────────────────

    def nuevo_proyecto(self, nombre: str, ruta: Path, autor: str = "") -> Proyecto:
        """Crea un proyecto nuevo y lo establece como activo."""
        proyecto = Proyecto.nuevo(nombre=nombre, ruta=ruta, autor=autor)
        self._proyecto_activo = proyecto
        logger.info("Proyecto nuevo creado: %s en %s", nombre, ruta)
        return proyecto

    def abrir_proyecto(self, ruta: Path) -> Proyecto:
        """Carga un proyecto existente desde su directorio."""
        if not (ruta / NOMBRE_ARCHIVO_PROYECTO).exists():
            raise FileNotFoundError(
                f"No se encontró un proyecto válido en: {ruta}"
            )
        proyecto = Proyecto.cargar(ruta)
        self._proyecto_activo = proyecto
        logger.info("Proyecto abierto: %s desde %s", proyecto.nombre, ruta)
        return proyecto

    def guardar_proyecto(self) -> None:
        """Guarda la metadata del proyecto activo."""
        if self._proyecto_activo:
            self._proyecto_activo.guardar()
            logger.debug("Proyecto guardado: %s", self._proyecto_activo.nombre)

    def cerrar_proyecto(self) -> None:
        """Cierra el proyecto activo y limpia el estado."""
        if self._proyecto_activo:
            logger.info("Cerrando proyecto: %s", self._proyecto_activo.nombre)
        self._proyecto_activo = None

    # ─── Gestión de elementos ─────────────────────────────────────────────────

    def crear_elemento(
        self,
        nombre: str,
        tipo: TipoElemento,
        padre_id: str,
        subdir: str = "",
    ) -> Optional[ItemProyecto]:
        """
        Crea un nuevo item (capítulo, escena, nota, etc.) en el proyecto activo.
        Genera el archivo .md correspondiente en disco.
        """
        if not self._proyecto_activo:
            return None

        proyecto = self._proyecto_activo
        padre = proyecto.buscar_item(padre_id)
        if not padre:
            logger.error("Padre no encontrado con ID: %s", padre_id)
            return None

        # Los contenedores (capítulos, carpetas) no tienen archivo propio:
        # son nodos del árbol que agrupan documentos.
        if tipo in (TipoElemento.CAPITULO, TipoElemento.CARPETA):
            nuevo_item = ItemProyecto(nombre=nombre, tipo=tipo, ruta_relativa="")
            padre.agregar_hijo(nuevo_item)
            proyecto.guardar()
            logger.info("Contenedor creado: %s (%s)", nombre, tipo.value)
            return nuevo_item

        # Determinar subdirectorio en disco según el tipo
        tipo_a_subdir = {
            TipoElemento.ESCENA:     "manuscrito",
            TipoElemento.NOTA:       "notas",
            TipoElemento.PERSONAJE:  "personajes",
            TipoElemento.UBICACION:  "ubicaciones",
        }
        if not subdir:
            subdir = tipo_a_subdir.get(tipo, "notas")

        # Generar nombre de archivo seguro
        nombre_archivo = self._nombre_seguro(nombre) + EXTENSION_DOCUMENTO
        ruta_relativa = f"{subdir}/{nombre_archivo}"
        ruta_absoluta = proyecto.ruta / ruta_relativa

        # Evitar colisión de nombres
        contador = 1
        while ruta_absoluta.exists():
            nombre_archivo = f"{self._nombre_seguro(nombre)}_{contador}{EXTENSION_DOCUMENTO}"
            ruta_relativa = f"{subdir}/{nombre_archivo}"
            ruta_absoluta = proyecto.ruta / ruta_relativa
            contador += 1

        # Crear el archivo en disco con plantilla inicial
        plantilla = self._plantilla_inicial(nombre, tipo)
        ruta_absoluta.write_text(plantilla, encoding="utf-8")

        # Crear el nodo en el árbol
        nuevo_item = ItemProyecto(
            nombre=nombre,
            tipo=tipo,
            ruta_relativa=ruta_relativa,
        )
        padre.agregar_hijo(nuevo_item)
        proyecto.guardar()

        logger.info("Elemento creado: %s (%s)", nombre, tipo.value)
        return nuevo_item

    def renombrar_elemento(self, item_id: str, nuevo_nombre: str) -> bool:
        """Renombra un item sin mover su archivo en disco."""
        if not self._proyecto_activo:
            return False
        item = self._proyecto_activo.buscar_item(item_id)
        if not item:
            return False
        item.nombre = nuevo_nombre
        self._proyecto_activo.guardar()
        return True

    def eliminar_elemento(self, item_id: str) -> bool:
        """Elimina un item del árbol y su archivo en disco."""
        if not self._proyecto_activo:
            return False
        proyecto = self._proyecto_activo
        item = proyecto.buscar_item(item_id)
        if not item or not item.padre_id:
            return False

        # Eliminar archivo si existe
        if item.ruta_relativa:
            ruta = proyecto.ruta / item.ruta_relativa
            if ruta.exists() and ruta.is_file():
                ruta.unlink()

        # Quitar del árbol
        padre = proyecto.buscar_item(item.padre_id)
        if padre:
            padre.eliminar_hijo(item_id)

        proyecto.guardar()
        logger.info("Elemento eliminado: %s", item.nombre)
        return True

    # ─── Lectura y escritura de documentos ────────────────────────────────────

    def leer_documento(self, item: ItemProyecto) -> str:
        """Lee el contenido de un archivo .md."""
        if not self._proyecto_activo:
            return ""
        ruta = self._proyecto_activo.ruta / item.ruta_relativa
        if ruta.exists():
            return ruta.read_text(encoding="utf-8")
        return ""

    def guardar_documento(self, item: ItemProyecto, contenido: str) -> bool:
        """Escribe el contenido de un documento en disco."""
        if not self._proyecto_activo:
            return False
        try:
            ruta = self._proyecto_activo.ruta / item.ruta_relativa
            ruta.write_text(contenido, encoding="utf-8")
            return True
        except OSError as e:
            logger.error("Error al guardar documento: %s", e)
            return False

    # ─── Utilidades ──────────────────────────────────────────────────────────

    @staticmethod
    def _nombre_seguro(nombre: str) -> str:
        """Convierte un nombre humano a un nombre de archivo válido."""
        import re
        nombre = nombre.lower().strip()
        nombre = re.sub(r"[áàäâ]", "a", nombre)
        nombre = re.sub(r"[éèëê]", "e", nombre)
        nombre = re.sub(r"[íìïî]", "i", nombre)
        nombre = re.sub(r"[óòöô]", "o", nombre)
        nombre = re.sub(r"[úùüû]", "u", nombre)
        nombre = re.sub(r"ñ", "n", nombre)
        nombre = re.sub(r"[^a-z0-9_\-]", "_", nombre)
        nombre = re.sub(r"_+", "_", nombre)
        return nombre[:60]

    @staticmethod
    def _plantilla_inicial(nombre: str, tipo: TipoElemento) -> str:
        """Genera el contenido inicial de un documento nuevo según su tipo."""
        plantillas = {
            TipoElemento.CAPITULO:  f"# {nombre}\n\n",
            TipoElemento.ESCENA:    f"## {nombre}\n\n",
            TipoElemento.NOTA:      f"# Nota: {nombre}\n\n",
            TipoElemento.PERSONAJE: (
                f"# {nombre}\n\n"
                "**Edad:** \n\n"
                "**Descripción física:** \n\n"
                "**Personalidad:** \n\n"
                "**Historia:** \n\n"
            ),
            TipoElemento.UBICACION: (
                f"# {nombre}\n\n"
                "**Descripción:** \n\n"
                "**Clima:** \n\n"
                "**Notas:** \n\n"
            ),
        }
        return plantillas.get(tipo, f"# {nombre}\n\n")
