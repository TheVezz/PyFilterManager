from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QSizePolicy,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    InfoBadge,
    InfoBar,
    InfoBarPosition,
    MessageBox,
    PrimaryPushButton,
    SimpleCardWidget,
    StrongBodyLabel,
    TableWidget,
    ToolButton,
    ToolTipFilter,
)
from qfluentwidgets import (
    FluentIcon as FIF,
)
from qfluentwidgets.components.widgets.info_badge import InfoLevel

from backend.i18n import EMPTY_VALUE, format_date, tr
from backend.schemas.filtri import InterventoVoce, QuadroFiltroDetail
from backend.schemas.stato_filtro import FiltroStato
from backend.services.intervento_crud_service import (
    InterventoCrudError,
    delete_intervento,
)
from frontend.components.intervento_dialog import prompt_intervento


def _status_badge(stato: FiltroStato) -> tuple[str, InfoLevel, str]:
    badges = {
        "ok": ("✓", InfoLevel.SUCCESS, tr("status.ok")),
        "warning": ("!", InfoLevel.WARNING, tr("status.warning")),
        "overdue": ("✗", InfoLevel.ERROR, tr("status.overdue")),
    }
    return badges[stato]


INTERVENTO_ID_ROLE = Qt.ItemDataRole.UserRole


