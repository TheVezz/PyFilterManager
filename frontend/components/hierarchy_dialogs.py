import re
from collections.abc import Callable

from pydantic import ValidationError
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout
from qfluentwidgets import (
    ComboBox,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    MessageBox,
    PrimaryPushButton,
    PushButton,
    SpinBox,
)

from backend.i18n import invalid_date_message
from backend.schemas.frequenza import FREQUENZA_ERROR_MESSAGE
from backend.schemas.hierarchy import (
    DIMENSIONE_FILTRI_PATTERN,
    NameInput,
    QuadroFiltroCreate,
    QuadroFiltroEditData,
    QuadroFiltroUpdate,
)
from backend.services.hierarchy_crud_service import (
    HierarchyCrudError,
    create_quadro_with_filtro,
    load_quadro_filtro_edit,
    update_quadro_with_filtro,
)
from frontend.components.date_input import DateInput
from frontend.components.frequenza_input import FrequenzaInput
from frontend.components.preavviso_advanced_section import PreavvisoAdvancedSection


def _show_dialog_error(dialog: QDialog, message: str) -> None:
    InfoBar.error(
        "Errore",
        message,
        duration=5000,
        parent=dialog,
        position=InfoBarPosition.BOTTOM,
    )


def _format_validation_error(error: ValidationError) -> str:
    for item in error.errors():
        field = item.get("loc", ())[-1] if item.get("loc") else None
        if field == "dimensione_filtri":
            return (
                "La dimensione deve usare il formato larghezzaxaltezza "
                "con la lettera x minuscola (es. 600x600)."
            )
        if field == "quadro_elettrico":
            return "Inserisci il nome del quadro elettrico."
        if field == "quantita_filtri":
            return "Inserisci la quantità filtri."
        if field == "frequenza_intervento":
            return FREQUENZA_ERROR_MESSAGE
        if field == "data_primo_intervento":
            return "Seleziona la data del primo intervento."
        if field == "preavviso_percentuale":
            return "Inserisci la percentuale per l'in scadenza."
        if field == "preavviso_massimo_giorni":
            return "Inserisci il tetto massimo in giorni per l'in scadenza."
    for item in error.errors():
        message = item.get("msg")
        if isinstance(message, str) and "preavviso" in message.lower():
            return message
    return "Controlla i dati inseriti."


def _dimensione_filtri_error(value: str) -> str | None:
    text = value.strip()
    if not text:
        return "Inserisci la dimensione dei filtri."
    if any(separator in text for separator in ("*", "×", "X")):
        return (
            "Usa solo la lettera x minuscola come separatore "
            "(es. 600x600, non 600*600)."
        )
    if not re.fullmatch(DIMENSIONE_FILTRI_PATTERN, text):
        return (
            "La dimensione deve usare il formato larghezzaxaltezza "
            "con la lettera x minuscola (es. 600x600)."
        )
    return None


class TextInputDialog(QDialog):
    def __init__(
        self,
        title: str,
        label: str,
        initial: str = "",
        parent=None,
        validate: Callable[[str], str | None] | None = None,
    ) -> None:
        super().__init__(parent)
        self._value: str | None = None
        self._validate = validate

        self.setWindowTitle(title)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setModal(True)
        self.resize(420, 140)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        layout.addWidget(QLabel(label, self))
        self.input = LineEdit(self)
        self.input.setText(initial)
        self.input.setClearButtonEnabled(True)
        layout.addWidget(self.input)

        buttons = QHBoxLayout()
        self.cancel_button = PushButton("Annulla", self)
        self.ok_button = PrimaryPushButton("Salva", self)
        buttons.addStretch(1)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.ok_button)
        layout.addLayout(buttons)

        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.clicked.connect(self._on_accept)
        self.input.returnPressed.connect(self._on_accept)

    def _on_accept(self) -> None:
        text = self.input.text()
        if self._validate is not None:
            message = self._validate(text)
            if message:
                _show_dialog_error(self, message)
                return

        try:
            self._value = NameInput(name=text).name
        except ValidationError:
            _show_dialog_error(self, "Il campo non può essere vuoto.")
            return
        self.accept()

    def value(self) -> str | None:
        return self._value


