from collections.abc import Sequence
from typing import cast

from PySide6.QtCore import QEvent, Qt, QTimer, Signal
from PySide6.QtWidgets import QFrame, QSizePolicy, QVBoxLayout, QWidget
from qfluentwidgets import AdaptiveFlowLayout, BodyLabel, ScrollArea
from qfluentwidgets.components.widgets.scroll_bar import ScrollBarHandleDisplayMode

from backend.schemas.filtri import FiltroCard, ImpiantoFiltriSection, RepartoFiltriSection
from backend.schemas.hierarchy import TreeNode
from backend.schemas.stato_filtro import FiltroStato
from backend.services.filtri_service import (
    load_filtri_by_impianto,
    load_filtri_by_reparto,
    load_filtri_by_sede,
    load_quadro_detail,
)
from frontend.components.filtro_card import FiltroCardWidget
from frontend.components.quadro_detail_panel import QuadroDetailPanel
from frontend.components.section_divider import SectionDivider


class CardsGridWidget(QWidget):
    card_clicked = Signal(int)

    def __init__(
        self,
        cards: list[FiltroCard],
        min_card_width: int,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._flow = AdaptiveFlowLayout(self, needAni=False)
        self._flow.setContentsMargins(0, 4, 0, 12)
        self._flow.setHorizontalSpacing(12)
        self._flow.setVerticalSpacing(12)
        self._flow.setWidgetMinimumWidth(min_card_width)

        for card in cards:
            widget = FiltroCardWidget(card, self)
            widget.quadro_clicked.connect(self.card_clicked.emit)
            self._flow.addWidget(widget)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._flow.heightForWidth(width)


class FiltriGridPanel(QWidget):
    CARD_MIN_WIDTH = 220
    SCROLLBAR_GUTTER = 24
    header_changed = Signal(str)
    content_changed = Signal()
    detail_navigation_changed = Signal()
    data_changed = Signal()
    quadro_opened = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("filtri-grid-panel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._grid_context: TreeNode | None = None
        self._in_detail_view = False
        self._detail_quadro_id: int | None = None
        self._search_query = ""
        self._search_scopes: list[str] = ["all"]
        self._state_filters: list[FiltroStato] = []
        self._current_view_type: str | None = None
        self._current_view_data: (
            list[RepartoFiltriSection] | list[ImpiantoFiltriSection] | None
        ) = None

        self.content_layout = QVBoxLayout(self)
        self.content_layout.setContentsMargins(0, 0, self.SCROLLBAR_GUTTER, 0)
        self.content_layout.setSpacing(4)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._detail_panel = QuadroDetailPanel(self)
        self._detail_panel.interventi_changed.connect(self._on_interventi_changed)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self.content_layout.heightForWidth(width)

    def can_go_back(self) -> bool:
        return self._in_detail_view and self._grid_context is not None

    def is_in_detail_view(self) -> bool:
        return self._in_detail_view

    def go_back_to_grid(self) -> TreeNode | None:
        if not self.can_go_back():
            return None
        return self._grid_context

    def set_search_query(self, query: str) -> None:
        normalized = query.strip().lower()
        if normalized == self._search_query:
            return
        self._search_query = normalized
        self._apply_current_view()

    def set_search_scopes(self, scopes: Sequence[str]) -> None:
        normalized = [
            scope.strip().lower()
            for scope in scopes
            if isinstance(scope, str)
        ]
        if not normalized or "all" in normalized:
            normalized = ["all"]
        else:
            normalized = [scope for scope in normalized if scope != "all"]

        if normalized == self._search_scopes:
            return
        self._search_scopes = normalized
        self._apply_current_view()

    def set_state_filters(self, stati: Sequence[str]) -> None:
        normalized = cast(
            list[FiltroStato],
            [
                stato.strip().lower()
                for stato in stati
                if isinstance(stato, str)
                and stato.strip().lower() in {"ok", "warning", "overdue"}
            ],
        )
        if normalized == self._state_filters:
            return
        self._state_filters = normalized
        self._apply_current_view()

    def update_for_node(self, node: TreeNode) -> None:
        if node.node_type == "quadro_elettrico":
            self._show_quadro_detail(node.entity_id)
            return

        self._in_detail_view = False
        self._grid_context = node

        if node.node_type == "reparto":
            reparto_view = load_filtri_by_reparto(node.entity_id)
            if reparto_view is None:
                self._current_view_type = None
                self._current_view_data = None
                self._show_placeholder("Reparto non trovato.")
                self.header_changed.emit("Filtri")
                return
            self._current_view_type = "impianti"
            self._current_view_data = reparto_view.impianti
            self.header_changed.emit(reparto_view.reparto)
            self._apply_current_view()
            return

        if node.node_type == "sede":
            sede_view = load_filtri_by_sede(node.entity_id)
            if sede_view is None:
                self._current_view_type = None
                self._current_view_data = None
                self._show_placeholder("Sede non trovata.")
                self.header_changed.emit("Filtri")
                return
            self._current_view_type = "reparti"
            self._current_view_data = sede_view.reparti
            self.header_changed.emit(sede_view.sede)
            self._apply_current_view()
            return

        if node.node_type == "impianto":
            section = load_filtri_by_impianto(node.entity_id)
            if section is None:
                self._current_view_type = None
                self._current_view_data = None
                self._show_placeholder("Impianto non trovato.")
                self.header_changed.emit("Filtri")
                return
            self._current_view_type = "impianti"
            self._current_view_data = [section]
            self.header_changed.emit(section.impianto)
            self._apply_current_view()
            return

        self._current_view_type = None
        self._current_view_data = None
        self._show_placeholder(
            "Seleziona un elemento valido per visualizzare i filtri."
        )
        self.header_changed.emit("Filtri")

    def _show_quadro_detail(self, quadro_id: int) -> None:
        self._detail_quadro_id = quadro_id
        self._current_view_type = None
        self._current_view_data = None
        detail = load_quadro_detail(quadro_id)
        if detail is None:
            self._show_placeholder("Quadro non trovato.")
            self.header_changed.emit("Filtri")
            return

        self._clear_content()
        self._in_detail_view = True
        self._detail_panel.set_detail(detail)
        self._detail_panel.show()
        self.content_layout.addWidget(self._detail_panel, 1)
        self.header_changed.emit(detail.quadro_elettrico)
        self._refresh_layout()
        self.detail_navigation_changed.emit()

    def _reload_quadro_detail(self) -> None:
        if self._detail_quadro_id is None:
            return
        self._show_quadro_detail(self._detail_quadro_id)

    def _on_interventi_changed(self) -> None:
        self._reload_quadro_detail()
        self.data_changed.emit()

    def _on_card_clicked(self, quadro_id: int) -> None:
        self._show_quadro_detail(quadro_id)
        self.quadro_opened.emit(quadro_id)

    def _clear_content(self) -> None:
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None and widget is not self._detail_panel:
                widget.deleteLater()
        self._detail_panel.setParent(self)
        self._detail_panel.hide()

    def _show_placeholder(self, message: str) -> None:
        self._in_detail_view = False
        self._detail_quadro_id = None
        self._clear_content()
        placeholder = BodyLabel(message, self)
        placeholder.setWordWrap(True)
        placeholder.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.addWidget(placeholder)
        self._refresh_layout()

    def _render_reparti_sections(self, reparti: list[RepartoFiltriSection]) -> None:
        self._clear_content()
        has_cards = False

        for reparto in reparti:
            reparto_cards = [card for impianto in reparto.impianti for card in impianto.filtri]
            if not reparto_cards:
                continue

            has_cards = True
            self.content_layout.addWidget(
                SectionDivider(f"Reparto · {reparto.reparto}", self)
            )
            self._append_impianti_sections(reparto.impianti)

        if not has_cards:
            self._append_empty_state("Nessun filtro presente in questa sede.")
        self._refresh_layout()

    def _render_impianti_sections(self, impianti: list[ImpiantoFiltriSection]) -> None:
        self._clear_content()
        self._append_impianti_sections(impianti)
        self._refresh_layout()

    def _append_impianti_sections(self, impianti: list[ImpiantoFiltriSection]) -> None:
        has_cards = False

        for impianto in impianti:
            if not impianto.filtri:
                continue

            has_cards = True
            self.content_layout.addWidget(
                SectionDivider(f"Impianto · {impianto.impianto}", self)
            )
            self.content_layout.addWidget(self._build_cards_grid(impianto.filtri))

        if not has_cards:
            self._append_empty_state("Nessun filtro presente in questo reparto.")

    def _apply_current_view(self) -> None:
        if self._in_detail_view:
            return
        if self._current_view_type == "reparti":
            reparti = self._filter_reparti(
                cast(list[RepartoFiltriSection], self._current_view_data or [])
            )
            self._render_reparti_sections(reparti)
            return
        if self._current_view_type == "impianti":
            impianti = self._filter_impianti(
                cast(list[ImpiantoFiltriSection], self._current_view_data or [])
            )
            self._render_impianti_sections(impianti)

    def _filter_reparti(
        self,
        reparti: Sequence[RepartoFiltriSection],
    ) -> list[RepartoFiltriSection]:
        filtered: list[RepartoFiltriSection] = []
        for reparto in reparti:
            impianti = self._filter_impianti(reparto.impianti)
            if impianti:
                filtered.append(
                    RepartoFiltriSection(
                        reparto_id=reparto.reparto_id,
                        reparto=reparto.reparto,
                        impianti=impianti,
                    )
                )
        return filtered

    def _filter_impianti(
        self,
        impianti: Sequence[ImpiantoFiltriSection],
    ) -> list[ImpiantoFiltriSection]:
        filtered: list[ImpiantoFiltriSection] = []
        for impianto in impianti:
            cards = [card for card in impianto.filtri if self._matches_card(card)]
            if cards:
                filtered.append(
                    ImpiantoFiltriSection(
                        impianto_id=impianto.impianto_id,
                        impianto=impianto.impianto,
                        filtri=cards,
                    )
                )
        return filtered

    def _matches_card(self, card: FiltroCard) -> bool:
        if self._state_filters and card.stato not in self._state_filters:
            return False

        if not self._search_query:
            return True

        fields = {
            "quadro": card.quadro_elettrico,
            "reparto": card.reparto,
            "impianto": card.impianto,
            "dimensione": card.dimensione_filtri,
            "frequenza": card.frequenza_intervento,
            "quantita": str(card.quantita_filtri),
        }

        if self._search_scopes == ["all"]:
            haystack = " ".join(fields.values()).lower()
        else:
            haystack = " ".join(
                fields.get(scope, "")
                for scope in self._search_scopes
            ).lower()
        return self._search_query in haystack

    def _render_cards(self, cards: list[FiltroCard]) -> None:
        self._clear_content()
        if not cards:
            self._append_empty_state("Nessun filtro associato a questo quadro.")
        else:
            self.content_layout.addWidget(self._build_cards_grid(cards))
        self._refresh_layout()

    def _append_empty_state(self, message: str) -> None:
        label = BodyLabel(message, self)
        label.setWordWrap(True)
        self.content_layout.addWidget(label)

    def _build_cards_grid(self, cards: list[FiltroCard]) -> CardsGridWidget:
        grid = CardsGridWidget(cards, self.CARD_MIN_WIDTH, self)
        grid.card_clicked.connect(self._on_card_clicked)
        return grid

    def _refresh_layout(self) -> None:
        self.updateGeometry()
        self.content_changed.emit()
        if not self._in_detail_view:
            self.detail_navigation_changed.emit()


class FiltriContentScrollArea(ScrollArea):
    """Scroll area che abilita lo scroll solo se il contenuto supera il viewport."""

    def __init__(self, panel: FiltriGridPanel, parent=None) -> None:
        super().__init__(parent)
        self._panel = panel
        self._scroll_enabled = False

        self.setObjectName("filtri-content-scroll")
        self.setWidget(panel)
        self.setWidgetResizable(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.enableTransparentBackground()
        self.viewport().setStyleSheet("background: transparent;")

        panel.content_changed.connect(self.sync_content)
        self.viewport().installEventFilter(self)
        self._set_scroll_enabled(False)

    def eventFilter(self, obj, event) -> bool:
        if (
            obj is self.viewport()
            and event.type() == QEvent.Type.Wheel
            and not self._scroll_enabled
        ):
            event.ignore()
            return True
        return super().eventFilter(obj, event)

    def sync_content(self) -> None:
        QTimer.singleShot(0, self._apply_geometry)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_geometry()

    def wheelEvent(self, event) -> None:
        if not self._scroll_enabled:
            event.ignore()
            return
        super().wheelEvent(event)

    def _apply_geometry(self) -> None:
        viewport = self.viewport()
        width = max(viewport.width(), 1)
        viewport_height = max(viewport.height(), 1)

        if self._panel.is_in_detail_view():
            self._panel.resize(width, viewport_height)
            self._set_scroll_enabled(False)
            return

        content_height = max(self._panel.heightForWidth(width), 1)

        if content_height <= viewport_height:
            self._panel.resize(width, viewport_height)
            self._set_scroll_enabled(False)
        else:
            self._panel.resize(width, content_height)
            self._set_scroll_enabled(True)

    def _set_scroll_enabled(self, enabled: bool) -> None:
        self._scroll_enabled = enabled
        v_bar = self.scrollDelagate.vScrollBar
        v_bar.setForceHidden(not enabled)

        if enabled:
            v_bar.setHandleDisplayMode(ScrollBarHandleDisplayMode.ALWAYS)
            v_bar.groove.setOpacity(1)
            v_bar.handle.setOpacity(1)
            v_bar._isExpanded = True
            v_bar._isEnter = True
        else:
            v_bar.setHandleDisplayMode(ScrollBarHandleDisplayMode.ON_HOVER)
            v_bar._isExpanded = False
            v_bar._isEnter = False
            v_bar.groove.setOpacity(0)
            v_bar.handle.setOpacity(0)

        bar = self.verticalScrollBar()
        bar.setValue(0)
        if not enabled:
            bar.setRange(0, 0)
