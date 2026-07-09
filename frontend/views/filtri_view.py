from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QSplitter, QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, PushButton, SubtitleLabel

from backend.i18n import filter_state_options, tr
from frontend.components.filtri_grid_panel import FiltriContentScrollArea, FiltriGridPanel
from frontend.components.hierarchy_tree import HierarchyTreeWidget
from frontend.components.multi_select_filter_button import MultiSelectFilterButton
from frontend.components.scoped_search_line_edit import ScopedSearchLineEdit


class FiltriInterface(QFrame):
    data_changed = Signal()
    SEARCH_SCOPES_BY_NODE = {
        "sede": ["all", "quadro", "reparto", "impianto", "dimensione", "frequenza", "quantita"],
        "reparto": ["all", "quadro", "impianto", "dimensione", "frequenza", "quantita"],
        "impianto": ["all", "quadro", "dimensione", "frequenza", "quantita"],
        "quadro_elettrico": ["all", "quadro", "dimensione", "frequenza", "quantita"],
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("home-interface")

        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        left_panel = QWidget(self)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(36, 36, 24, 36)
        left_layout.setSpacing(12)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.filtri_title = SubtitleLabel(tr("nav.filtri"), left_panel)
        self.filters_bar = QWidget(left_panel)
        filters_layout = QHBoxLayout(self.filters_bar)
        filters_layout.setContentsMargins(0, 0, 0, 0)
        filters_layout.setSpacing(12)

        self.search_input = ScopedSearchLineEdit(self.filters_bar)
        self.search_input.setPlaceholderText(tr("filtri.search.all_fields"))
        self.search_input.setMinimumWidth(280)

        self.state_filter = MultiSelectFilterButton(
            tr("filter.state"),
            filter_state_options(),
            parent=self.filters_bar,
        )

        self.reset_filters_button = PushButton(tr("common.reset"), self.filters_bar)
        self.reset_filters_button.setFixedHeight(33)

        filters_layout.addWidget(self.search_input, 1)
        filters_layout.addWidget(self.state_filter, 0)
        filters_layout.addWidget(self.reset_filters_button, 0)

        self.content_stack = QStackedWidget(left_panel)
        self.content_stack.setObjectName("filtri-content-stack")

        empty_page = QWidget(self.content_stack)
        empty_layout = QVBoxLayout(empty_page)
        empty_layout.setContentsMargins(0, 0, 0, 0)
        empty_layout.setSpacing(0)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.filtri_hint = BodyLabel(
            tr("filtri.hint"),
            empty_page,
        )
        self.filtri_hint.setWordWrap(True)
        self.filtri_hint.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        empty_layout.addWidget(self.filtri_hint)

        self.filtri_panel = FiltriGridPanel()
        self.content_scroll = FiltriContentScrollArea(self.filtri_panel, left_panel)

        scroll_page = QWidget(self.content_stack)
        scroll_page.setAutoFillBackground(False)
        scroll_layout = QVBoxLayout(scroll_page)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)
        scroll_layout.addWidget(self.content_scroll)

        self.content_stack.addWidget(empty_page)
        self.content_stack.addWidget(scroll_page)

        left_layout.addWidget(self.filtri_title)
        left_layout.addWidget(self.filters_bar)
        left_layout.addWidget(self.content_stack, 1)

        right_panel = QWidget(self)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(24, 36, 36, 36)
        right_layout.setSpacing(12)
        right_layout.addWidget(SubtitleLabel(tr("filtri.structure"), right_panel))
        self.hierarchy_tree = HierarchyTreeWidget(right_panel)
        right_layout.addWidget(self.hierarchy_tree, 1)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([600, 360])

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        self.hierarchy_tree.selection_changed.connect(self._on_tree_selection_changed)
        self.hierarchy_tree.data_changed.connect(self._emit_data_changed)
        self.filtri_panel.header_changed.connect(self.filtri_title.setText)
        self.filtri_panel.data_changed.connect(self._emit_data_changed)
        self.filtri_panel.quadro_opened.connect(self._on_quadro_opened)
        self.filtri_panel.detail_navigation_changed.connect(self._update_filters_bar_visibility)
        self.search_input.textChanged.connect(self.filtri_panel.set_search_query)
        self.search_input.scopesChanged.connect(self._on_search_scopes_changed)
        self.state_filter.valuesChanged.connect(self._on_state_filters_changed)
        self.reset_filters_button.clicked.connect(self._reset_filters)
        self._update_search_placeholder()
        self._on_tree_selection_changed(self.hierarchy_tree.selected_node())

    def _on_quadro_opened(self, quadro_id: int) -> None:
        self.hierarchy_tree.select_entity("quadro_elettrico", quadro_id)

    def _emit_data_changed(self) -> None:
        self.data_changed.emit()

    def _on_tree_selection_changed(self, node) -> None:
        if node is None:
            self.filtri_title.setText(tr("nav.filtri"))
            self.content_stack.setCurrentIndex(0)
            self.search_input.set_available_scopes(
                [
                    "all",
                    "quadro",
                    "reparto",
                    "impianto",
                    "dimensione",
                    "frequenza",
                    "quantita",
                ]
            )
            self._update_filters_bar_visibility()
            return

        self.search_input.set_available_scopes(
            self.SEARCH_SCOPES_BY_NODE.get(
                node.node_type,
                ["all", "quadro", "reparto", "impianto", "dimensione", "frequenza", "quantita"],
            )
        )
        self.content_stack.setCurrentIndex(1)
        self.filtri_panel.update_for_node(node)
        self.content_scroll.sync_content()
        self._update_filters_bar_visibility()

    def _on_search_scopes_changed(self, scopes: list[str]) -> None:
        self.filtri_panel.set_search_scopes(scopes)
        self._update_search_placeholder()

    def _on_state_filters_changed(self, values: list[str]) -> None:
        if values == ["all"]:
            self.filtri_panel.set_state_filters([])
            return
        self.filtri_panel.set_state_filters(values)

    def _reset_filters(self) -> None:
        self.search_input.set_scopes(["all"])
        self.search_input.clear()
        self.state_filter.set_values(["all"])
        self.filtri_panel.set_search_scopes(["all"])
        self.filtri_panel.set_search_query("")
        self.filtri_panel.set_state_filters([])

    def _update_search_placeholder(self) -> None:
        placeholders = {
            "all": tr("filtri.search.all"),
            "quadro": tr("filtri.search.quadro"),
            "reparto": tr("filtri.search.reparto"),
            "impianto": tr("filtri.search.impianto"),
            "dimensione": tr("filtri.search.dimensione"),
            "frequenza": tr("filtri.search.frequenza"),
            "quantita": tr("filtri.search.quantita"),
        }
        scopes = self.search_input.scopes()
        if scopes == ["all"]:
            placeholder = placeholders["all"]
        elif len(scopes) == 1:
            placeholder = placeholders.get(scopes[0], placeholders["all"])
        else:
            placeholder = tr("filtri.search.selected_fields")
        self.search_input.setPlaceholderText(placeholder)

    def _update_filters_bar_visibility(self) -> None:
        visible = self.content_stack.currentIndex() == 1 and not self.filtri_panel.is_in_detail_view()
        self.filters_bar.setVisible(visible)

    def reload(self) -> None:
        self.filtri_title.setText(tr("nav.filtri"))
        self.filtri_hint.setText(tr("filtri.hint"))
        self.search_input.setPlaceholderText(tr("filtri.search.all_fields"))
        self.state_filter.set_title(tr("filter.state"))
        self.state_filter.set_options(filter_state_options())
        self.reset_filters_button.setText(tr("common.reset"))
        self._update_search_placeholder()

        node = self.hierarchy_tree.selected_node()
        if node is not None:
            self.filtri_panel.update_for_node(node)
            self.content_scroll.sync_content()

    def reload_live_data(self) -> None:
        node = self.hierarchy_tree.selected_node()
        if node is not None:
            self.filtri_panel.update_for_node(node)
            self.content_scroll.sync_content()
