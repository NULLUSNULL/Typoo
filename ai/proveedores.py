# ai/proveedores.py
# Capa de abstracción de proveedores de IA. Cada proveedor sabe generar texto
# en streaming a partir de una lista de mensajes. Se usa solo la biblioteca
# estándar (urllib) para no añadir dependencias obligatorias.
#
# Protocolos soportados:
#   - "openai"    : /chat/completions con SSE (OpenAI, NVIDIA, Groq, Mistral, LM Studio)
#   - "anthropic" : /v1/messages con SSE
#   - "ollama"    : /api/chat con JSON por líneas

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Iterator, Optional

Mensaje = dict[str, str]                 # {"role": "system|user|assistant", "content": str}
Cancelar = Optional[Callable[[], bool]]  # devuelve True para abortar


@dataclass(frozen=True)
class InfoProveedor:
    """Metadatos de un proveedor para la interfaz y los valores por defecto."""
    id: str
    etiqueta: str
    modo: str            # "nube" | "local"
    protocolo: str       # "openai" | "anthropic" | "ollama"
    base_url: str
    requiere_clave: bool
    modelo_defecto: str
    ayuda: str = ""


# Catálogo de proveedores. Los modelos por defecto son sugerencias editables;
# el usuario puede escribir cualquier identificador de modelo.
PROVEEDORES: dict[str, InfoProveedor] = {
    "openai": InfoProveedor(
        "openai", "OpenAI", "nube", "openai",
        "https://api.openai.com/v1", True, "gpt-4o-mini",
        "Crea una API key en platform.openai.com."),
    "anthropic": InfoProveedor(
        "anthropic", "Anthropic (Claude)", "nube", "anthropic",
        "https://api.anthropic.com", True, "claude-3-5-sonnet-latest",
        "Crea una API key en console.anthropic.com."),
    "nvidia": InfoProveedor(
        "nvidia", "NVIDIA NIM", "nube", "openai",
        "https://integrate.api.nvidia.com/v1", True, "meta/llama-3.1-70b-instruct",
        "API key en build.nvidia.com (compatible con OpenAI)."),
    "groq": InfoProveedor(
        "groq", "Groq", "nube", "openai",
        "https://api.groq.com/openai/v1", True, "llama-3.3-70b-versatile",
        "API key en console.groq.com (compatible con OpenAI)."),
    "mistral": InfoProveedor(
        "mistral", "Mistral", "nube", "openai",
        "https://api.mistral.ai/v1", True, "mistral-large-latest",
        "API key en console.mistral.ai (compatible con OpenAI)."),
    "ollama": InfoProveedor(
        "ollama", "Ollama (local)", "local", "ollama",
        "http://localhost:11434", False, "llama3.1",
        "Instala Ollama y descarga un modelo con «ollama pull»."),
    "lmstudio": InfoProveedor(
        "lmstudio", "LM Studio (local)", "local", "openai",
        "http://localhost:1234/v1", False, "",
        "Inicia el servidor local de LM Studio y carga un modelo."),
    "embebido": InfoProveedor(
        "embebido", "Embebido (descargable)", "embebido", "embebido",
        "", False, "",
        "Modelos que se ejecutan en tu equipo, sin conexión. "
        "Requiere la dependencia llama-cpp-python."),
}


# Caché de modelos embebidos ya cargados (evita recargar el .gguf en cada tarea).
_LLM_CACHE: dict[str, object] = {}


def _cargar_llm(ruta: str, n_ctx: int):
    llm = _LLM_CACHE.get(ruta)
    if llm is None:
        import llama_cpp
        llm = llama_cpp.Llama(model_path=ruta, n_ctx=n_ctx, verbose=False)
        _LLM_CACHE[ruta] = llm
    return llm


def info_proveedor(id_proveedor: str) -> InfoProveedor:
    return PROVEEDORES.get(id_proveedor, PROVEEDORES["openai"])


class ErrorIA(Exception):
    """Error legible para mostrar al usuario."""


# ─── Utilidades HTTP (streaming por líneas) ──────────────────────────────────

