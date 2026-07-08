from collections.abc import Iterable

from PySide6.QtCore import QPoint, Signal
from PySide6.QtGui import QAction, QFontMetrics
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy
from qfluentwidgets import PushButton
from qfluentwidgets.components.widgets.menu import CheckableMenu, MenuAnimationType

from frontend.components.theme_aware_styles import (
    badge_stylesheet,
    bind_theme_updates,
    transparent_label_stylesheet,
)


class MultiSelectFilterButton(PushButton):
    valuesChanged = Signal(list)

    def __init__(
        self,
        title: str,
        options: list[tuple[str, str]],
        *,
        all_key: str = "all",
        parent=None,
    ) -> None:
        super().__init__(parent=parent)
        self._title = title
        self._options = options
        self._all_key = all_key
        self._values: list[str] = [all_key]

        self.setText("")
        self.clicked.connect(self._show_menu)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(33)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(6)

        self._title_label = QLabel(self._title, self)
        self._title_label.setFont(self.font())
        layout.addWidget(self._title_label, 0)

        self._badge = QLabel(self)
        self._badge.setObjectName("filterBadge")
        self._badge.setFont(self.font())
        layout.addWidget(self._badge, 0)

        self._arrow_label = QLabel("▾", self)
        self._arrow_label.setFont(self.font())
        layout.addWidget(self._arrow_label, 0)
        layout.addStretch(1)

        self._apply_theme_styles()
        bind_theme_updates(self, self._apply_theme_styles)

        self._update_badge()
        self._update_tooltip()

    def _apply_theme_styles(self) -> None:
        self._title_label.setStyleSheet(transparent_label_stylesheet())
        self._arrow_label.setStyleSheet(transparent_label_stylesheet())
        self._badge.setStyleSheet(badge_stylesheet("filterBadge"))

    def values(self) -> list[str]:
        return list(self._values)

    def set_title(self, title: str) -> None:
        self._title = title
        self._title_label.setText(title)
        self._update_tooltip()
        self._update_button_width()

    def set_options(self, options: list[tuple[str, str]]) -> None:
        self._options = options
        self.set_values(self._values)

    def set_values(self, values: Iterable[str]) -> None:
        valid = {key for key, _ in self._options}
        normalized = [
            value.strip().lower()
            for value in values
            if isinstance(value, str) and value.strip().lower() in valid
        ]
        if not normalized or self._all_key in normalized:
            normalized = [self._all_key]
        else:
            normalized = [value for value in normalized if value != self._all_key]
            specific_values = [key for key, _ in self._options if key != self._all_key]
            if set(normalized) == set(specific_values):
                normalized = [self._all_key]

        if normalized == self._values:
            return

        self._values = normalized
        self._update_badge()
        self._update_tooltip()
        self.valuesChanged.emit(self.values())

    def label_for(self, value: str) -> str:
        for key, label in self._options:
            if key == value:
                return label
        return self._title

    def values_label(self) -> str:
        if self._values == [self._all_key]:
            return self.label_for(self._all_key)
        return ", ".join(self.label_for(value) for value in self._values)

    def _show_menu(self) -> None:
        menu = CheckableMenu(parent=self)
        for key, label in self._options:
            action = QAction(label, menu)
            action.setCheckable(True)
            action.setChecked(key in self._values)
            action.triggered.connect(
                lambda checked=False, value=key: self._toggle_value(value)
            )
            menu.addAction(action)

        pos = self.mapToGlobal(QPoint(0, self.height()))
        menu.exec(pos, aniType=MenuAnimationType.DROP_DOWN)

    def _toggle_value(self, value: str) -> None:
        if value == self._all_key:
            self.set_values([self._all_key])
            return

        current = [item for item in self._values if item != self._all_key]
        if value in current:
            current.remove(value)
        else:
            current.append(value)
        self.set_values(current or [self._all_key])

    def _update_badge(self) -> None:
        if self._values == [self._all_key]:
            text = self.label_for(self._all_key)
        elif len(self._values) == 1:
            text = self.label_for(self._values[0])
        else:
            text = f"{len(self._values)} stati"

        self._badge.setText(text)
        self._badge.adjustSize()
        self._update_button_width()

    def _update_tooltip(self) -> None:
        self.setToolTip(f"{self._title}: {self.values_label()}")

    def _update_button_width(self) -> None:
        metrics = QFontMetrics(self.font())
        title_width = metrics.horizontalAdvance(self._title)
        width = 10 + title_width + 6 + self._badge.width() + 6 + 10 + 10
        self.setMinimumWidth(max(118, width))
