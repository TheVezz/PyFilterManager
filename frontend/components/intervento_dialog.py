from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout
from qfluentwidgets import (
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PrimaryPushButton,
    PushButton,
)

from backend.i18n import invalid_date_message, tr
from backend.schemas.filtri import InterventoCreate, InterventoUpdate, InterventoVoce
from backend.services.intervento_crud_service import (
    InterventoCrudError,
    create_intervento,
    update_intervento,
)
from frontend.components.date_input import DateInput


def _show_dialog_error(dialog: QDialog, message: str) -> None:
    InfoBar.error(
        tr("common.error"),
        message,
        duration=5000,
        parent=dialog,
        position=InfoBarPosition.BOTTOM,
    )


class InterventoDialog(QDialog):
    def __init__(
        self,
        filtro_id: int,
        parent=None,
        intervento: InterventoVoce | None = None,
    ) -> None:
        super().__init__(parent)
        self._filtro_id = filtro_id
        self._intervento = intervento

        self.setWindowTitle(
            tr("intervento.edit") if intervento else tr("intervento.new")
        )
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setModal(True)
        self.resize(420, 220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        layout.addWidget(QLabel(tr("intervento.date"), self))
        self.data_input = DateInput(self)
        layout.addWidget(self.data_input)

        layout.addWidget(QLabel(tr("intervento.notes"), self))
        self.note_input = LineEdit(self)
        self.note_input.setPlaceholderText(tr("intervento.notes_placeholder"))
        self.note_input.setClearButtonEnabled(True)
        layout.addWidget(self.note_input)

        buttons = QHBoxLayout()
        self.cancel_button = PushButton(tr("common.cancel"), self)
        self.ok_button = PrimaryPushButton(
            tr("intervento.save_changes") if intervento else tr("intervento.add"),
            self,
        )
        buttons.addStretch(1)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.ok_button)
        layout.addLayout(buttons)

        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.clicked.connect(self._on_accept)
        self.note_input.returnPressed.connect(self._on_accept)

        if intervento is not None:
            self.data_input.setDate(
                QDate(intervento.data.year, intervento.data.month, intervento.data.day)
            )
            self.note_input.setText(intervento.note)

    def _on_accept(self) -> None:
        selected_date = self.data_input.to_python()
        if selected_date is None:
            _show_dialog_error(self, invalid_date_message())
            self.data_input.setFocus()
            return

        note = self.note_input.text().strip()

        try:
            if self._intervento is None:
                create_intervento(
                    InterventoCreate(
                        filtro_id=self._filtro_id,
                        data=selected_date,
                        note=note,
                    )
                )
            else:
                update_intervento(
                    InterventoUpdate(
                        intervento_id=self._intervento.intervento_id,
                        data=selected_date,
                        note=note,
                    )
                )
        except InterventoCrudError as error:
            _show_dialog_error(self, str(error))
            return

        self.accept()


def prompt_intervento(
    parent,
    filtro_id: int,
    intervento: InterventoVoce | None = None,
) -> bool:
    dialog = InterventoDialog(filtro_id, parent, intervento=intervento)
    return bool(dialog.exec())
