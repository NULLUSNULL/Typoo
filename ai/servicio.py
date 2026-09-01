# ai/servicio.py
# Ejecución de las tareas de IA en segundo plano para no bloquear la interfaz.

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from ai.proveedores import ErrorIA, ProveedorIA, Mensaje


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
        acumulado: list[str] = []
        try:
            for trozo in self._proveedor.generar_stream(
                self._mensajes,
                temperatura=self._temperatura,
                max_tokens=self._max_tokens,
                cancelar=lambda: self._cancelado,
            ):
                if self._cancelado:
                    break
                acumulado.append(trozo)
                self.token.emit(trozo)
            if not self._cancelado:
                self.terminado.emit("".join(acumulado))
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