class QuadroFiltroDialog(QDialog):
    def __init__(
        self,
        linea_id: int,
        parent=None,
        edit_data: QuadroFiltroEditData | None = None,
    ) -> None:
        super().__init__(parent)
        self._linea_id = linea_id
        self._edit_data = edit_data
        self._edit_mode = edit_data is not None

        self.setWindowTitle(
            "Modifica quadro elettrico" if self._edit_mode else "Nuovo quadro elettrico"
        )
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setModal(True)
        self.resize(420, 460 if self._edit_mode else 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Nome quadro elettrico", self))
        self.quadro_input = LineEdit(self)
        self.quadro_input.setClearButtonEnabled(True)
        layout.addWidget(self.quadro_input)

        layout.addWidget(QLabel("Quantità filtri", self))
        self.quantita_input = SpinBox(self)
        self.quantita_input.setRange(1, 9999)
        self.quantita_input.setValue(1)
        self.quantita_input.setAccelerated(True)
        layout.addWidget(self.quantita_input)

        layout.addWidget(QLabel("Dimensione filtri", self))
        self.dimensione_input = LineEdit(self)
        self.dimensione_input.setPlaceholderText("es. 600x600")
        self.dimensione_input.setClearButtonEnabled(True)
        layout.addWidget(self.dimensione_input)

        layout.addWidget(QLabel("Frequenza intervento", self))
        self.frequenza_input = FrequenzaInput(self)
        layout.addWidget(self.frequenza_input)

        self.data_label = QLabel("Data primo intervento", self)
        self.data_input = DateInput(self)
        if self._edit_mode:
            self.data_label.hide()
            self.data_input.hide()
        else:
            layout.addWidget(self.data_label)
            layout.addWidget(self.data_input)

        self.preavviso_section = PreavvisoAdvancedSection(self)
        layout.addWidget(self.preavviso_section)

        buttons = QHBoxLayout()
        self.cancel_button = PushButton("Annulla", self)
        self.ok_button = PrimaryPushButton("Salva", self)
        buttons.addStretch(1)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.ok_button)
        layout.addLayout(buttons)

        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.clicked.connect(self._on_accept)
        self.quadro_input.returnPressed.connect(self._focus_quantita)
        self.quantita_input.editingFinished.connect(self._focus_dimensione)
        self.dimensione_input.returnPressed.connect(self._focus_frequenza)
        if not self._edit_mode:
            self.frequenza_input.amount_input.editingFinished.connect(self._focus_data)

        self.preavviso_section.expandedChanged.connect(self._adjust_dialog_size)

        if self._edit_data is not None:
            self._prefill_edit_data(self._edit_data)
        else:
            self.preavviso_section.set_preavviso(usa_globale=True, expand=False)

    def _prefill_edit_data(self, edit_data: QuadroFiltroEditData) -> None:
        self.quadro_input.setText(edit_data.quadro_elettrico)
        self.quantita_input.setValue(edit_data.quantita_filtri)
        self.dimensione_input.setText(edit_data.dimensione_filtri)
        if edit_data.frequenza_intervento:
            self.frequenza_input.set_value(edit_data.frequenza_intervento)
        self.preavviso_section.set_preavviso(
            usa_globale=edit_data.preavviso_usa_globale,
            percentuale=edit_data.preavviso_percentuale,
            massimo_giorni=edit_data.preavviso_massimo_giorni,
        )

    def _adjust_dialog_size(self) -> None:
        self.adjustSize()
        self.resize(max(self.width(), 420), self.sizeHint().height())

    def _focus_quantita(self) -> None:
        self.quantita_input.setFocus()

    def _focus_dimensione(self) -> None:
        self.dimensione_input.setFocus()

    def _focus_frequenza(self) -> None:
        self.frequenza_input.setFocus()

    def _focus_data(self) -> None:
        self.data_input.setFocus()

    def _selected_date(self):
        return self.data_input.to_python()

    def _on_accept(self) -> None:
        dimensione_error = _dimensione_filtri_error(self.dimensione_input.text())
        if dimensione_error:
            _show_dialog_error(self, dimensione_error)
            self.dimensione_input.setFocus()
            return

        frequenza_error = self.frequenza_input.validation_error()
        if frequenza_error:
            _show_dialog_error(self, frequenza_error)
            self.frequenza_input.setFocus()
            return

        preavviso_values = self.preavviso_section.preavviso_values()

        if self._edit_mode:
            if self._edit_data is None:
                return
            try:
                data = QuadroFiltroUpdate(
                    quadro_elettrico_id=self._edit_data.quadro_elettrico_id,
                    quadro_elettrico=self.quadro_input.text(),
                    quantita_filtri=self.quantita_input.value(),
                    dimensione_filtri=self.dimensione_input.text(),
                    frequenza_intervento=self.frequenza_input.value(),
                    preavviso_usa_globale=preavviso_values["preavviso_usa_globale"],
                    preavviso_percentuale=preavviso_values["preavviso_percentuale"],
                    preavviso_massimo_giorni=preavviso_values["preavviso_massimo_giorni"],
                )
            except ValidationError as error:
                _show_dialog_error(self, _format_validation_error(error))
                return

            try:
                update_quadro_with_filtro(data)
            except HierarchyCrudError as error:
                _show_dialog_error(self, str(error))
                return

            self.accept()
            return

        selected_date = self._selected_date()
        if selected_date is None:
            _show_dialog_error(self, invalid_date_message())
            self.data_input.setFocus()
            return

        try:
            create_data = QuadroFiltroCreate(
                linea_id=self._linea_id,
                quadro_elettrico=self.quadro_input.text(),
                quantita_filtri=self.quantita_input.value(),
                dimensione_filtri=self.dimensione_input.text(),
                frequenza_intervento=self.frequenza_input.value(),
                data_primo_intervento=selected_date,
                preavviso_usa_globale=preavviso_values["preavviso_usa_globale"],
                preavviso_percentuale=preavviso_values["preavviso_percentuale"],
                preavviso_massimo_giorni=preavviso_values["preavviso_massimo_giorni"],
            )
        except ValidationError as error:
            _show_dialog_error(self, _format_validation_error(error))
            return

        try:
            create_quadro_with_filtro(create_data)
        except HierarchyCrudError as error:
            _show_dialog_error(self, str(error))
            return

        self.accept()


