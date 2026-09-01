# ai/modelos.py
# Catálogo y gestión de los modelos de IA embebidos (GGUF, ejecutados con
# llama.cpp). La descarga usa solo la biblioteca estándar; llama-cpp-python es
# una dependencia opcional que solo se necesita para *ejecutar* un modelo.

from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

Progreso = Optional[Callable[[int, int], None]]  # (leido, total)
Cancelar = Optional[Callable[[], bool]]


@dataclass(frozen=True)
class InfoModelo:
    id: str
    etiqueta: str
    nivel: str            # "ligero" | "medio" | "grande"
    descripcion: str
    ram: str              # recomendación de memoria
    repo: str             # repositorio de Hugging Face
    archivo: str          # nombre del .gguf
    tamano_gb: float      # tamaño aproximado (informativo)
    n_ctx: int = 4096

    @property
    def url(self) -> str:
        return f"https://huggingface.co/{self.repo}/resolve/main/{self.archivo}"


# Tres niveles pensados para edición literaria en español. Son cuantizaciones
# Q4_K_M (buen equilibrio calidad/tamaño); los identificadores de archivo pueden
# actualizarse con el tiempo.
CATALOGO: list[InfoModelo] = [
    InfoModelo(
        "ligero", "Ligero · Llama 3.2 3B Instruct", "ligero",
        "Rápido y ligero. Bien para pulir y sugerencias breves.",
        "Recomendado: 8 GB de RAM.",
        "bartowski/Llama-3.2-3B-Instruct-GGUF",
        "Llama-3.2-3B-Instruct-Q4_K_M.gguf", 2.0),
    InfoModelo(
        "medio", "Medio · Qwen2.5 7B Instruct", "medio",
        "Equilibrado, buen español. Reescritura y análisis con solvencia.",
        "Recomendado: 16 GB de RAM.",
        "bartowski/Qwen2.5-7B-Instruct-GGUF",
        "Qwen2.5-7B-Instruct-Q4_K_M.gguf", 4.7),
    InfoModelo(
        "grande", "Grande · Qwen2.5 14B Instruct", "grande",
        "El de mayor calidad. Para equipos potentes o con GPU.",
        "Recomendado: 32 GB de RAM (o GPU dedicada).",
        "bartowski/Qwen2.5-14B-Instruct-GGUF",
        "Qwen2.5-14B-Instruct-Q4_K_M.gguf", 9.0),
]


def modelo_por_id(id_modelo: str) -> Optional[InfoModelo]:
    return next((m for m in CATALOGO if m.id == id_modelo), None)


def directorio_modelos() -> Path:
    """Carpeta donde se guardan los .gguf descargados."""
    d = Path.home() / ".typoo" / "modelos_ia"
    d.mkdir(parents=True, exist_ok=True)
    return d


def ruta_modelo(info: InfoModelo) -> Path:
    return directorio_modelos() / info.archivo


def esta_descargado(info: InfoModelo) -> bool:
    ruta = ruta_modelo(info)
    return ruta.is_file() and ruta.stat().st_size > 0


def eliminar(info: InfoModelo) -> bool:
    ruta = ruta_modelo(info)
    try:
        if ruta.is_file():
            ruta.unlink()
        return True
    except OSError:
        return False


class DescargaCancelada(Exception):
    pass


def descargar(info: InfoModelo, on_progress: Progreso = None,
              cancelar: Cancelar = None) -> Path:
    """
    Descarga el modelo a un archivo temporal .part y lo renombra al terminar.
    Devuelve la ruta final. Lanza DescargaCancelada si se aborta, o una
    excepción con mensaje legible si falla.
    """
    destino = ruta_modelo(info)
    if esta_descargado(info):
        return destino
    parcial = destino.with_name(destino.name + ".part")
    req = urllib.request.Request(info.url, headers={"User-Agent": "Typoo"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            total = int(resp.headers.get("Content-Length", "0"))
            leido = 0
            with open(parcial, "wb") as f:
                while True:
                    if cancelar and cancelar():
                        raise DescargaCancelada()
                    trozo = resp.read(1 << 20)  # 1 MiB
                    if not trozo:
                        break
                    f.write(trozo)
                    leido += len(trozo)
                    if on_progress:
                        on_progress(leido, total)
    except DescargaCancelada:
        _borrar(parcial)
        raise
    except urllib.error.HTTPError as e:
        _borrar(parcial)
        raise RuntimeError(f"El servidor respondió {e.code} al descargar el modelo.") from e
    except urllib.error.URLError as e:
        _borrar(parcial)
        raise RuntimeError(f"No se pudo descargar: {e.reason}") from e
    except OSError as e:
        _borrar(parcial)
        raise RuntimeError(f"Error de disco al descargar: {e}") from e

    parcial.replace(destino)
    return destino


def _borrar(ruta: Path) -> None:
    try:
        if ruta.is_file():
            ruta.unlink()
    except OSError:
        pass


def llama_cpp_disponible() -> bool:
    """True si llama-cpp-python está instalado (necesario para ejecutar)."""
    try:
        import llama_cpp  # noqa: F401
        return True
    except Exception:
        return False
