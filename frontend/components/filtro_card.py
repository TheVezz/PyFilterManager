from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    InfoBadge,
    SimpleCardWidget,
    StrongBodyLabel,
)
from qfluentwidgets.components.widgets.info_badge import InfoLevel

from backend.i18n import format_date, tr
from backend.schemas.filtri import FiltroCard
from backend.schemas.stato_filtro import FiltroStato


def _status_badge(stato: FiltroStato) -> tuple[str, InfoLevel, str]:
    badges = {
        "ok": ("✓", InfoLevel.SUCCESS, tr("status.ok")),
        "warning": ("!", InfoLevel.WARNING, tr("status.warning")),
        "overdue": ("✗", InfoLevel.ERROR, tr("status.overdue")),
    }
    return badges[stato]


class FiltroCardWidget(SimpleCardWidget):
    CARD_MIN_HEIGHT = 160
    quadro_clicked = Signal(int)

    def __init__(self, card: FiltroCard, parent=None) -> None:
        super().__init__(parent)
        self._quadro_id = card.quadro_elettrico_id
        self.setMinimumHeight(self.CARD_MIN_HEIGHT)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clicked.connect(lambda: self.quadro_clicked.emit(self._quadro_id))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        title = StrongBodyLabel(card.quadro_elettrico, self)
        title.setWordWrap(True)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)
        header.addWidget(title, 1)
        header.addWidget(self._build_stato_badge(card.stato), 0, Qt.AlignmentFlag.AlignTop)

        dimensione = BodyLabel(
            tr("card.dimension", value=card.dimensione_filtri),
            self,
        )
        quantita = CaptionLabel(
            tr("card.filter_quantity", value=card.quantita_filtri),
            self,
        )
        frequenza = CaptionLabel(
            tr("card.frequency", value=card.frequenza_intervento),
            self,
        )
        if card.ultimo_intervento is not None:
            intervento_text = tr(
                "card.last_intervention",
                date=format_date(card.ultimo_intervento),
            )
        else:
            intervento_text = tr(
                "card.last_intervention",
                date=format_date(None),
            )
        intervento = CaptionLabel(intervento_text, self)

        layout.addLayout(header)
        layout.addWidget(dimensione)
        layout.addWidget(quantita)
        layout.addWidget(frequenza)
        layout.addWidget(intervento)
        layout.addStretch(1)

    def _build_stato_badge(self, stato: FiltroStato) -> InfoBadge:
        symbol, level, tooltip = _status_badge(stato)
        badge = InfoBadge(symbol, self, level)
        badge.setToolTip(tooltip)
        badge.setFixedHeight(24)
        badge.setMinimumWidth(24)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return badge
