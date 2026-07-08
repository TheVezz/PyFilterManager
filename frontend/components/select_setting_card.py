from PySide6.QtCore import Qt, Signal
from qfluentwidgets import ComboBox, SettingCard


class SelectSettingCard(SettingCard):
    """Card impostazioni con elenco a discesa."""

    valueChanged = Signal(str)

    def __init__(
        self,
        icon,
        title: str,
        content: str | None,
        options: list[tuple[str, str]],
        current_value: str,
        parent=None,
    ) -> None:
        super().__init__(icon, title, content, parent)
        self._value_to_index: dict[str, int] = {}

        self.combo_box = ComboBox(self)
        self.hBoxLayout.addWidget(self.combo_box, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        for index, (value, label) in enumerate(options):
            self.combo_box.addItem(label, userData=value)
            self._value_to_index[value] = index

        self.set_value(current_value)
        self.combo_box.currentIndexChanged.connect(self._on_index_changed)

    def set_value(self, value: str) -> None:
        index = self._value_to_index.get(value)
        if index is None:
            return
        blocked = self.combo_box.blockSignals(True)
        self.combo_box.setCurrentIndex(index)
        self.combo_box.blockSignals(blocked)

    def current_value(self) -> str:
        return str(self.combo_box.currentData())

    def _on_index_changed(self, index: int) -> None:
        value = self.combo_box.itemData(index)
        if value is not None:
            self.valueChanged.emit(str(value))
