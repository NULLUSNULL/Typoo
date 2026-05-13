# services/autoguardado.py
# Servicio de autoguardado periódico basado en QTimer

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QTimer

from core.configuracion import Configuracion
from core.logger import logger


class ServicioAutoguardado:
    """
    Administra el guardado automático periódico de documentos abiertos.
    Se conecta a una función de guardado proporcionada por la ventana principal.
    """

    def __init__(self, funcion_guardar: Callable[[], None]) -> None:
        self._funcion_guardar = funcion_guardar
        self._config = Configuracion()
        self._timer = QTimer()
        self._timer.timeout.connect(self._ejecutar_guardado)

    def iniciar(self) -> None:
        """Activa el autoguardado según la configuración actual."""
        if self._config.autoguardado_activo:
            intervalo = self._config.intervalo_autoguardado
            self._timer.start(intervalo)
            logger.debug("Autoguardado iniciado (intervalo: %d ms)", intervalo)

    def detener(self) -> None:
        """Detiene el timer de autoguardado."""
        self._timer.stop()
        logger.debug("Autoguardado detenido")

    def actualizar_intervalo(self, intervalo_ms: int) -> None:
        """Actualiza el intervalo sin detener el servicio si está activo."""
        self._config.intervalo_autoguardado = intervalo_ms
        if self._timer.isActive():
            self._timer.setInterval(intervalo_ms)

    def _ejecutar_guardado(self) -> None:
        """Callback del timer: invoca la función de guardado."""
        try:
            logger.debug("Autoguardado ejecutándose...")
            self._funcion_guardar()
        except Exception as e:
            logger.error("Error en autoguardado: %s", e)