class DetailRow(QWidget):
    def __init__(self, label: str, value: str, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = CaptionLabel(label, self)
        title.setMinimumWidth(160)
        body = BodyLabel(value, self)
        body.setWordWrap(True)

        layout.addWidget(title, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(body, 1)


class InfoDivider(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(0)

        line = QFrame(self)
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setFixedHeight(1)
        layout.addWidget(line)


class QuadroDetailPanel(QWidget):
    interventi_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("quadro-detail-panel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._detail: QuadroFiltroDetail | None = None
        self._table_has_data_rows = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        badge_row = QHBoxLayout()
        badge_row.setContentsMargins(0, 0, 0, 0)
        badge_row.addStretch(1)
        self.badge_host = QWidget(self)
        self.badge_layout = QHBoxLayout(self.badge_host)
        self.badge_layout.setContentsMargins(0, 0, 0, 0)
        badge_row.addWidget(self.badge_host, 0, Qt.AlignmentFlag.AlignTop)

        self.path_label = CaptionLabel("", self)
        self.path_label.setWordWrap(True)

        self.info_card = SimpleCardWidget(self)
        info_layout = QVBoxLayout(self.info_card)
        info_layout.setContentsMargins(16, 14, 16, 14)
        info_layout.setSpacing(8)
        self.info_rows_host = QVBoxLayout()
        self.info_rows_host.setSpacing(6)
        info_layout.addLayout(self.info_rows_host)

        self.interventi_section = QWidget(self)
        self.interventi_section.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        interventi_layout = QVBoxLayout(self.interventi_section)
        interventi_layout.setContentsMargins(0, 0, 0, 0)
        interventi_layout.setSpacing(8)

        interventi_header = QHBoxLayout()
        interventi_header.setContentsMargins(0, 0, 0, 0)
        interventi_header.setSpacing(8)
        self.interventi_title = StrongBodyLabel(
            tr("detail.history"),
            self.interventi_section,
        )
        self.create_button = PrimaryPushButton(
            FIF.ADD, tr("detail.create_intervention"), self.interventi_section
        )
        self.edit_button = self._make_tool_button(
            FIF.EDIT, tr("detail.edit_intervention")
        )
        self.delete_button = self._make_tool_button(
            FIF.DELETE, tr("detail.delete_intervention")
        )
        interventi_header.addWidget(self.interventi_title)
        interventi_header.addStretch(1)
        interventi_header.addWidget(self.create_button)
        interventi_header.addWidget(self.edit_button)
        interventi_header.addWidget(self.delete_button)

        self.interventi_table = TableWidget(self.interventi_section)
        self.interventi_table.setMinimumHeight(160)
        self.interventi_table.setBorderVisible(True)
        self.interventi_table.setBorderRadius(8)
        self.interventi_table.setWordWrap(True)
        self.interventi_table.setColumnCount(2)
        self.interventi_table.setHorizontalHeaderLabels(
            [tr("detail.column.date"), tr("detail.column.notes")]
        )
        self.interventi_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.interventi_table.horizontalHeader().setStretchLastSection(True)
        self.interventi_table.verticalHeader().hide()
        self.interventi_table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed
        )
        self.interventi_table.verticalHeader().setDefaultSectionSize(36)
        self.interventi_table.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.interventi_table.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.interventi_table.setSelectionMode(TableWidget.SelectionMode.SingleSelection)
        self.interventi_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.interventi_table.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.interventi_table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        interventi_layout.addLayout(interventi_header, 0)
        interventi_layout.addWidget(self.interventi_table, 1)

        layout.addLayout(badge_row, 0)
        layout.addWidget(self.path_label, 0)
        layout.addWidget(self.info_card, 0)
        layout.addWidget(self.interventi_section, 1)

        self.create_button.clicked.connect(self._on_create_intervento)
        self.edit_button.clicked.connect(self._on_edit_selected)
        self.delete_button.clicked.connect(self._on_delete_selected)
        self.interventi_table.itemSelectionChanged.connect(self._update_action_buttons)
        self.interventi_table.doubleClicked.connect(self._on_edit_selected)

        self._update_action_buttons()

    def _make_tool_button(self, icon, tooltip: str) -> ToolButton:
        button = ToolButton(icon, self)
        button.setToolTip(tooltip)
        button.installEventFilter(ToolTipFilter(button))
        return button

    def set_detail(self, detail: QuadroFiltroDetail) -> None:
        self._detail = detail
        self.path_label.setText(
            f"{detail.sede} · {detail.reparto} · {detail.impianto}"
        )
        self._set_badge(detail.stato)
        self._rebuild_info_rows(detail)
        self._rebuild_interventi_table(detail)
        has_filtro = detail.filtro_id is not None
        self.create_button.setVisible(has_filtro)
        self.interventi_section.setVisible(True)
        self._update_action_buttons()

    def _set_badge(self, stato: FiltroStato) -> None:
        while self.badge_layout.count():
            item = self.badge_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()

        symbol, level, tooltip = _status_badge(stato)
        badge = InfoBadge(symbol, self.badge_host, level)
        badge.setToolTip(tooltip)
        badge.setFixedHeight(28)
        badge.setMinimumWidth(28)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_layout.addWidget(badge)

    def _rebuild_info_rows(self, detail: QuadroFiltroDetail) -> None:
        while self.info_rows_host.count():
            item = self.info_rows_host.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()

        if detail.filtro_id is None:
            self.info_rows_host.addWidget(
                BodyLabel(tr("detail.no_filter"), self.info_card)
            )
            return

        giorni = EMPTY_VALUE
        if detail.giorni_rimanenti is not None:
            if detail.giorni_rimanenti < 0:
                giorni = tr("detail.overdue_days", count=abs(detail.giorni_rimanenti))
            elif detail.giorni_rimanenti == 0:
                giorni = tr("detail.due_today")
            else:
                giorni = tr("detail.days", count=detail.giorni_rimanenti)

        preavviso = self._format_preavviso(detail)

        self._add_detail_row(
            tr("detail.filter_quantity"),
            (
                str(detail.quantita_filtri)
                if detail.quantita_filtri is not None
                else EMPTY_VALUE
            ),
        )
        self._add_detail_row(
            tr("detail.dimension"),
            detail.dimensione_filtri or EMPTY_VALUE,
        )
        self._add_detail_row(
            tr("detail.frequency"),
            detail.frequenza_intervento or EMPTY_VALUE,
        )
        self._add_detail_row(
            tr("detail.warning_config"),
            detail.preavviso_descrizione or EMPTY_VALUE,
        )
        self._add_divider()
        self._add_detail_row(
            tr("detail.last_intervention"),
            format_date(detail.ultimo_intervento),
        )
        self._add_detail_row(
            tr("detail.next_due"),
            format_date(detail.prossima_scadenza),
        )
        self._add_detail_row(tr("detail.days_to_due"), giorni)
        self._add_divider()
        self._add_detail_row(
            tr("detail.warning_duration"),
            self._format_giorni_preavviso(detail.giorni_preavviso),
        )
        self._add_detail_row(
            tr("detail.warning_start"),
            format_date(detail.data_inizio_preavviso),
        )
        self._add_detail_row(tr("detail.warning_status"), preavviso)

    def _add_detail_row(self, label: str, value: str) -> None:
        self.info_rows_host.addWidget(DetailRow(label, value, self.info_card))

    def _add_divider(self) -> None:
        self.info_rows_host.addWidget(InfoDivider(self.info_card))

    def _format_giorni_preavviso(self, giorni: int | None) -> str:
        if giorni is None:
            return EMPTY_VALUE
        return tr("detail.days", count=giorni)

    def _format_preavviso(self, detail: QuadroFiltroDetail) -> str:
        if detail.giorni_rimanenti is None or detail.giorni_preavviso is None:
            return EMPTY_VALUE
        if detail.stato == "overdue":
            return tr("status.overdue_short")
        if detail.stato == "warning":
            return tr("status.warning_short")
        giorni_al_preavviso = detail.giorni_rimanenti - detail.giorni_preavviso
        if giorni_al_preavviso <= 0:
            return tr("status.warning_short")
        if giorni_al_preavviso == 1:
            return tr("detail.in_days_one")
        return tr("detail.in_days", count=giorni_al_preavviso)

    def _rebuild_interventi_table(self, detail: QuadroFiltroDetail) -> None:
        self.interventi_table.clearSelection()
        self.interventi_table.clearSpans()
        self.interventi_table.setRowCount(0)
        self._table_has_data_rows = bool(detail.interventi)

        if not detail.interventi:
            self._set_empty_table_message()
            self._update_action_buttons()
            return

        self.interventi_table.setRowCount(len(detail.interventi))
        for row, intervento in enumerate(detail.interventi):
            date_item = self._table_item(format_date(intervento.data))
            date_item.setData(INTERVENTO_ID_ROLE, intervento.intervento_id)
            note = intervento.note.strip() or EMPTY_VALUE
            self.interventi_table.setItem(row, 0, date_item)
            self.interventi_table.setItem(row, 1, self._table_item(note))

        self.interventi_table.scrollToTop()
        self._update_action_buttons()

    def _set_empty_table_message(self) -> None:
        self.interventi_table.setRowCount(1)
        message = self._table_item(tr("detail.no_interventions"))
        message.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setFlags(Qt.ItemFlag.NoItemFlags)
        self.interventi_table.setItem(0, 0, message)
        self.interventi_table.setSpan(0, 0, 1, 2)

    def _selected_intervento(self) -> InterventoVoce | None:
        if not self._table_has_data_rows or self._detail is None:
            return None

        row = self.interventi_table.currentRow()
        if row < 0:
            return None

        date_item = self.interventi_table.item(row, 0)
        if date_item is None:
            return None

        intervento_id = date_item.data(INTERVENTO_ID_ROLE)
        if not intervento_id:
            return None

        return self._intervento_by_id(int(intervento_id))

    def _update_action_buttons(self) -> None:
        has_filtro = self._detail is not None and self._detail.filtro_id is not None
        has_selection = self._selected_intervento() is not None
        self.create_button.setEnabled(has_filtro)
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def _intervento_by_id(self, intervento_id: int) -> InterventoVoce | None:
        if self._detail is None:
            return None
        for intervento in self._detail.interventi:
            if intervento.intervento_id == intervento_id:
                return intervento
        return None

    def _on_create_intervento(self) -> None:
        if self._detail is None or self._detail.filtro_id is None:
            self._show_error(tr("detail.no_filter"))
            return
        if prompt_intervento(self.window(), self._detail.filtro_id):
            self._show_success(tr("detail.intervention_added"))
            self.interventi_changed.emit()

    def _on_edit_selected(self) -> None:
        intervento = self._selected_intervento()
        if intervento is None or self._detail is None or self._detail.filtro_id is None:
            return
        if prompt_intervento(
            self.window(),
            self._detail.filtro_id,
            intervento=intervento,
        ):
            self._show_success(tr("detail.intervention_updated"))
            self.interventi_changed.emit()

    def _on_delete_selected(self) -> None:
        intervento = self._selected_intervento()
        if intervento is None:
            return
        self._delete_intervento(intervento)

    def _delete_intervento(self, intervento: InterventoVoce) -> None:
        dialog = MessageBox(
            tr("detail.delete_confirm_title"),
            tr("detail.delete_confirm", date=format_date(intervento.data)),
            self.window(),
        )
        dialog.yesButton.setText(tr("common.delete"))
        dialog.cancelButton.setText(tr("common.cancel"))
        if not dialog.exec():
            return

        try:
            delete_intervento(intervento.intervento_id)
        except InterventoCrudError as error:
            self._show_error(str(error))
            return

        self._show_success(tr("detail.intervention_deleted"))
        self.interventi_changed.emit()

    def _show_error(self, message: str) -> None:
        InfoBar.error(
            tr("common.error"),
            message,
            duration=5000,
            parent=self.window(),
            position=InfoBarPosition.BOTTOM,
        )

    def _show_success(self, message: str) -> None:
        InfoBar.success(
            tr("common.success"),
            message,
            duration=3000,
            parent=self.window(),
            position=InfoBarPosition.BOTTOM,
        )

    def _table_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item
