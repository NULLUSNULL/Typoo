# widgets/barra_titulo.py
# Barra de título propia de la aplicación. En Linux la ventana se muestra sin la
# barra de título del sistema (frameless) y esta barra la sustituye: contiene el
# icono y el nombre de la app y los botones de minimizar, maximizar y cerrar,
# permite arrastrar la ventana y maximizar con doble clic. En el resto de
# sistemas se usa la barra de título nativa y aquí solo se muestra el rótulo.

from __future__ import annotations

import sys

from PySide6.QtCore import QEvent, QObject, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget

ES_LINUX = sys.platform.startswith("linux")

_S = 4  # supermuestreo para iconos nítidos


def _icono_ventana(tipo: str, color_hex: str) -> QIcon:
    """Dibuja el glifo de un botón de ventana (min/max/restore/close)."""
    lado = 12
    px = lado * _S
    pm = QPixmap(px, px)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pluma = QPen(QColor(color_hex))
    pluma.setWidthF(1.4 * _S)
    pluma.setCapStyle(Qt.PenCapStyle.RoundCap)
    pluma.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pluma)
    m = 2.0 * _S
    if tipo == "min":
        y = px / 2
        p.drawLine(int(m), int(y), int(px - m), int(y))
    elif tipo == "max":
        p.drawRect(QRectF(m, m, px - 2 * m, px - 2 * m))
    elif tipo == "restore":
        d = 2.0 * _S
        p.drawRect(QRectF(m, m + d, px - 2 * m - d, px - 2 * m - d))
        p.drawLine(int(m + d), int(m + d), int(m + d), int(m))
        p.drawLine(int(m + d), int(m), int(px - m), int(m))
        p.drawLine(int(px - m), int(m), int(px - m), int(px - m - d))
        p.drawLine(int(px - m), int(px - m - d), int(px - m - d), int(px - m - d))
    elif tipo == "close":
        p.drawLine(int(m), int(m), int(px - m), int(px - m))
        p.drawLine(int(px - m), int(m), int(m), int(px - m))
    p.end()
    pm.setDevicePixelRatio(float(_S))
    return QIcon(pm)


