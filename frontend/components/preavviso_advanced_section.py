from typing import TypedDict

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from qfluentwidgets import CaptionLabel, DoubleSpinBox, PushButton, RadioButton, SpinBox
from qfluentwidgets import FluentIcon as FIF

from backend.schemas.stato_filtro import StatoFiltroConfig, get_stato_filtro_config


class PreavvisoValues(TypedDict):
    preavviso_usa_globale: bool
    preavviso_percentuale: float | None
    preavviso_massimo_giorni: int | None


class PreavvisoAdvancedSection(QWidget):
    """Sezione espandibile per configurare lo stato in scadenza del filtro."""

    expandedChanged = Signal(bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._global_config = get_stato_filtro_config()
        self._expanded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.toggle_button = PushButton("Avanzate", self)
        self.toggle_button.setIcon(FIF.CHEVRON_RIGHT_MED)
        self.toggle_button.clicked.connect(self.toggle_expanded)
        layout.addWidget(self.toggle_button)

        self.content = QWidget(self)
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)

        content_layout.addWidget(QLabel("Configurazione in scadenza", self.content))

        self.global_radio = RadioButton(self._global_label(), self.content)
        self.custom_radio = RadioButton("Personalizzato", self.content)
        self.global_radio.setChecked(True)
        content_layout.addWidget(self.global_radio)
        content_layout.addWidget(self.custom_radio)

        self.custom_fields = QWidget(self.content)
        custom_layout = QVBoxLayout(self.custom_fields)
        custom_layout.setContentsMargins(24, 0, 0, 0)
        custom_layout.setSpacing(8)

        custom_layout.addWidget(QLabel("Percentuale in scadenza", self.custom_fields))
        self.percentuale_input = DoubleSpinBox(self.custom_fields)
        self.percentuale_input.setRange(0, 100)
        self.percentuale_input.setDecimals(1)
        self.percentuale_input.setSingleStep(1)
        self.percentuale_input.setSuffix(" %")
        self.percentuale_input.setValue(self._global_config.preavviso_percentuale)
        custom_layout.addWidget(self.percentuale_input)

        custom_layout.addWidget(QLabel("Tetto massimo giorni", self.custom_fields))
        self.massimo_input = SpinBox(self.custom_fields)
        self.massimo_input.setRange(1, 9999)
        self.massimo_input.setValue(self._global_config.preavviso_massimo_giorni)
        self.massimo_input.setAccelerated(True)
        custom_layout.addWidget(self.massimo_input)

        self.custom_fields.hide()
        content_layout.addWidget(self.custom_fields)

        self.global_hint = CaptionLabel(self._global_hint(), self.content)
        content_layout.addWidget(self.global_hint)

        self.content.hide()
        layout.addWidget(self.content)

        self.global_radio.toggled.connect(self._on_mode_changed)
        self.custom_radio.toggled.connect(self._on_mode_changed)

    def _global_label(self) -> str:
        return (
            f"Valori globali ({self._global_config.preavviso_percentuale:g}%, "
            f"max {self._global_config.preavviso_massimo_giorni} giorni)"
        )

    def _global_hint(self) -> str:
        return (
            "I valori globali sono definiti in pyproject.toml "
            f"({self._global_config.preavviso_percentuale:g}%, "
            f"max {self._global_config.preavviso_massimo_giorni} giorni)."
        )

    def toggle_expanded(self) -> None:
        self.set_expanded(not self._expanded)

    def set_expanded(self, expanded: bool) -> None:
        if self._expanded == expanded:
            return

        self._expanded = expanded
        self.content.setVisible(expanded)
        icon = FIF.CHEVRON_DOWN_MED if expanded else FIF.CHEVRON_RIGHT_MED
        self.toggle_button.setIcon(icon)
        self.expandedChanged.emit(expanded)

    def set_preavviso(
        self,
        *,
        usa_globale: bool,
        percentuale: float | None = None,
        massimo_giorni: int | None = None,
        expand: bool | None = None,
    ) -> None:
        self.global_radio.setChecked(usa_globale)
        self.custom_radio.setChecked(not usa_globale)
        percentuale_value = (
            percentuale
            if percentuale is not None
            else self._global_config.preavviso_percentuale
        )
        massimo_value = (
            massimo_giorni
            if massimo_giorni is not None
            else self._global_config.preavviso_massimo_giorni
        )
        self.percentuale_input.setValue(percentuale_value)
        self.massimo_input.setValue(massimo_value)
        self._on_mode_changed()
        if expand is None:
            expand = not usa_globale
        self.set_expanded(expand)

    def preavviso_values(self) -> PreavvisoValues:
        usa_globale = self.global_radio.isChecked()
        if usa_globale:
            return {
                "preavviso_usa_globale": True,
                "preavviso_percentuale": None,
                "preavviso_massimo_giorni": None,
            }
        return {
            "preavviso_usa_globale": False,
            "preavviso_percentuale": self.percentuale_input.value(),
            "preavviso_massimo_giorni": self.massimo_input.value(),
        }

    def reload_global_config(self, config: StatoFiltroConfig | None = None) -> None:
        self._global_config = config or get_stato_filtro_config()
        self.global_radio.setText(self._global_label())
        self.global_hint.setText(self._global_hint())

    def _on_mode_changed(self) -> None:
        custom = self.custom_radio.isChecked()
        self.custom_fields.setVisible(custom)
        self.global_hint.setVisible(not custom)
