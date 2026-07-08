from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    FluentWindow,
    NavigationItemPosition,
    PushButton,
    SimpleCardWidget,
    StrongBodyLabel,
    SubtitleLabel,
)
from qfluentwidgets import FluentIcon as FIF

from backend.config import get_app_name
from backend.i18n import filter_state_options, tr
from backend.services.filtri_service import load_home_status_summary
from frontend.components.filtri_grid_panel import (
    FiltriContentScrollArea,
    FiltriGridPanel,
)
from frontend.components.hierarchy_tree import HierarchyTreeWidget
from frontend.components.multi_select_filter_button import MultiSelectFilterButton
from frontend.components.scoped_search_line_edit import ScopedSearchLineEdit
from frontend.views.report_view import ReportInterface
from frontend.views.settings_view import SettingsInterface


class HomeInterface(QFrame):
    SEARCH_SCOPES_BY_NODE = {
        "sede": ["all", "quadro", "reparto", "linea", "dimensione", "frequenza", "quantita"],
        "reparto": ["all", "quadro", "linea", "dimensione", "frequenza", "quantita"],
        "linea": ["all", "quadro", "dimensione", "frequenza", "quantita"],
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
        self.filtri_panel.header_changed.connect(self.filtri_title.setText)
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

    def _on_tree_selection_changed(self, node) -> None:
        if node is None:
            self.filtri_title.setText(tr("nav.filtri"))
            self.content_stack.setCurrentIndex(0)
            self.search_input.set_available_scopes(
                [
                    "all",
                    "quadro",
                    "reparto",
                    "linea",
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
                ["all", "quadro", "reparto", "linea", "dimensione", "frequenza", "quantita"],
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
            "linea": tr("filtri.search.linea"),
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
        visible = (
            self.content_stack.currentIndex() == 1
            and not self.filtri_panel.is_in_detail_view()
        )
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


class HomeView(FluentWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(get_app_name())
        self.resize(1100, 700)

        self.dashboardInterface = DashboardInterface(self)
        self.filtriInterface = HomeInterface(self)
        self.reportInterface = ReportInterface(self)
        self.settingsInterface = SettingsInterface(self)
        self.addSubInterface(self.dashboardInterface, FIF.HOME, tr("nav.home"))
        self.addSubInterface(self.filtriInterface, FIF.IOT, tr("nav.filtri"))
        self.addSubInterface(self.reportInterface, FIF.DOCUMENT, tr("nav.report"))
        self.addSubInterface(
            self.settingsInterface,
            FIF.SETTING,
            tr("nav.settings"),
            position=NavigationItemPosition.BOTTOM,
        )
        self.settingsInterface.preferences_changed.connect(self._on_preferences_changed)
        self._setup_navigation_back()

    def _setup_navigation_back(self) -> None:
        nav_panel = self.navigationInterface.panel
        nav_panel.history.emptyChanged.disconnect(nav_panel.returnButton.setDisabled)
        nav_panel.returnButton.clicked.disconnect()

        nav_panel.returnButton.clicked.connect(self._on_navigation_back)
        self.filtriInterface.filtri_panel.detail_navigation_changed.connect(
            self._sync_return_button
        )
        self.stackedWidget.currentChanged.connect(self._sync_return_button)
        self._sync_return_button()

    def _on_navigation_back(self) -> None:
        current_widget = self.stackedWidget.currentWidget()
        if current_widget is self.filtriInterface:
            node = self.filtriInterface.filtri_panel.go_back_to_grid()
            if node is not None:
                self.filtriInterface.hierarchy_tree.select_entity(
                    node.node_type, node.entity_id
                )
        self._sync_return_button()

    def _sync_return_button(self, *_args) -> None:
        current_widget = self.stackedWidget.currentWidget()
        can_panel_back = (
            current_widget is self.filtriInterface
            and self.filtriInterface.filtri_panel.can_go_back()
        )
        self.navigationInterface.panel.returnButton.setDisabled(
            not can_panel_back
        )

    def _on_preferences_changed(self) -> None:
        self.dashboardInterface.reload()
        self.reportInterface.reload()
        self.filtriInterface.reload()
        self.settingsInterface.reload()
