from datetime import date as date_value

from PySide6.QtCore import QDate, Qt, QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QWidget
from qfluentwidgets import (
    FluentIcon as FIF,
)
from qfluentwidgets import (
    Flyout,
    FlyoutAnimationType,
    LineEdit,
    TransparentToolButton,
)
from qfluentwidgets.components.date_time.fast_calendar_view import FastCalendarView

from backend.i18n import date_input_placeholder, format_date, parse_user_date, tr


class DateInput(QWidget):
    """Campo data digitabile con pulsante calendario."""

    dateChanged = Signal(QDate)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._active_flyout: Flyout | None = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(33)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.date_edit = LineEdit(self)
        self.date_edit.setPlaceholderText(date_input_placeholder())
        self.date_edit.setClearButtonEnabled(True)
        self._set_text(QDate.currentDate())

        self.calendar_button = TransparentToolButton(FIF.CALENDAR, self)
        self.calendar_button.setFixedSize(33, 33)
        self.calendar_button.setToolTip(tr("date.open_calendar"))
        self.calendar_button.clicked.connect(self._open_calendar)

        layout.addWidget(self.date_edit, 1)
        layout.addWidget(self.calendar_button)

    def setFocus(
        self,
        reason: Qt.FocusReason = Qt.FocusReason.OtherFocusReason,
    ) -> None:
        self.date_edit.setFocus(reason)

    def setDate(self, value: QDate) -> None:
        self._set_text(value)

    def date(self) -> QDate | None:
        parsed = self.to_python()
        if parsed is None:
            return QDate()
        return QDate(parsed.year, parsed.month, parsed.day)

    def to_python(self) -> date_value | None:
        return parse_user_date(self.date_edit.text())

    def _set_text(self, value: QDate) -> None:
        if not value.isValid():
            self.date_edit.setText("")
            return
        self.date_edit.setText(
            format_date(date_value(value.year(), value.month(), value.day()))
        )

    def _open_calendar(self) -> None:
        if self._active_flyout is not None:
            return

        view = FastCalendarView(None)
        view.setResetEnabled(False)
        view.dateChanged.connect(self._on_calendar_date)

        flyout = Flyout.make(
            view,
            self.calendar_button,
            self.window(),
            FlyoutAnimationType.DROP_DOWN,
        )
        self._active_flyout = flyout
        flyout.closed.connect(self._clear_active_flyout)
        view.dateChanged.connect(flyout.close)

        current = self.date()
        if current is not None and current.isValid() and current != QDate.currentDate():
            QTimer.singleShot(0, lambda: self._apply_calendar_date(view, current))

    def _apply_calendar_date(self, view: FastCalendarView, value: QDate) -> None:
        try:
            view.setDate(value)
        except RuntimeError:
            return

    def _clear_active_flyout(self) -> None:
        self._active_flyout = None

    def _on_calendar_date(self, value: QDate) -> None:
        self._set_text(value)
        self.dateChanged.emit(value)
