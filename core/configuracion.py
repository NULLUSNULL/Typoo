# core/configuracion.py
# Gestión de la configuración persistente de la aplicación usando QSettings

from __future__ import annotations

from PySide6.QtCore import QSettings

from core.constantes import (
    NOMBRE_APP, AUTOR_APP, Tema,
    INTERVALO_AUTOGUARDADO_MS, MAX_RESPALDOS,
    FUENTE_EDITOR_FAMILIA, FUENTE_EDITOR_TAMANIO,
)


class Configuracion:
    """
    Singleton que centraliza el acceso y persistencia de la configuración
    de la aplicación mediante QSettings.
    """

    _instancia: "Configuracion | None" = None

    def __new__(cls) -> "Configuracion":
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._settings = QSettings(AUTOR_APP, NOMBRE_APP)
        return cls._instancia

    # ─── Tema ──────────────────────────────────────────────────────────────────

    @property
    def tema(self) -> Tema:
        valor = self._settings.value("interfaz/tema", Tema.OSCURO.value)
        return Tema(valor)

    @tema.setter
    def tema(self, valor: Tema) -> None:
        self._settings.setValue("interfaz/tema", valor.value)

    # ─── Fuente del editor ─────────────────────────────────────────────────────

    @property
    def fuente_familia(self) -> str:
        return self._settings.value("editor/fuente_familia", FUENTE_EDITOR_FAMILIA)

    @fuente_familia.setter
    def fuente_familia(self, valor: str) -> None:
        self._settings.setValue("editor/fuente_familia", valor)

    @property
    def fuente_tamanio(self) -> int:
        return int(self._settings.value("editor/fuente_tamanio", FUENTE_EDITOR_TAMANIO))

    @fuente_tamanio.setter
    def fuente_tamanio(self, valor: int) -> None:
        self._settings.setValue("editor/fuente_tamanio", valor)

    # ─── Autoguardado ─────────────────────────────────────────────────────────

    @property
    def autoguardado_activo(self) -> bool:
        return self._settings.value("editor/autoguardado_activo", True, type=bool)

    @autoguardado_activo.setter
    def autoguardado_activo(self, valor: bool) -> None:
        self._settings.setValue("editor/autoguardado_activo", valor)

    @property
    def intervalo_autoguardado(self) -> int:
        return int(self._settings.value("editor/intervalo_autoguardado", INTERVALO_AUTOGUARDADO_MS))

    @intervalo_autoguardado.setter
    def intervalo_autoguardado(self, valor: int) -> None:
        self._settings.setValue("editor/intervalo_autoguardado", valor)

    # ─── Respaldos ────────────────────────────────────────────────────────────

    @property
    def max_respaldos(self) -> int:
        return int(self._settings.value("general/max_respaldos", MAX_RESPALDOS))

    @max_respaldos.setter
    def max_respaldos(self, valor: int) -> None:
        self._settings.setValue("general/max_respaldos", valor)

    @property
    def ruta_respaldos(self) -> str:
        """Ruta personalizada para respaldos; cadena vacía = junto al proyecto."""
        return self._settings.value("general/ruta_respaldos", "")

    @ruta_respaldos.setter
    def ruta_respaldos(self, valor: str) -> None:
        self._settings.setValue("general/ruta_respaldos", valor)

    @property
    def intervalo_respaldo_ms(self) -> int:
        """Intervalo automático de respaldo en ms; 0 = desactivado."""
        return int(self._settings.value("general/intervalo_respaldo_ms", 0))

    @intervalo_respaldo_ms.setter
    def intervalo_respaldo_ms(self, valor: int) -> None:
        self._settings.setValue("general/intervalo_respaldo_ms", valor)

    # ─── Proyecto reciente ────────────────────────────────────────────────────

    @property
    def ultimo_proyecto(self) -> str:
        return self._settings.value("general/ultimo_proyecto", "")

    @ultimo_proyecto.setter
    def ultimo_proyecto(self, ruta: str) -> None:
        self._settings.setValue("general/ultimo_proyecto", ruta)

    def proyectos_recientes(self) -> list[str]:
        self._settings.beginGroup("proyectos_recientes")
        rutas = [self._settings.value(k) for k in self._settings.childKeys()]
        self._settings.endGroup()
        return [r for r in rutas if r]

    def agregar_proyecto_reciente(self, ruta: str) -> None:
        recientes = self.proyectos_recientes()
        if ruta in recientes:
            recientes.remove(ruta)
        recientes.insert(0, ruta)
        recientes = recientes[:10]  # máximo 10 recientes
        self._settings.beginGroup("proyectos_recientes")
        self._settings.remove("")
        for i, r in enumerate(recientes):
            self._settings.setValue(str(i), r)
        self._settings.endGroup()

    # ─── Geometría de la ventana ──────────────────────────────────────────────

    @property
    def geometria_ventana(self) -> bytes | None:
        return self._settings.value("interfaz/geometria")

    @geometria_ventana.setter
    def geometria_ventana(self, datos: bytes) -> None:
        self._settings.setValue("interfaz/geometria", datos)

    @property
    def estado_ventana(self) -> bytes | None:
        return self._settings.value("interfaz/estado")

    @estado_ventana.setter
    def estado_ventana(self, datos: bytes) -> None:
        self._settings.setValue("interfaz/estado", datos)

    def sincronizar(self) -> None:
        self._settings.sync()
