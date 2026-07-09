from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout
from qfluentwidgets import BodyLabel, SimpleCardWidget, StrongBodyLabel, SubtitleLabel

from backend.i18n import tr
from backend.services.filtri_service import load_home_status_summary


class StatusSummaryCard(SimpleCardWidget):
    def __init__(self, title: str, value: str, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)
        layout.addWidget(BodyLabel(title, self))
        self.value_label = StrongBodyLabel(value, self)
        layout.addWidget(self.value_label)


class DashboardInterface(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("dashboard-interface")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(16)

        layout.addWidget(SubtitleLabel(tr("nav.home"), self))
        intro = BodyLabel(tr("dashboard.intro"), self)
        intro.setWordWrap(True)
        layout.addWidget(intro)

        cards_row = QHBoxLayout()
        cards_row.setContentsMargins(0, 0, 0, 0)
        cards_row.setSpacing(12)

        self.ok_card = StatusSummaryCard(tr("dashboard.ok"), "0", self)
        self.warning_card = StatusSummaryCard(tr("dashboard.warning"), "0", self)
        self.overdue_card = StatusSummaryCard(tr("dashboard.overdue"), "0", self)
        cards_row.addWidget(self.ok_card, 1)
        cards_row.addWidget(self.warning_card, 1)
        cards_row.addWidget(self.overdue_card, 1)
        layout.addLayout(cards_row)
        layout.addStretch(1)

        self.reload()

    def reload(self) -> None:
        summary = load_home_status_summary()
        self.ok_card.value_label.setText(str(summary.ok))
        self.warning_card.value_label.setText(str(summary.warning))
        self.overdue_card.value_label.setText(str(summary.overdue))
