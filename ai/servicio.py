# ai/servicio.py
# Ejecución de las tareas de IA en segundo plano para no bloquear la interfaz.

from __future__ import annotations

import re

from PySide6.QtCore import QThread, Signal

from ai.proveedores import ErrorIA, ProveedorIA, Mensaje

# Bloques de "razonamiento" que algunos modelos (Qwen3, DeepSeek-R1…) emiten y
# que no queremos mostrar: solo interesa la respuesta final.
_RE_PENSAMIENTO_CERRADO = re.compile(r"<think(?:ing)?>.*?</think(?:ing)?>",
                                     re.DOTALL | re.IGNORECASE)
_RE_PENSAMIENTO_ABIERTO = re.compile(r"<think(?:ing)?>.*$",
                                     re.DOTALL | re.IGNORECASE)


def limpiar_pensamiento(texto: str) -> str:
    """Elimina los bloques <think>…</think> (cerrados o aún abiertos)."""
    texto = _RE_PENSAMIENTO_CERRADO.sub("", texto)
    texto = _RE_PENSAMIENTO_ABIERTO.sub("", texto)
    return texto


class TrabajadorIA(QThread):
    """Ejecuta una generación en streaming y emite los fragmentos."""

    token = Signal(str)       # cada fragmento de texto recibido
    terminado = Signal(str)   # texto completo al finalizar
    error = Signal(str)       # mensaje de error legible

    def __init__(
        self,
        proveedor: ProveedorIA,
        mensajes: list[Mensaje],
        *,
        temperatura: float = 0.7,
        max_tokens: int = 1024,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._proveedor = proveedor
        self._mensajes = mensajes
        self._temperatura = temperatura
        self._max_tokens = max_tokens
        self._cancelado = False

    def cancelar(self) -> None:
        self._cancelado = True

    def run(self) -> None:  # noqa: D401 - ejecutado en el hilo
        crudo: list[str] = []
        limpio_emitido = ""
        try:
            for trozo in self._proveedor.generar_stream(
                self._mensajes,
                temperatura=self._temperatura,
                max_tokens=self._max_tokens,
                cancelar=lambda: self._cancelado,
            ):
                if self._cancelado:
                    break
                crudo.append(trozo)
                # Recalcular el texto sin razonamiento y emitir solo lo nuevo.
                limpio = limpiar_pensamiento("".join(crudo))
                if len(limpio) > len(limpio_emitido) and limpio.startswith(limpio_emitido):
                    self.token.emit(limpio[len(limpio_emitido):])
                    limpio_emitido = limpio
            if not self._cancelado:
                self.terminado.emit(limpiar_pensamiento("".join(crudo)).strip())
        except ErrorIA as e:
            self.error.emit(str(e))
        except Exception as e:  # pragma: no cover - salvaguarda
            self.error.emit(f"Error inesperado: {e}")


class TrabajadorPrueba(QThread):
    """Prueba de conexión con el proveedor (no bloquea el diálogo)."""

    resultado = Signal(bool, str)

    def __init__(self, proveedor: ProveedorIA, parent=None) -> None:
        super().__init__(parent)
        self._proveedor = proveedor

    def run(self) -> None:
        try:
            ok, msg = self._proveedor.probar()
        except Exception as e:  # pragma: no cover
            ok, msg = False, f"Error inesperado: {e}"
        self.resultado.emit(ok, msg)


class TrabajadorDescarga(QThread):
    """Descarga un modelo embebido en segundo plano, informando del progreso."""

    progreso = Signal(int, int)   # (bytes_leidos, bytes_totales)
    terminado = Signal()
    cancelado = Signal()
    error = Signal(str)

    def __init__(self, info, parent=None) -> None:
        super().__init__(parent)
        self._info = info
        self._cancelar = False

    def cancelar(self) -> None:
        self._cancelar = True

    def run(self) -> None:
        from ai import modelos
        try:
            modelos.descargar(
                self._info,
                on_progress=lambda leido, total: self.progreso.emit(leido, total),
                cancelar=lambda: self._cancelar,
            )
            self.terminado.emit()
        except modelos.DescargaCancelada:
            self.cancelado.emit()
        except Exception as e:  # noqa: BLE001 - mensaje legible para el usuario
            self.error.emit(str(e))