def _lineas_stream(
    url: str,
    cuerpo: dict,
    cabeceras: dict[str, str],
    cancelar: Cancelar = None,
    timeout: int = 120,
) -> Iterator[str]:
    """POST con respuesta en streaming; produce líneas de texto ya decodificadas."""
    datos = json.dumps(cuerpo).encode("utf-8")
    cab = {"Content-Type": "application/json", **cabeceras}
    req = urllib.request.Request(url, data=datos, headers=cab, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        detalle = ""
        try:
            detalle = e.read().decode("utf-8", "replace")
        except Exception:
            pass
        raise ErrorIA(f"El servicio respondió {e.code}. {_resumen_error(detalle)}") from e
    except urllib.error.URLError as e:
        raise ErrorIA(f"No se pudo conectar: {e.reason}") from e

    with resp:
        for cruda in resp:
            if cancelar and cancelar():
                break
            yield cruda.decode("utf-8", "replace").rstrip("\n")


def _resumen_error(cuerpo: str) -> str:
    """Extrae un mensaje de error corto del cuerpo JSON si lo hay."""
    try:
        d = json.loads(cuerpo)
        if isinstance(d, dict):
            err = d.get("error")
            if isinstance(err, dict):
                return str(err.get("message", ""))[:200]
            if isinstance(err, str):
                return err[:200]
            if "message" in d:
                return str(d["message"])[:200]
    except Exception:
        pass
    return cuerpo[:200]


def _get_ok(url: str, cabeceras: dict[str, str], timeout: int = 15) -> tuple[bool, str]:
    req = urllib.request.Request(url, headers=cabeceras, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return (200 <= resp.status < 300), f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {_resumen_error(_leer(e))}"
    except urllib.error.URLError as e:
        return False, f"No se pudo conectar: {e.reason}"


def _leer(e: urllib.error.HTTPError) -> str:
    try:
        return e.read().decode("utf-8", "replace")
    except Exception:
        return ""


# ─── Proveedor ───────────────────────────────────────────────────────────────

class ProveedorIA:
    """Cliente de un proveedor de IA según su protocolo."""

    def __init__(self, info: InfoProveedor, *, modelo: str = "",
                 api_key: str = "", base_url: str = "") -> None:
        self.info = info
        self.protocolo = info.protocolo
        self.modelo = modelo or info.modelo_defecto
        self.api_key = api_key
        self.base_url = (base_url or info.base_url).rstrip("/")

    # -- Generación en streaming --------------------------------------------
    def generar_stream(
        self,
        mensajes: list[Mensaje],
        *,
        temperatura: float = 0.7,
        max_tokens: int = 1024,
        cancelar: Cancelar = None,
    ) -> Iterator[str]:
        if self.protocolo == "openai":
            yield from self._stream_openai(mensajes, temperatura, max_tokens, cancelar)
        elif self.protocolo == "anthropic":
            yield from self._stream_anthropic(mensajes, temperatura, max_tokens, cancelar)
        elif self.protocolo == "ollama":
            yield from self._stream_ollama(mensajes, temperatura, cancelar)
        elif self.protocolo == "embebido":
            yield from self._stream_embebido(mensajes, temperatura, max_tokens, cancelar)
        else:
            raise ErrorIA(f"Protocolo no soportado: {self.protocolo}")

    def _stream_embebido(self, mensajes, temperatura, max_tokens, cancelar):
        from ai import modelos
        info = modelos.modelo_por_id(self.modelo)
        if info is None:
            raise ErrorIA("No hay ningún modelo embebido seleccionado.")
        if not modelos.llama_cpp_disponible():
            raise ErrorIA(
                "Falta la dependencia «llama-cpp-python». Instálala para usar "
                "modelos embebidos (pip install llama-cpp-python).")
        if not modelos.esta_descargado(info):
            raise ErrorIA(f"El modelo «{info.etiqueta}» aún no está descargado.")
        try:
            llm = _cargar_llm(str(modelos.ruta_modelo(info)), info.n_ctx)
            stream = llm.create_chat_completion(
                messages=mensajes,
                temperature=temperatura,
                max_tokens=max_tokens,
                stream=True,
            )
        except ErrorIA:
            raise
        except Exception as e:
            raise ErrorIA(f"No se pudo cargar el modelo embebido: {e}") from e
        for chunk in stream:
            if cancelar and cancelar():
                break
            try:
                trozo = chunk["choices"][0].get("delta", {}).get("content")
                if trozo:
                    yield trozo
            except (KeyError, IndexError):
                continue

    def _stream_openai(self, mensajes, temperatura, max_tokens, cancelar):
        cab = {}
        if self.api_key:
            cab["Authorization"] = f"Bearer {self.api_key}"
        cuerpo = {
            "model": self.modelo,
            "messages": mensajes,
            "stream": True,
            "temperature": temperatura,
            "max_tokens": max_tokens,
        }
        for linea in _lineas_stream(f"{self.base_url}/chat/completions", cuerpo, cab, cancelar):
            if not linea.startswith("data:"):
                continue
            payload = linea[5:].strip()
            if payload == "[DONE]":
                break
            try:
                obj = json.loads(payload)
                delta = obj["choices"][0].get("delta", {})
                trozo = delta.get("content")
                if trozo:
                    yield trozo
            except (KeyError, IndexError, json.JSONDecodeError):
                continue

    def _stream_anthropic(self, mensajes, temperatura, max_tokens, cancelar):
        # Anthropic recibe el system aparte y solo user/assistant en messages.
        sistema = " ".join(m["content"] for m in mensajes if m["role"] == "system")
        conv = [m for m in mensajes if m["role"] in ("user", "assistant")]
        cab = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        cuerpo = {
            "model": self.modelo,
            "system": sistema,
            "messages": conv,
            "stream": True,
            "temperature": temperatura,
            "max_tokens": max_tokens,
        }
        for linea in _lineas_stream(f"{self.base_url}/v1/messages", cuerpo, cab, cancelar):
            if not linea.startswith("data:"):
                continue
            payload = linea[5:].strip()
            try:
                obj = json.loads(payload)
                if obj.get("type") == "content_block_delta":
                    trozo = obj.get("delta", {}).get("text")
                    if trozo:
                        yield trozo
                elif obj.get("type") == "message_stop":
                    break
            except json.JSONDecodeError:
                continue

    def _stream_ollama(self, mensajes, temperatura, cancelar):
        cuerpo = {
            "model": self.modelo,
            "messages": mensajes,
            "stream": True,
            "options": {"temperature": temperatura},
        }
        for linea in _lineas_stream(f"{self.base_url}/api/chat", cuerpo, {}, cancelar):
            if not linea.strip():
                continue
            try:
                obj = json.loads(linea)
                trozo = obj.get("message", {}).get("content")
                if trozo:
                    yield trozo
                if obj.get("done"):
                    break
            except json.JSONDecodeError:
                continue

    # -- Prueba de conexión --------------------------------------------------
    def probar(self) -> tuple[bool, str]:
        """Comprueba conectividad y credenciales. Devuelve (ok, mensaje)."""
        try:
            if self.protocolo == "openai":
                cab = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
                ok, msg = _get_ok(f"{self.base_url}/models", cab)
                return ok, ("Conexión correcta." if ok else msg)
            if self.protocolo == "ollama":
                ok, msg = _get_ok(f"{self.base_url}/api/tags", {})
                return ok, ("Conexión con Ollama correcta." if ok else msg)
            if self.protocolo == "anthropic":
                # Petición mínima para validar clave y modelo.
                list(self.generar_stream(
                    [{"role": "user", "content": "ping"}], max_tokens=1))
                return True, "Conexión correcta."
            if self.protocolo == "embebido":
                from ai import modelos
                info = modelos.modelo_por_id(self.modelo)
                if info is None:
                    return False, "Selecciona un modelo embebido."
                if not modelos.llama_cpp_disponible():
                    return False, ("Falta «llama-cpp-python» (necesaria para "
                                   "ejecutar modelos embebidos).")
                if not modelos.esta_descargado(info):
                    return False, f"El modelo «{info.etiqueta}» no está descargado."
                return True, "Modelo embebido listo (se cargará al primer uso)."
        except ErrorIA as e:
            return False, str(e)
        except Exception as e:  # pragma: no cover - salvaguarda
            return False, f"Error inesperado: {e}"
        return False, "Protocolo no soportado."


def crear_proveedor_desde_config(config) -> ProveedorIA:
    """Construye el ProveedorIA a partir de la Configuracion de la app."""
    info = info_proveedor(config.ia_proveedor)
    return ProveedorIA(
        info,
        modelo=config.ia_modelo,
        api_key=config.ia_api_key(info.id) if info.requiere_clave else "",
        base_url=config.ia_base_url,
    )
