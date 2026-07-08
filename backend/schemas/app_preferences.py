from typing import Literal

from pydantic import BaseModel

ThemePreference = Literal["auto", "light", "dark"]
LanguagePreference = Literal["system", "it", "en"]
DateFormatPreference = Literal["system", "dmY", "mdY"]


class AppPreferences(BaseModel):
    theme: ThemePreference = "auto"
    language: LanguagePreference = "system"
    date_format: DateFormatPreference = "system"


DEFAULT_APP_PREFERENCES = AppPreferences()
