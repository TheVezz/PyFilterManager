from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import ComboBox, SpinBox

from backend.schemas.frequenza import (
    FREQUENZA_ALIASES,
    FREQUENZA_ERROR_MESSAGE,
    normalize_frequenza_intervento,
)

FREQUENZA_UNITA = ["giorni", "settimane", "mesi"]

FREQUENZA_PRESET_LABELS = {
    "Personalizzato": None,
    "Bimestrale": "bimestrale",
    "Trimestrale": "trimestrale",
    "Quadrimestrale": "quadrimestrale",
    "Semestrale": "semestrale",
    "Annuale": "annuale",
}


class FrequenzaInput(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        custom_row = QHBoxLayout()
        custom_row.setContentsMargins(0, 0, 0, 0)
        custom_row.setSpacing(8)

        self.amount_input = SpinBox(self)
        self.amount_input.setRange(1, 9999)
        self.amount_input.setValue(12)
        self.amount_input.setAccelerated(True)

        self.unit_input = ComboBox(self)
        self.unit_input.addItems(FREQUENZA_UNITA)
        self.unit_input.setCurrentText("mesi")

        custom_row.addWidget(self.amount_input, 1)
        custom_row.addWidget(self.unit_input, 1)

        self.preset_input = ComboBox(self)
        for label in FREQUENZA_PRESET_LABELS:
            self.preset_input.addItem(label)

        layout.addLayout(custom_row)
        layout.addWidget(self.preset_input)

        self.amount_input.valueChanged.connect(self._on_custom_changed)
        self.unit_input.currentTextChanged.connect(self._on_custom_changed)
        self.preset_input.currentTextChanged.connect(self._on_preset_changed)

    def setFocus(
        self,
        reason: Qt.FocusReason = Qt.FocusReason.OtherFocusReason,
    ) -> None:
        self.amount_input.setFocus(reason)

    def set_value(self, value: str) -> None:
        normalized = normalize_frequenza_intervento(value)
        for label, alias in FREQUENZA_PRESET_LABELS.items():
            if alias and FREQUENZA_ALIASES.get(alias) == normalized:
                self.preset_input.setCurrentText(label)
                return

        amount, unit = normalized.split(" ", 1)
        self.preset_input.blockSignals(True)
        self.amount_input.blockSignals(True)
        self.unit_input.blockSignals(True)
        self.preset_input.setCurrentText("Personalizzato")
        self.amount_input.setValue(int(amount))
        index = self.unit_input.findText(unit)
        if index >= 0:
            self.unit_input.setCurrentIndex(index)
        self.preset_input.blockSignals(False)
        self.amount_input.blockSignals(False)
        self.unit_input.blockSignals(False)

    def value(self) -> str:
        self.amount_input.interpretText()
        preset = self.preset_input.currentText()
        alias = FREQUENZA_PRESET_LABELS.get(preset)
        if alias:
            return normalize_frequenza_intervento(alias)
        return normalize_frequenza_intervento(
            f"{self.amount_input.value()} {self.unit_input.currentText()}"
        )

    def validation_error(self) -> str | None:
        try:
            self.value()
        except ValueError:
            return FREQUENZA_ERROR_MESSAGE
        return None

    def _on_custom_changed(self) -> None:
        if self.preset_input.currentText() != "Personalizzato":
            self.preset_input.blockSignals(True)
            self.preset_input.setCurrentText("Personalizzato")
            self.preset_input.blockSignals(False)

    def _on_preset_changed(self, label: str) -> None:
        alias = FREQUENZA_PRESET_LABELS.get(label)
        if alias is None:
            return

        normalized = FREQUENZA_ALIASES[alias]
        amount, unit = normalized.split(" ", 1)
        self.amount_input.blockSignals(True)
        self.unit_input.blockSignals(True)
        self.amount_input.setValue(int(amount))
        index = self.unit_input.findText(unit)
        if index >= 0:
            self.unit_input.setCurrentIndex(index)
        self.amount_input.blockSignals(False)
        self.unit_input.blockSignals(False)
