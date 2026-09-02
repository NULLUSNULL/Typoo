# widgets/iconos_formato.py
# Iconos vectoriales para la barra de formato del editor. Se dibujan con
# QPainter (monocromos, del color del tema) y con supermuestreo 4× para que se
# vean nítidos en cualquier densidad de pantalla.

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap

_S = 4            # supermuestreo
_LADO = 20        # tamaño lógico del icono


def _lienzo():
    px = _LADO * _S
    pm = QPixmap(px, px)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    return pm, painter, px


def _icono(pm: QPixmap, painter: QPainter) -> QIcon:
    painter.end()
    pm.setDevicePixelRatio(float(_S))
    return QIcon(pm)


def _pluma(color: QColor, grosor: float) -> QPen:
    pluma = QPen(color)
    pluma.setWidthF(grosor * _S)
    pluma.setCapStyle(Qt.PenCapStyle.RoundCap)
    pluma.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pluma


def _letra(texto: str, color: QColor, *, bold=False, italic=False,
           underline=False, strike=False, punto=12.5) -> QIcon:
    """Icono a partir de una letra estilizada (B, I, U, S…)."""
    pm, painter, px = _lienzo()
    fuente = QFont()
    fuente.setPointSizeF(punto * _S)
    fuente.setBold(bold)
    if not bold:
        fuente.setWeight(QFont.Weight.DemiBold)
    fuente.setItalic(italic)
    fuente.setUnderline(underline)
    fuente.setStrikeOut(strike)
    painter.setFont(fuente)
    painter.setPen(_pluma(color, 0))
    painter.drawText(QRectF(0, 0, px, px), Qt.AlignmentFlag.AlignCenter, texto)
    return _icono(pm, painter)


# ─── Listas y sangría ─────────────────────────────────────────────────────────

def _lista(color: QColor, numerada: bool) -> QIcon:
    pm, painter, px = _lienzo()
    painter.setPen(_pluma(color, 1.9))
    filas_y = [5.5, 10.0, 14.5]                # en unidades lógicas
    x_texto = 3.0
    x_linea_ini = 9.5 if numerada else 8.5
    x_linea_fin = 17.0
    for i, y in enumerate(filas_y):
        yy = y * _S
        painter.drawLine(int(x_linea_ini * _S), int(yy),
                         int(x_linea_fin * _S), int(yy))
        if numerada:
            fuente = QFont(); fuente.setPointSizeF(4.6 * _S); fuente.setBold(True)
            painter.setFont(fuente)
            painter.drawText(
                QRectF(0, (y - 2.4) * _S, 7.5 * _S, 4.8 * _S),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{i + 1}")
        else:
            r = 1.15 * _S
            painter.setBrush(color)
            painter.drawEllipse(QPointF(x_texto * _S + r, yy), r, r)
            painter.setBrush(Qt.BrushStyle.NoBrush)
    return _icono(pm, painter)


def _sangria(color: QColor, aumentar: bool) -> QIcon:
    pm, painter, px = _lienzo()
    painter.setPen(_pluma(color, 1.9))
    for y in (5.0, 15.0):                       # líneas largas arriba y abajo
        painter.drawLine(int(3 * _S), int(y * _S), int(17 * _S), int(y * _S))
    for y in (10.0,):                           # línea media (sangrada)
        x0 = 9.0 if aumentar else 3.0
        painter.drawLine(int(x0 * _S), int(y * _S), int(17 * _S), int(y * _S))
    # Flecha (triángulo) indicando la dirección de la sangría.
    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    cy = 10.0 * _S
    if aumentar:
        p = [QPointF(3 * _S, 7.4 * _S), QPointF(3 * _S, 12.6 * _S),
             QPointF(6.4 * _S, cy)]
    else:
        p = [QPointF(6.4 * _S, 7.4 * _S), QPointF(6.4 * _S, 12.6 * _S),
             QPointF(3 * _S, cy)]
    painter.drawPolygon(p)
    return _icono(pm, painter)


def _cita(color: QColor) -> QIcon:
    """Icono de cita/epígrafe: barra vertical + dos líneas de texto."""
    pm, painter, px = _lienzo()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawRoundedRect(QRectF(3 * _S, 4.5 * _S, 1.8 * _S, 11 * _S),
                            0.9 * _S, 0.9 * _S)
    painter.setPen(_pluma(color, 1.7))
    painter.drawLine(int(7 * _S), int(7.5 * _S), int(17 * _S), int(7.5 * _S))
    painter.drawLine(int(7 * _S), int(12.5 * _S), int(15 * _S), int(12.5 * _S))
    return _icono(pm, painter)


def _separador(color: QColor) -> QIcon:
    """Separador de escena: tres puntos centrados (• • •)."""
    pm, painter, px = _lienzo()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    r = 1.3 * _S
    for x in (6.0, 10.0, 14.0):
        painter.drawEllipse(QPointF(x * _S, 10 * _S), r, r)
    return _icono(pm, painter)


def _indice(color: QColor, superior: bool) -> QIcon:
    """Sub/superíndice: una «x» grande y un «2» pequeño arriba o abajo."""
    pm, painter, px = _lienzo()
    painter.setPen(_pluma(color, 0))
    f1 = QFont(); f1.setPointSizeF(9.5 * _S); painter.setFont(f1)
    painter.drawText(QRectF(1.5 * _S, 2.5 * _S, 12 * _S, 15 * _S),
                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "x")
    f2 = QFont(); f2.setPointSizeF(5.5 * _S); f2.setBold(True); painter.setFont(f2)
    y = 2.0 * _S if superior else 9.5 * _S
    painter.drawText(QRectF(10 * _S, y, 8 * _S, 8 * _S),
                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "2")
    return _icono(pm, painter)


# ─── API pública: conjunto completo de iconos para un color de tema ───────────

def iconos_barra(color_hex: str) -> dict[str, QIcon]:
    color = QColor(color_hex)
    return {
        "negrita":     _letra("B", color, bold=True),
        "cursiva":     _letra("I", color, italic=True),
        "subrayado":   _letra("U", color, underline=True),
        "tachado":     _letra("S", color, strike=True),
        "subindice":   _indice(color, superior=False),
        "superindice": _indice(color, superior=True),
        "cita":        _cita(color),
        "lista_v":     _lista(color, numerada=False),
        "lista_n":     _lista(color, numerada=True),
        "sangria_mas": _sangria(color, aumentar=True),
        "sangria_men": _sangria(color, aumentar=False),
        "separador":   _separador(color),
    }
