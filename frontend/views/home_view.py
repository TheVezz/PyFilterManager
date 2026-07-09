from PySide6.QtCore import QTimer
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import FluentWindow, NavigationItemPosition

from backend.config import get_app_name
from backend.i18n import tr
from backend.services.app_preferences_service import load_app_preferences
from frontend.views.dashboard_view import DashboardInterface
from frontend.views.filtri_view import FiltriInterface
from frontend.views.report_view import ReportInterface
from frontend.views.settings_view import SettingsInterface


class HomeView(FluentWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(get_app_name())
        self.resize(1100, 700)

        self.dashboardInterface = DashboardInterface(self)
        self.filtriInterface = FiltriInterface(self)
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
        self._live_refresh_timer = QTimer(self)
        self._live_refresh_timer.timeout.connect(self._refresh_live_data)
        self._apply_live_refresh_interval()
        self._live_refresh_timer.start()

        self.filtriInterface.data_changed.connect(self._refresh_live_data)
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
        self._apply_live_refresh_interval()
        self._refresh_live_data()
        self.settingsInterface.reload()

    def _refresh_live_data(self) -> None:
        self.dashboardInterface.reload()
        self.reportInterface.reload()
        self.filtriInterface.reload_live_data()

    def _apply_live_refresh_interval(self) -> None:
        preferences = load_app_preferences()
        interval_ms = int(preferences.live_refresh_seconds) * 1000
        self._live_refresh_timer.setInterval(interval_ms)
