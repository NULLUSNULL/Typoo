"""
Widgets package initialization.
"""

from typoo.widgets.project_explorer import ProjectExplorer
from typoo.widgets.editor_widget import EditorWidget
from typoo.widgets.tab_widget import TabWidget
from typoo.widgets.status_bar import StatusBar
from typoo.widgets.format_toolbar import FormatToolbar

__all__ = [
    "ProjectExplorer",
    "EditorWidget",
    "TabWidget",
    "StatusBar",
    "FormatToolbar",
]
