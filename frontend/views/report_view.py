import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import cast

from PySide6.QtCore import QMarginsF, QPoint, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPageLayout, QPainter
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    AdaptiveFlowLayout,
    BodyLabel,
    CaptionLabel,
    InfoBadge,
    PrimaryPushButton,
    ScrollArea,
    SimpleCardWidget,
    StrongBodyLabel,
    SubtitleLabel,
)
from qfluentwidgets import (
    FluentIcon as FIF,
)
from qfluentwidgets.components.widgets.info_badge import InfoLevel

from backend.i18n import (
    EMPTY_VALUE,
    filter_state_options,
    format_date,
    format_datetime,
    tr,
)
from backend.schemas.filtri import (
    ReportFilterState,
    ReportQuadroVoce,
    ReportSummary,
)
from backend.services.filtri_service import load_report_summary
from frontend.components.multi_select_filter_button import MultiSelectFilterButton
from frontend.components.section_divider import SectionDivider


def _format_report_date(value) -> str:
    if value is None:
        return EMPTY_VALUE
    return format_date(value)


class SummaryCard(SimpleCardWidget):
    def __init__(self, title: str, value: str, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        self.title_label = BodyLabel(title, self)
        self.title_label.setWordWrap(False)
        layout.addWidget(self.title_label)
        self.value_label = StrongBodyLabel(value, self)
        layout.addWidget(self.value_label)
        self.detail_label = BodyLabel("", self)
        self.detail_label.setWordWrap(True)
        self.detail_label.hide()
        layout.addWidget(self.detail_label)


class PrintSummaryCard(QFrame):
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setProperty("printCard", True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        self.title_label = QLabel(title, self)
        self.value_label = QLabel("", self)
        value_font = self.value_label.font()
        value_font.setPointSize(18)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.detail_label = QLabel("", self)
        self.detail_label.setWordWrap(True)
        self.detail_label.hide()

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.detail_label)


class ReportResultCard(SimpleCardWidget):
    CARD_MIN_HEIGHT = 160

    def __init__(self, voce: ReportQuadroVoce, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(self.CARD_MIN_HEIGHT)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        title = StrongBodyLabel(voce.quadro_elettrico, self)
        title.setWordWrap(True)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)
        header.addWidget(title, 1)
        header.addWidget(
            self._build_stato_badge(voce.stato),
            0,
            Qt.AlignmentFlag.AlignTop,
        )

        layout.addLayout(header)
        layout.addWidget(
            BodyLabel(tr("card.dimension", value=voce.dimensione_filtri), self)
        )
        layout.addWidget(
            CaptionLabel(tr("card.filter_quantity", value=voce.quantita_filtri), self)
        )
        layout.addWidget(
            CaptionLabel(
                tr(
                    "card.last_intervention",
                    date=_format_report_date(voce.ultimo_intervento),
                ),
                self,
            )
        )
        layout.addWidget(CaptionLabel(tr("card.new_intervention_date"), self))
        layout.addStretch(1)

    def _build_stato_badge(self, stato: str) -> InfoBadge:
        badges = {
            "ok": ("✓", InfoLevel.SUCCESS, tr("status.ok")),
            "warning": ("!", InfoLevel.WARNING, tr("status.warning")),
            "overdue": ("✗", InfoLevel.ERROR, tr("status.overdue")),
        }
        symbol, level, tooltip = badges[stato]
        badge = InfoBadge(symbol, self, level)
        badge.setToolTip(tooltip)
        badge.setFixedHeight(24)
        badge.setMinimumWidth(24)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return badge


class ReportCardsGridWidget(QWidget):
    CARD_MIN_WIDTH = 220

    def __init__(self, voci: list[ReportQuadroVoce], parent=None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._flow = AdaptiveFlowLayout(self, needAni=False)
        self._flow.setContentsMargins(0, 4, 0, 12)
        self._flow.setHorizontalSpacing(12)
        self._flow.setVerticalSpacing(12)
        self._flow.setWidgetMinimumWidth(self.CARD_MIN_WIDTH)

        for voce in voci:
            self._flow.addWidget(ReportResultCard(voce, self))

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._flow.heightForWidth(width)


def _group_voci_by_reparto_impianto(
    voci: list[ReportQuadroVoce],
) -> list[tuple[str, list[tuple[str, list[ReportQuadroVoce]]]]]:
    grouped: dict[str, dict[str, list[ReportQuadroVoce]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for voce in voci:
        grouped[voce.reparto][voce.impianto].append(voce)

    ordered: list[tuple[str, list[tuple[str, list[ReportQuadroVoce]]]]] = []
    for reparto in sorted(grouped):
        impianti: list[tuple[str, list[ReportQuadroVoce]]] = []
        for impianto in sorted(grouped[reparto]):
            cards = sorted(
                grouped[reparto][impianto],
                key=lambda item: item.quadro_elettrico,
            )
            impianti.append((impianto, cards))
        ordered.append((reparto, impianti))
    return ordered


def _summary_details(summary: ReportSummary) -> tuple[str, str]:
    quadri_detail = ""
    quadri_value = str(summary.quadri_scaduti)
    if summary.states == ["all"]:
        quadri_value = ""
        quadri_detail = "\n".join(
            [
                tr("report.summary.total", count=summary.quadri_scaduti),
                tr("report.summary.ok", count=summary.quadri_ok),
                tr("report.summary.overdue", count=summary.quadri_overdue),
                tr("report.summary.warning", count=summary.quadri_warning),
            ]
        )
    elif len(summary.states) > 1:
        details: list[str] = [tr("report.summary.total", count=summary.quadri_scaduti)]
        if "ok" in summary.states:
            details.append(tr("report.summary.ok", count=summary.quadri_ok))
        if "overdue" in summary.states:
            details.append(tr("report.summary.overdue", count=summary.quadri_overdue))
        if "warning" in summary.states:
            details.append(tr("report.summary.warning", count=summary.quadri_warning))
        quadri_value = ""
        quadri_detail = "\n".join(details)
    return quadri_value, quadri_detail


def _fill_summary_card(card: SummaryCard, summary: ReportSummary) -> None:
    card.title_label.setText(summary.title)
    quadri_value, quadri_detail = _summary_details(summary)
    card.value_label.setText(quadri_value)
    card.detail_label.setText(quadri_detail)
    card.detail_label.setVisible(bool(quadri_detail))


def _fill_filtri_card(card: SummaryCard, summary: ReportSummary) -> None:
    card.value_label.setText(str(summary.filtri_da_preparare))
    dettagli_dimensioni = "\n".join(
        tr(
            "report.filters_dimension_line",
            quantity=voce.quantita_filtri,
            dimension=voce.dimensione_filtri,
        )
        for voce in summary.filtri_per_dimensione
    )
    card.detail_label.setText(dettagli_dimensioni)
    card.detail_label.setVisible(bool(dettagli_dimensioni))


def _empty_message(states: list[ReportFilterState]) -> str:
    if states == ["all"]:
        return tr("report.empty.all")
    labels = {
        "ok": tr("report.state.ok"),
        "warning": tr("report.state.warning"),
        "overdue": tr("report.state.overdue"),
    }
    if len(states) == 1:
        return tr("report.empty.single", state=labels[states[0]])
    joined = ", ".join(labels[state] for state in states)
    return tr("report.empty.multiple", states=joined)


class PrintableReportPage(QFrame):
    PAGE_WIDTH = 980

    def __init__(self, summary: ReportSummary, generated_at: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("printable-report-page")
        self.setStyleSheet(
            """
            QFrame#printable-report-page {
                background: white;
                color: #202020;
            }
            QFrame#printable-report-page QFrame[printCard="true"] {
                background: white;
                border: 1px solid #d7d7d7;
                border-radius: 8px;
            }
            QFrame#printable-report-page QLabel {
                color: #202020;
                background: transparent;
            }
            QFrame#printable-report-page QFrame[dividerLine="true"] {
                border: none;
                border-top: 1px solid #d0d0d0;
                background: transparent;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(16)

        title = QLabel(tr("nav.report"), self)
        title_font = title.font()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        generated_label = QLabel(tr("report.generated_at", datetime=generated_at), self)
        layout.addWidget(generated_label)

        summary_row = QHBoxLayout()
        summary_row.setContentsMargins(0, 0, 0, 0)
        summary_row.setSpacing(12)
        self.quadri_card = self._create_summary_card(summary.title)
        self.filtri_card = self._create_summary_card(tr("report.filters_to_prepare"))
        summary_row.addWidget(self.quadri_card, 1)
        summary_row.addWidget(self.filtri_card, 1)
        layout.addLayout(summary_row)

        results_card = QFrame(self)
        results_card.setProperty("printCard", True)
        results_layout = QVBoxLayout(results_card)
        results_layout.setContentsMargins(16, 16, 16, 16)
        results_layout.setSpacing(12)
        section_title = QLabel(summary.title, results_card)
        section_font = section_title.font()
        section_font.setPointSize(13)
        section_font.setBold(True)
        section_title.setFont(section_font)
        results_layout.addWidget(section_title)

        if not summary.quadri_scaduti_voci:
            empty_label = QLabel(_empty_message(summary.states), results_card)
            empty_label.setWordWrap(True)
            results_layout.addWidget(empty_label)
        else:
            grouped_impianti = _group_voci_by_reparto_impianto(summary.quadri_scaduti_voci)
            for reparto, impianti in grouped_impianti:
                results_layout.addWidget(
                    self._create_divider(
                        tr("report.divider.reparto", name=reparto),
                        results_card,
                    )
                )
                for impianto, cards in impianti:
                    results_layout.addWidget(
                        self._create_divider(
                            tr("report.divider.impianto", name=impianto),
                            results_card,
                        )
                    )
                    results_layout.addLayout(self._create_cards_rows(cards))

        layout.addWidget(results_card)
        self._fill_summary_card(self.quadri_card, summary)
        self._fill_filtri_card(self.filtri_card, summary)

    def _create_summary_card(self, title: str) -> PrintSummaryCard:
        return PrintSummaryCard(title, self)

    def _fill_summary_card(
        self,
        card: PrintSummaryCard,
        summary: ReportSummary,
    ) -> None:
        card.title_label.setText(summary.title)
        quadri_value, quadri_detail = _summary_details(summary)
        card.value_label.setText(quadri_value)
        card.detail_label.setText(quadri_detail)
        card.detail_label.setVisible(bool(quadri_detail))

    def _fill_filtri_card(self, card: PrintSummaryCard, summary: ReportSummary) -> None:
        card.value_label.setText(str(summary.filtri_da_preparare))
        dettagli_dimensioni = "\n".join(
            tr(
                "report.filters_dimension_line",
                quantity=voce.quantita_filtri,
                dimension=voce.dimensione_filtri,
            )
            for voce in summary.filtri_per_dimensione
        )
        card.detail_label.setText(dettagli_dimensioni)
        card.detail_label.setVisible(bool(dettagli_dimensioni))

    def _create_divider(self, text: str, parent: QWidget) -> QWidget:
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(12)

        left_line = QFrame(widget)
        left_line.setProperty("dividerLine", True)
        label = QLabel(text, widget)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_line = QFrame(widget)
        right_line.setProperty("dividerLine", True)

        layout.addWidget(left_line, 1)
        layout.addWidget(label, 0)
        layout.addWidget(right_line, 1)
        return widget

    def _create_cards_rows(self, cards: list[ReportQuadroVoce]) -> QVBoxLayout:
        rows_layout = QVBoxLayout()
        rows_layout.setContentsMargins(0, 0, 0, 0)
        rows_layout.setSpacing(12)

        for start in range(0, len(cards), 3):
            row_widget = QWidget(self)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(12)

            for voce in cards[start : start + 3]:
                row_layout.addWidget(self._create_report_card(voce), 1)

            missing = 3 - len(cards[start : start + 3])
            for _ in range(missing):
                spacer = QWidget(row_widget)
                spacer.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Preferred,
                )
                row_layout.addWidget(spacer, 1)

            rows_layout.addWidget(row_widget)
        return rows_layout

    def _create_report_card(self, voce: ReportQuadroVoce) -> QFrame:
        card = QFrame(self)
        card.setProperty("printCard", True)
        card.setMinimumHeight(160)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        title = QLabel(voce.quadro_elettrico, card)
        title_font = title.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setWordWrap(True)
        header.addWidget(title, 1)

        badge = QLabel(self._badge_text(voce.stato), card)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(24, 24)
        badge.setStyleSheet(
            f"border-radius: 12px; font-weight: 700; {self._badge_style(voce.stato)}"
        )
        header.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)

        layout.addLayout(header)
        for text in [
            tr("card.dimension", value=voce.dimensione_filtri),
            tr("card.filter_quantity", value=voce.quantita_filtri),
            tr(
                "card.last_intervention",
                date=_format_report_date(voce.ultimo_intervento),
            ),
            tr("card.new_intervention_date"),
        ]:
            label = QLabel(text, card)
            label.setWordWrap(True)
            layout.addWidget(label)
        layout.addStretch(1)
        return card

    def _badge_text(self, stato: str) -> str:
        return {"ok": "✓", "warning": "!", "overdue": "✗"}[stato]

    def _badge_style(self, stato: str) -> str:
        styles = {
            "ok": "background: #dff3e4; color: #1f7a35;",
            "warning": "background: #fff2cc; color: #946200;",
            "overdue": "background: #ffd9d9; color: #a12626;",
        }
        return styles[stato]


class ReportInterface(QFrame):
    SCROLLBAR_GUTTER = 24

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("report-interface")
        self._current_summary: ReportSummary | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(16)

        layout.addWidget(SubtitleLabel(tr("nav.report"), self))

        controls_row = QHBoxLayout()
        controls_row.setContentsMargins(0, 0, 0, 0)
        controls_row.setSpacing(12)

        self.state_filter = MultiSelectFilterButton(
            tr("filter.panels"),
            filter_state_options(),
            parent=self,
        )
        self.state_filter.set_values(["overdue"])
        self.state_filter.valuesChanged.connect(self.reload)
        controls_row.addWidget(self.state_filter, 0, Qt.AlignmentFlag.AlignLeft)

        self.print_button = PrimaryPushButton(tr("report.print"), self)
        self.print_button.setIcon(FIF.PRINT)
        self.print_button.clicked.connect(self._print_report)
        controls_row.addWidget(self.print_button, 0, Qt.AlignmentFlag.AlignLeft)
        controls_row.addStretch(1)
        layout.addLayout(controls_row)

        summary_row = QHBoxLayout()
        summary_row.setContentsMargins(0, 0, 0, 0)
        summary_row.setSpacing(12)
        self.quadri_scaduti_card = SummaryCard(tr("report.panels_overdue"), "0", self)
        self.filtri_preparare_card = SummaryCard(
            tr("report.filters_to_prepare"),
            "0",
            self,
        )
        summary_row.addWidget(self.quadri_scaduti_card, 1)
        summary_row.addWidget(self.filtri_preparare_card, 1)
        layout.addLayout(summary_row)

        table_card = SimpleCardWidget(self)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(16, 16, 16, 16)
        table_layout.setSpacing(12)
        self.table_title = StrongBodyLabel(tr("report.panels_overdue"), table_card)
        table_layout.addWidget(self.table_title)

        self.empty_label = BodyLabel(tr("report.empty.all"), table_card)
        self.empty_label.hide()
        table_layout.addWidget(self.empty_label)

        self.cards_scroll = ScrollArea(table_card)
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cards_scroll.enableTransparentBackground()
        self.cards_scroll.viewport().setStyleSheet("background: transparent;")

        self.cards_container = QWidget(self.cards_scroll)
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, self.SCROLLBAR_GUTTER, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cards_scroll.setWidget(self.cards_container)
        table_layout.addWidget(self.cards_scroll)

        layout.addWidget(table_card, 1)
        self.reload()

    def reload(self) -> None:
        summary = load_report_summary(
            cast(list[ReportFilterState], self.state_filter.values())
        )
        self._apply_summary(summary)

    def _apply_summary(self, summary: ReportSummary) -> None:
        self._current_summary = summary
        _fill_summary_card(self.quadri_scaduti_card, summary)
        _fill_filtri_card(self.filtri_preparare_card, summary)
        self.table_title.setText(summary.title)

        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()

        self.empty_label.setText(_empty_message(summary.states))
        self.empty_label.setVisible(not summary.quadri_scaduti_voci)
        self.cards_scroll.setVisible(bool(summary.quadri_scaduti_voci))

        if summary.quadri_scaduti_voci:
            grouped_impianti = _group_voci_by_reparto_impianto(summary.quadri_scaduti_voci)
            for reparto, impianti in grouped_impianti:
                self.cards_layout.addWidget(
                    SectionDivider(
                        tr("report.divider.reparto", name=reparto),
                        self.cards_container,
                    ),
                    0,
                    Qt.AlignmentFlag.AlignTop,
                )
                for impianto, cards in impianti:
                    self.cards_layout.addWidget(
                        SectionDivider(
                            tr("report.divider.impianto", name=impianto),
                            self.cards_container,
                        ),
                        0,
                        Qt.AlignmentFlag.AlignTop,
                    )
                    self.cards_layout.addWidget(
                        ReportCardsGridWidget(cards, self.cards_container),
                        0,
                        Qt.AlignmentFlag.AlignTop,
                    )

    def _print_report(self) -> None:
        if self._current_summary is None:
            return

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
            prefix="filtri-report-",
        )
        temp_path = Path(temp_file.name)
        temp_file.close()

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(str(temp_path))
        printer.setPageMargins(QMarginsF(12, 12, 12, 12), QPageLayout.Unit.Millimeter)
        generated_at = format_datetime(datetime.now())

        page = PrintableReportPage(self._current_summary, generated_at, self)
        page.resize(PrintableReportPage.PAGE_WIDTH, 1)
        page_layout = page.layout()
        if page_layout is not None:
            page_layout.activate()
        page.adjustSize()
        page.resize(PrintableReportPage.PAGE_WIDTH, page.sizeHint().height())
        page.ensurePolished()

        page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
        scale_x = page_rect.width() / max(page.width(), 1)
        scale_y = page_rect.height() / max(page.height(), 1)
        scale = min(scale_x, scale_y)

        painter = QPainter(printer)
        painter.scale(scale, scale)
        page.render(painter, QPoint(0, 0))
        painter.end()

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(temp_path)))