class BarraTitulo(QWidget):
    """Barra de título propia (rótulo + botones de ventana en Linux)."""

    def __init__(self, ventana: QWidget, titulo: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._ventana = ventana
        self.setObjectName("BarraTitulo")
        self._frameless = ES_LINUX

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 4, 8, 4)
        lay.setSpacing(8)

        # Icono de la app (izquierda).
        self._icono_app = QLabel()
        self._icono_app.setFixedSize(18, 18)
        self._icono_app.setScaledContents(True)
        lay.addWidget(self._icono_app)

        lay.addStretch(1)

        self._lbl_titulo = QLabel(titulo)
        self._lbl_titulo.setObjectName("BannerTitulo")
        f = self._lbl_titulo.font()
        f.setBold(True)
        f.setPointSize(f.pointSize() + 1)
        self._lbl_titulo.setFont(f)
        lay.addWidget(self._lbl_titulo)

        # Indicador de IA (lo gestiona la ventana principal).
        self.icono_ia = QLabel()
        self.icono_ia.setFixedSize(18, 18)
        self.icono_ia.setScaledContents(True)
        self.icono_ia.hide()
        lay.addWidget(self.icono_ia)

        lay.addStretch(1)

        # Botones de ventana (solo cuando sustituimos la barra nativa).
        self._botones: list[QToolButton] = []
        if self._frameless:
            self._btn_min = self._crear_boton("min", "Minimizar", self._minimizar)
            self._btn_max = self._crear_boton("max", "Maximizar", self._alternar_maximizar)
            self._btn_cerrar = self._crear_boton("close", "Cerrar", self._ventana.close,
                                                 cerrar=True)
            for b in (self._btn_min, self._btn_max, self._btn_cerrar):
                lay.addWidget(b)
        else:
            # Sin botones: iguala el ancho de la zona derecha para centrar el
            # rótulo respecto del icono de la izquierda.
            self._icono_app.hide()

        self.aplicar_tema("#E7E7EA")

    def _crear_boton(self, tipo, tooltip, slot, cerrar=False) -> QToolButton:
        b = QToolButton()
        b.setObjectName("BotonCerrarVentana" if cerrar else "BotonVentana")
        b.setFixedSize(30, 24)
        b.setIconSize(QSize(12, 12))
        b.setToolTip(tooltip)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        b.clicked.connect(slot)
        b.setProperty("_tipo", tipo)
        self._botones.append(b)
        return b

    # ─── Icono de la app ──────────────────────────────────────────────────────
    def establecer_icono(self, icono: QIcon) -> None:
        if not icono.isNull():
            self._icono_app.setPixmap(icono.pixmap(18, 18))
            self._icono_app.show()

    # ─── Tema ───────────────────────────────────────────────────────────────
    def aplicar_tema(self, color_hex: str) -> None:
        self._color_actual = color_hex
        if not self._frameless:
            return
        for b in self._botones:
            tipo = b.property("_tipo")
            if tipo == "max" and self._ventana.isMaximized():
                tipo = "restore"
            b.setIcon(_icono_ventana(tipo, color_hex))

    # ─── Acciones de ventana ──────────────────────────────────────────────────
    def _minimizar(self) -> None:
        self._ventana.showMinimized()

    def _alternar_maximizar(self) -> None:
        if self._ventana.isMaximized():
            self._ventana.showNormal()
        else:
            self._ventana.showMaximized()
        self.actualizar_boton_maximizar()

    def actualizar_boton_maximizar(self) -> None:
        if not self._frameless:
            return
        tipo = "restore" if self._ventana.isMaximized() else "max"
        # Recolorear con el color actual manteniendo el glifo correcto.
        color = self._color_actual or "#E7E7EA"
        self._btn_max.setIcon(_icono_ventana(tipo, color))

    _color_actual: str | None = None

    # ─── Arrastre y doble clic para mover/maximizar ────────────────────────────
    def mousePressEvent(self, ev) -> None:  # type: ignore[override]
        if self._frameless and ev.button() == Qt.MouseButton.LeftButton:
            wh = self._ventana.windowHandle()
            if wh is not None:
                wh.startSystemMove()
                ev.accept()
                return
        super().mousePressEvent(ev)

    def mouseDoubleClickEvent(self, ev) -> None:  # type: ignore[override]
        if self._frameless and ev.button() == Qt.MouseButton.LeftButton:
            self._alternar_maximizar()
            ev.accept()
            return
        super().mouseDoubleClickEvent(ev)


class RedimensionadorSinBorde(QObject):
    """Filtro que permite redimensionar una ventana sin borde arrastrando cerca
    de sus bordes (usa startSystemResize, compatible con X11 y Wayland)."""

    def __init__(self, ventana: QWidget, margen: int = 6) -> None:
        super().__init__(ventana)
        self._v = ventana
        self._m = margen

    def eventFilter(self, obj, ev) -> bool:  # noqa: D401
        v = self._v
        if not v.isVisible() or v.isMaximized() or v.isFullScreen():
            return False
        if ev.type() == QEvent.Type.MouseButtonPress and \
                ev.button() == Qt.MouseButton.LeftButton:
            try:
                gp = ev.globalPosition().toPoint()
            except AttributeError:
                return False
            bordes = self._bordes(gp)
            if bordes:
                wh = v.windowHandle()
                if wh is not None:
                    wh.startSystemResize(bordes)
                    return True
        return False

    def _bordes(self, gp):
        r = self._v.frameGeometry()
        m = self._m
        bordes = Qt.Edge(0)
        cerca_izq = abs(gp.x() - r.left()) <= m
        cerca_der = abs(gp.x() - r.right()) <= m
        cerca_arr = abs(gp.y() - r.top()) <= m
        cerca_aba = abs(gp.y() - r.bottom()) <= m
        if cerca_izq:
            bordes |= Qt.Edge.LeftEdge
        if cerca_der:
            bordes |= Qt.Edge.RightEdge
        # El borde superior solo redimensiona en las esquinas: así la franja
        # central de arriba (donde está la barra de menú) no roba sus clics.
        if cerca_arr and (cerca_izq or cerca_der):
            bordes |= Qt.Edge.TopEdge
        if cerca_aba:
            bordes |= Qt.Edge.BottomEdge
        return bordes
