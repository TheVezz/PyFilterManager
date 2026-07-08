from __future__ import annotations

import sys
from typing import cast

from PySide6.QtCore import QProcess, Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    InfoBar,
    InfoBarPosition,
    MessageBox,
    SettingCardGroup,
    SubtitleLabel,
)
from qfluentwidgets import (
    FluentIcon as FIF,
)

from backend.i18n import format_date, tr
from backend.schemas.app_preferences import AppPreferences, ThemePreference
from backend.services.app_preferences_service import (
    load_app_preferences,
    save_app_preferences,
)
from backend.services.app_theme_service import (
    apply_app_preferences,
    apply_theme,
)
from frontend.components.select_setting_card import SelectSettingCard


class SettingsInterface(QFrame):
    preferences_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("settings-interface")
        self._preferences = load_app_preferences()
        self._loading = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(16)

        layout.addWidget(SubtitleLabel(tr("settings.title"), self))
        intro = BodyLabel(tr("settings.intro"), self)
        intro.setWordWrap(True)
        layout.addWidget(intro)

        appearance_group = SettingCardGroup(tr("settings.appearance"), self)
        self.theme_card = SelectSettingCard(
            FIF.BRUSH,
            tr("settings.theme"),
            tr("settings.theme.help"),
            [
                ("auto", tr("settings.theme.auto")),
                ("light", tr("settings.theme.light")),
                ("dark", tr("settings.theme.dark")),
            ],
            self._preferences.theme,
            appearance_group,
        )
        appearance_group.addSettingCard(self.theme_card)
        layout.addWidget(appearance_group)

        language_group = SettingCardGroup(tr("settings.language_section"), self)
        self.language_card = SelectSettingCard(
            FIF.LANGUAGE,
            tr("settings.language"),
            tr("settings.language.help"),
            [
                ("system", tr("settings.language.system")),
                ("it", tr("settings.language.it")),
                ("en", tr("settings.language.en")),
            ],
            self._preferences.language,
            language_group,
        )
        language_group.addSettingCard(self.language_card)
        layout.addWidget(language_group)

        formats_group = SettingCardGroup(tr("settings.formats_section"), self)
        self.date_format_card = SelectSettingCard(
            FIF.CALENDAR,
            tr("settings.date_format"),
            tr("settings.date_format.help"),
            [
                ("system", tr("settings.date_format.system")),
                ("dmY", tr("settings.date_format.dmy")),
                ("mdY", tr("settings.date_format.mdy")),
            ],
            self._preferences.date_format,
            formats_group,
        )
        formats_group.addSettingCard(self.date_format_card)
        layout.addWidget(formats_group)

        self.preview_label = BodyLabel("", self)
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label)

        layout.addStretch(1)

        self.theme_card.valueChanged.connect(self._on_theme_changed)
        self.language_card.valueChanged.connect(self._on_language_changed)
        self.date_format_card.valueChanged.connect(self._on_date_format_changed)

        self._loading = False
        self._update_preview()

    def reload(self) -> None:
        self._preferences = load_app_preferences()
        self._loading = True
        self.theme_card.set_value(self._preferences.theme)
        self.language_card.set_value(self._preferences.language)
        self.date_format_card.set_value(self._preferences.date_format)
        self._loading = False
        self._update_preview()

    def _save_preferences(self) -> AppPreferences:
        save_app_preferences(self._preferences)
        return self._preferences

    def _on_theme_changed(self, value: str) -> None:
        if self._loading:
            return
        theme_value = cast(
            ThemePreference,
            value if value in {"auto", "light", "dark"} else "auto",
        )
        self._preferences = self._preferences.model_copy(update={"theme": theme_value})
        self._save_preferences()
        apply_theme(theme_value)
        self._update_preview()

    def _on_language_changed(self, value: str) -> None:
        if self._loading:
            return
        previous = load_app_preferences().language
        self._preferences = self._preferences.model_copy(update={"language": value})
        self._save_preferences()
        self._update_preview()
        if value != previous:
            self._prompt_restart()

    def _on_date_format_changed(self, value: str) -> None:
        if self._loading:
            return
        self._preferences = self._preferences.model_copy(update={"date_format": value})
        self._save_preferences()
        from PySide6.QtWidgets import QApplication

        apply_app_preferences(self._preferences, app=QApplication.instance())
        self._update_preview()
        self.preferences_changed.emit()

    def _update_preview(self) -> None:
        from datetime import date

        sample = format_date(date.today())
        self.preview_label.setText(tr("settings.date_preview", sample=sample))

    def _prompt_restart(self) -> None:
        dialog = MessageBox(
            tr("settings.restart_title"),
            tr("settings.restart_message"),
            self.window(),
        )
        dialog.yesButton.setText(tr("settings.restart_now"))
        dialog.cancelButton.setText(tr("common.cancel"))
        if dialog.exec():
            self._restart_application()

    def _restart_application(self) -> None:
        from PySide6.QtWidgets import QApplication
        restarted = QProcess.startDetached(sys.executable, sys.argv)
        if not restarted:
            self.show_restart_hint()
            return

        app = QApplication.instance()
        if app is not None:
            app.quit()

    def show_restart_hint(self) -> None:
        InfoBar.info(
            tr("settings.restart_title"),
            tr("settings.restart_message"),
            duration=5000,
            parent=self.window(),
            position=InfoBarPosition.BOTTOM,
        )
