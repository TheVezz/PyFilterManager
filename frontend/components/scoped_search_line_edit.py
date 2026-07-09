from collections.abc import Iterable

from PySide6.QtCore import QPoint, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QLabel, QLineEdit
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import SearchLineEdit
from qfluentwidgets.components.widgets.menu import CheckableMenu, MenuAnimationType

from backend.i18n import tr
from frontend.components.theme_aware_styles import (
    apply_search_field_palette,
    badge_stylesheet,
    bind_theme_updates,
)


class ScopedSearchLineEdit(SearchLineEdit):
    scopesChanged = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scopes: list[str] = ["all"]
        self._scope_labels: list[tuple[str, str]] = [
            ("all", tr("search.scope.all")),
            ("quadro", tr("search.scope.quadro")),
            ("reparto", tr("search.scope.reparto")),
            ("impianto", tr("search.scope.impianto")),
            ("dimensione", tr("search.scope.dimensione")),
            ("frequenza", tr("search.scope.frequenza")),
            ("quantita", tr("search.scope.quantita")),
        ]
        self._available_scopes: list[str] = [key for key, _ in self._scope_labels]

        self._scope_action = QAction(self)
        self._scope_action.setIcon(FIF.CHEVRON_DOWN_MED.icon())
        self._scope_action.triggered.connect(self._show_scope_menu)
        self.addAction(self._scope_action, QLineEdit.ActionPosition.LeadingPosition)
        self._scope_button = self.leftButtons[0]
        self._scope_badge = QLabel(self)
        self._scope_badge.setObjectName("searchScopeBadge")
        self.hBoxLayout.insertWidget(1, self._scope_badge, 0)
        self._apply_theme_styles()
        bind_theme_updates(self, self._apply_theme_styles)
        self._update_tooltip()
        self._update_badge()

    def _apply_theme_styles(self) -> None:
        self._scope_badge.setStyleSheet(badge_stylesheet("searchScopeBadge"))
        apply_search_field_palette(self)

    def scopes(self) -> list[str]:
        return list(self._scopes)

    def set_scopes(self, scopes: Iterable[str]) -> None:
        valid_scopes = set(self._available_scopes)
        normalized = [
            scope.strip().lower()
            for scope in scopes
            if isinstance(scope, str) and scope.strip().lower() in valid_scopes
        ]
        if not normalized or "all" in normalized:
            normalized = ["all"]
        else:
            normalized = [scope for scope in normalized if scope != "all"]

        if normalized == self._scopes:
            return

        self._scopes = normalized
        self._update_tooltip()
        self._update_badge()
        self.scopesChanged.emit(self.scopes())

    def set_available_scopes(self, scopes: Iterable[str]) -> None:
        valid_scopes = {key for key, _ in self._scope_labels}
        normalized = [
            scope.strip().lower()
            for scope in scopes
            if isinstance(scope, str) and scope.strip().lower() in valid_scopes
        ]
        if "all" not in normalized:
            normalized.insert(0, "all")

        if normalized == self._available_scopes:
            return

        self._available_scopes = normalized
        self.set_scopes(self._scopes)

    def scope_label(self, scope: str) -> str:
        for key, label in self._scope_labels:
            if key == scope:
                return label
        return tr("search.scope.all")

    def scopes_label(self) -> str:
        if self._scopes == ["all"]:
            return tr("search.scope.all")
        return ", ".join(self.scope_label(scope) for scope in self._scopes)

    def _show_scope_menu(self) -> None:
        menu = CheckableMenu(parent=self)
        for key, label in self._scope_labels:
            if key not in self._available_scopes:
                continue
            action = QAction(label, menu)
            action.setCheckable(True)
            action.setChecked(key in self._scopes)
            action.triggered.connect(
                lambda checked=False, scope=key: self._toggle_scope(scope)
            )
            menu.addAction(action)

        x = self._scope_button.x()
        y = self.height()
        pos = self.mapToGlobal(QPoint(x, y))
        menu.exec(pos, aniType=MenuAnimationType.DROP_DOWN)

    def _toggle_scope(self, scope: str) -> None:
        if scope == "all":
            self.set_scopes(["all"])
            return

        current = [item for item in self._scopes if item != "all"]
        if scope in current:
            current.remove(scope)
        else:
            current.append(scope)
        self.set_scopes(current or ["all"])

    def _update_tooltip(self) -> None:
        self._scope_button.setToolTip(
            tr("search.scope.tooltip", fields=self.scopes_label())
        )

    def _update_badge(self) -> None:
        if self._scopes == ["all"]:
            text = tr("search.scope.all")
        elif len(self._scopes) == 1:
            text = self.scope_label(self._scopes[0])
        else:
            text = tr("search.scope.multi", count=len(self._scopes))

        self._scope_badge.setText(text)
        self._scope_badge.adjustSize()
        self.setTextMargins(66 + self._scope_badge.width(), 0, 59, 0)
