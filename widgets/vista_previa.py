# widgets/vista_previa.py
# Panel de vista previa HTML renderizada desde Markdown

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


class VistaPrevia(QWidget):
    """
    Panel derecho que muestra la vista previa HTML del documento Markdown activo.
    Se actualiza en tiempo real mientras el usuario escribe.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._markdown_disponible = self._verificar_markdown()
        self._construir_ui()

    def _verificar_markdown(self) -> bool:
        """Comprueba si la librería 'markdown' está instalada."""
        try:
            import markdown  # noqa: F401
            return True
        except ImportError:
            return False

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Cabecera del panel
        cabecera = QLabel("  Vista previa")
        cabecera.setFixedHeight(28)
        cabecera.setObjectName("CabeceraPanel")
        layout.addWidget(cabecera)

        # Navegador HTML
        self._navegador = QTextBrowser()
        self._navegador.setOpenExternalLinks(True)
        self._navegador.setReadOnly(True)
        layout.addWidget(self._navegador)

    # ─── Actualización de contenido ───────────────────────────────────────────

    def actualizar(self, texto_markdown: str) -> None:
        """Convierte el texto Markdown a HTML y lo muestra."""
        if not texto_markdown.strip():
            self._navegador.setHtml("<p style='color:gray;'>Sin contenido.</p>")
            return

        html = self._convertir(texto_markdown)
        self._navegador.setHtml(html)

    def limpiar(self) -> None:
        self._navegador.setHtml("")

    def _convertir(self, texto: str) -> str:
        """Convierte Markdown a HTML con estilos adaptados al tema activo."""
        if self._markdown_disponible:
            import markdown
            cuerpo = markdown.markdown(
                texto,
                extensions=["fenced_code", "tables", "nl2br", "sane_lists"],
            )
        else:
            cuerpo = texto

        from core.configuracion import Configuracion
        from core.constantes import Tema
        oscuro = Configuracion().tema == Tema.OSCURO

        if oscuro:
            bg       = "#1E2227"
            color    = "#DCDFE4"
            h_color  = "#61AFEF"
            code_bg  = "#2C313A"
            code_fg  = "#98C379"
            bq_border= "#4B5263"
            bq_color = "#7F848E"
            link     = "#56B6C2"
            hr       = "#4B5263"
            th_bg    = "#2C313A"
            td_border= "#4B5263"
        else:
            bg       = "#FFFFFF"
            color    = "#1D1D1F"
            h_color  = "#007AFF"
            code_bg  = "#F0F0F5"
            code_fg  = "#3A3A3C"
            bq_border= "#D1D1D6"
            bq_color = "#6E6E73"
            link     = "#007AFF"
            hr       = "#D1D1D6"
            th_bg    = "#E8E8ED"
            td_border= "#D1D1D6"

        return f"""<html><head><style>
            body {{
                font-family: Georgia, 'Times New Roman', serif;
                font-size: 15px;
                line-height: 1.7;
                padding: 20px 30px;
                max-width: 700px;
                margin: 0 auto;
                color: {color};
                background: {bg};
            }}
            h1, h2, h3, h4, h5, h6 {{ color: {h_color}; margin-top: 1.2em; }}
            code {{
                background: {code_bg};
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                color: {code_fg};
            }}
            pre {{
                background: {code_bg};
                padding: 12px;
                border-radius: 5px;
                overflow-x: auto;
            }}
            pre code {{ background: none; padding: 0; }}
            blockquote {{
                border-left: 4px solid {bq_border};
                margin: 0;
                padding-left: 16px;
                color: {bq_color};
                font-style: italic;
            }}
            a {{ color: {link}; }}
            hr {{ border-color: {hr}; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid {td_border}; padding: 8px 12px; }}
            th {{ background: {th_bg}; }}
        </style></head>
        <body>{cuerpo}</body></html>"""