class MoveDialog(QDialog):
    def __init__(
        self,
        title: str,
        options: list[tuple[int, str]],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._selected_id: int | None = None

        self.setWindowTitle(title)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setModal(True)
        self.resize(480, 160)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Seleziona la nuova destinazione", self))
        self.combo = ComboBox(self)
        for option_id, label in options:
            self.combo.addItem(label, userData=option_id)
        layout.addWidget(self.combo)

        buttons = QHBoxLayout()
        self.cancel_button = PushButton("Annulla", self)
        self.ok_button = PrimaryPushButton("Sposta", self)
        buttons.addStretch(1)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.ok_button)
        layout.addLayout(buttons)

        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.clicked.connect(self._on_accept)

    def _on_accept(self) -> None:
        self._selected_id = self.combo.currentData()
        self.accept()

    def selected_id(self) -> int | None:
        return self._selected_id


def prompt_text(
    parent,
    title: str,
    label: str,
    initial: str = "",
    validate: Callable[[str], str | None] | None = None,
) -> str | None:
    dialog = TextInputDialog(title, label, initial, parent, validate=validate)
    if dialog.exec():
        return dialog.value()
    return None


def prompt_quadro_filtro(parent, linea_id: int) -> bool:
    dialog = QuadroFiltroDialog(linea_id, parent)
    return bool(dialog.exec())


def prompt_quadro_filtro_edit(parent, quadro_id: int) -> bool:
    try:
        edit_data = load_quadro_filtro_edit(quadro_id)
    except HierarchyCrudError as error:
        _show_dialog_error(parent, str(error))
        return False

    dialog = QuadroFiltroDialog(edit_data.linea_id, parent, edit_data=edit_data)
    return bool(dialog.exec())


def prompt_move(parent, title: str, options: list[tuple[int, str]]) -> int | None:
    dialog = MoveDialog(title, options, parent)
    if dialog.exec():
        return dialog.selected_id()
    return None


def confirm_delete(parent, item_label: str) -> bool:
    dialog = MessageBox(
        "Conferma eliminazione",
        f"Eliminare \"{item_label}\" e tutti gli elementi collegati?",
        parent,
    )
    dialog.yesButton.setText("Elimina")
    dialog.cancelButton.setText("Annulla")
    return dialog.exec()
