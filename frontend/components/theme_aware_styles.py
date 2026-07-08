from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QWidget
from qfluentwidgets import isDarkTheme
from qfluentwidgets.common.config import qconfig


def primary_text_color() -> str:
    return "rgba(255, 255, 255, 0.92)" if isDarkTheme() else "rgba(0, 0, 0, 0.88)"


def badge_stylesheet(object_name: str) -> str:
    text = primary_text_color()
    if isDarkTheme():
        background = "rgba(255, 255, 255, 0.14)"
    else:
        background = "rgba(0, 0, 0, 0.08)"
    return (
        f"QLabel#{object_name} {{"
        f"border-radius: 10px;"
        f"padding: 1px 8px;"
        f"background: {background};"
        f"color: {text};"
        f"}}"
    )


def transparent_label_stylesheet() -> str:
    return f"color: {primary_text_color()}; background: transparent;"


def apply_search_field_palette(widget: QWidget) -> None:
    palette = widget.palette()
    text = QColor(255, 255, 255, 235) if isDarkTheme() else QColor(0, 0, 0, 225)
    placeholder = QColor(255, 255, 255, 140) if isDarkTheme() else QColor(0, 0, 0, 120)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.PlaceholderText, placeholder)
    widget.setPalette(palette)


def bind_theme_updates(widget: QWidget, callback) -> None:
    qconfig.themeChanged.connect(lambda _theme: callback())
