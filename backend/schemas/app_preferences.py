from typing import Literal

from pydantic import BaseModel

ThemePreference = Literal["auto", "light", "dark"]
LanguagePreference = Literal["system", "it", "en"]
DateFormatPreference = Literal["system", "dmY", "mdY"]
LiveRefreshPreference = Literal["15", "30", "60", "300"]


class AppPreferences(BaseModel):
    theme: ThemePreference = "auto"
    language: LanguagePreference = "system"
    date_format: DateFormatPreference = "system"
    live_refresh_seconds: LiveRefreshPreference = "60"


DEFAULT_APP_PREFERENCES = AppPreferences()
