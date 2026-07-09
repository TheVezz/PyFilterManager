from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QTreeWidgetItem, QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (
    InfoBar,
    InfoBarPosition,
    ToolButton,
    ToolTipFilter,
    TreeWidget,
)

from backend.schemas.hierarchy import CHILD_NODE_TYPES, MOVABLE_NODE_TYPES, TreeNode
from backend.services.hierarchy_crud_service import (
    HierarchyCrudError,
    create_child,
    create_sede,
    delete_entity,
    list_move_targets,
    move_entity,
    update_entity,
    validate_child_create,
    validate_entity_move,
    validate_entity_rename,
    validate_sede_create,
)
from backend.services.hierarchy_service import load_hierarchy
from frontend.components.hierarchy_dialogs import (
    confirm_delete,
    prompt_move,
    prompt_quadro_filtro,
    prompt_quadro_filtro_edit,
    prompt_text,
)

NODE_LABELS = {
    "sede": "Sede",
    "reparto": "Reparto",
    "impianto": "Impianto",
    "quadro_elettrico": "Quadro elettrico",
}


class HierarchyTreeWidget(QWidget):
    SCROLLBAR_GUTTER = 24
    selection_changed = Signal(object)
    data_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("hierarchy-tree-panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        self.add_button = self._make_button(FIF.ADD, "Crea")
        self.edit_button = self._make_button(FIF.EDIT, "Modifica")
        self.delete_button = self._make_button(FIF.DELETE, "Elimina")
        self.move_button = self._make_button(FIF.MOVE, "Sposta")
        self.expand_button = self._make_button(FIF.CARE_DOWN_SOLID, "Espandi tutto")
        self.collapse_button = self._make_button(FIF.CARE_UP_SOLID, "Collassa tutto")

        toolbar.addWidget(self.add_button)
        toolbar.addWidget(self.edit_button)
        toolbar.addWidget(self.delete_button)
        toolbar.addWidget(self.move_button)
        toolbar.addStretch(1)
        toolbar.addWidget(self.expand_button)
        toolbar.addWidget(self.collapse_button)

        self.tree = TreeWidget(self)
        self.tree.setObjectName("hierarchy-tree")
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        self.tree.setViewportMargins(0, 0, self.SCROLLBAR_GUTTER, 0)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)

        layout.addLayout(toolbar)
        layout.addWidget(self.tree)

        self.add_button.clicked.connect(self._on_create)
        self.edit_button.clicked.connect(self._on_edit)
        self.delete_button.clicked.connect(self._on_delete)
        self.move_button.clicked.connect(self._on_move)
        self.expand_button.clicked.connect(self.tree.expandAll)
        self.collapse_button.clicked.connect(self.tree.collapseAll)

        self.refresh()

    def _make_button(self, icon, tooltip: str) -> ToolButton:
        button = ToolButton(icon, self)
        button.setToolTip(tooltip)
        button.installEventFilter(ToolTipFilter(button))
        return button

    def refresh(self, keep_selection: TreeNode | None = None) -> None:
        expanded_nodes = self._expanded_nodes()
        if keep_selection is None:
            keep_selection = self.selected_node()

        self.tree.clear()

        nodes = load_hierarchy()
        if not nodes:
            empty_item = QTreeWidgetItem(["Nessun elemento"])
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.tree.addTopLevelItem(empty_item)
            self._update_buttons()
            self.selection_changed.emit(None)
            return

        for node in nodes:
            self.tree.addTopLevelItem(self._create_item(node))

        self._restore_expanded_nodes(expanded_nodes)

        if keep_selection:
            self._select_node(keep_selection.node_type, keep_selection.entity_id)

        self._update_buttons()
        self.selection_changed.emit(self.selected_node())

    def selected_node(self) -> TreeNode | None:
        items = self.tree.selectedItems()
        if not items:
            return None
        node = items[0].data(0, Qt.ItemDataRole.UserRole)
        return node if isinstance(node, TreeNode) else None

    def select_entity(self, node_type: str, entity_id: int) -> None:
        self._select_node(node_type, entity_id)

    def _on_selection_changed(self) -> None:
        self._update_buttons()
        self.selection_changed.emit(self.selected_node())

    def _has_hierarchy_items(self) -> bool:
        if self.tree.topLevelItemCount() == 0:
            return False
        node = self.tree.topLevelItem(0).data(0, Qt.ItemDataRole.UserRole)
        return isinstance(node, TreeNode)

    def _update_buttons(self) -> None:
        node = self.selected_node()
        has_items = self._has_hierarchy_items()
        self.add_button.setEnabled(node is None or node.node_type in CHILD_NODE_TYPES)
        self.edit_button.setEnabled(node is not None)
        self.delete_button.setEnabled(node is not None)
        self.move_button.setEnabled(
            node is not None and node.node_type in MOVABLE_NODE_TYPES
        )
        self.expand_button.setEnabled(has_items)
        self.collapse_button.setEnabled(has_items)

    def _create_item(self, node: TreeNode) -> QTreeWidgetItem:
        item = QTreeWidgetItem([node.label])
        item.setData(0, Qt.ItemDataRole.UserRole, node)

        for child in node.children:
            item.addChild(self._create_item(child))

        return item

    def _select_node(self, node_type: str, entity_id: int) -> None:
        item = self._find_item(node_type, entity_id)
        if item is not None:
            self.tree.setCurrentItem(item)

    def _find_item(self, node_type: str, entity_id: int) -> QTreeWidgetItem | None:
        for index in range(self.tree.topLevelItemCount()):
            found = self._find_in_item(self.tree.topLevelItem(index), node_type, entity_id)
            if found is not None:
                return found
        return None

    def _find_in_item(
        self,
        item: QTreeWidgetItem,
        node_type: str,
        entity_id: int,
    ) -> QTreeWidgetItem | None:
        node = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(node, TreeNode) and node.node_type == node_type and node.entity_id == entity_id:
            return item

        for index in range(item.childCount()):
            found = self._find_in_item(item.child(index), node_type, entity_id)
            if found is not None:
                return found
        return None

    def _expanded_nodes(self) -> set[tuple[str, int]]:
        expanded: set[tuple[str, int]] = set()
        for index in range(self.tree.topLevelItemCount()):
            self._collect_expanded_nodes(self.tree.topLevelItem(index), expanded)
        return expanded

    def _collect_expanded_nodes(
        self,
        item: QTreeWidgetItem,
        expanded: set[tuple[str, int]],
    ) -> None:
        node = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(node, TreeNode) and item.isExpanded():
            expanded.add((node.node_type, node.entity_id))

        for index in range(item.childCount()):
            self._collect_expanded_nodes(item.child(index), expanded)

    def _restore_expanded_nodes(self, expanded_nodes: set[tuple[str, int]]) -> None:
        for node_type, entity_id in expanded_nodes:
            item = self._find_item(node_type, entity_id)
            if item is not None:
                item.setExpanded(True)

    def _show_error(self, message: str) -> None:
        InfoBar.error(
            "Errore",
            message,
            duration=4000,
            parent=self.window(),
            position=InfoBarPosition.TOP,
        )

    def _show_success(self, message: str) -> None:
        InfoBar.success(
            "Operazione completata",
            message,
            duration=2500,
            parent=self.window(),
            position=InfoBarPosition.TOP,
        )

    def _on_create(self) -> None:
        node = self.selected_node()
        if node is None:
            name = prompt_text(self.window(), "Nuova sede", "Nome sede")
            if not name:
                return
            try:
                create_sede(validate_sede_create(name))
                self.refresh()
                self.data_changed.emit()
                self._show_success("Sede creata.")
            except HierarchyCrudError as error:
                self._show_error(str(error))
            return

        child_type = CHILD_NODE_TYPES.get(node.node_type)
        if child_type is None:
            self._show_error("Non è possibile creare un elemento qui.")
            return

        if node.node_type == "impianto":
            if prompt_quadro_filtro(self.window(), node.entity_id):
                self.refresh(keep_selection=node)
                self.data_changed.emit()
                self._show_success("Quadro elettrico e filtro creati.")
            return

        label = NODE_LABELS[child_type]
        name = prompt_text(self.window(), f"Nuovo {label.lower()}", f"Nome {label.lower()}")
        if not name:
            return

        try:
            create_child(validate_child_create(node.node_type, node.entity_id, name))
            self.refresh(keep_selection=node)
            self.data_changed.emit()
            self._show_success(f"{label} creato.")
        except HierarchyCrudError as error:
            self._show_error(str(error))

    def _on_edit(self) -> None:
        node = self.selected_node()
        if node is None:
            return

        label = NODE_LABELS[node.node_type]

        if node.node_type == "quadro_elettrico":
            if not prompt_quadro_filtro_edit(self.window(), node.entity_id):
                return
            self.refresh(keep_selection=node)
            self.data_changed.emit()
            self._show_success(f"{label} aggiornato.")
            return

        name = prompt_text(
            self.window(),
            f"Modifica {label.lower()}",
            f"Nome {label.lower()}",
            node.label,
        )
        if not name or name == node.label:
            return

        try:
            update_entity(validate_entity_rename(node.node_type, node.entity_id, name))
            updated = TreeNode(
                label=name,
                node_type=node.node_type,
                entity_id=node.entity_id,
                children=node.children,
            )
            self.refresh(keep_selection=updated)
            self.data_changed.emit()
            self._show_success(f"{label} aggiornato.")
        except HierarchyCrudError as error:
            self._show_error(str(error))

    def _on_delete(self) -> None:
        node = self.selected_node()
        if node is None:
            return

        if not confirm_delete(self.window(), node.label):
            return

        try:
            delete_entity(node.node_type, node.entity_id)
            self.refresh()
            self.data_changed.emit()
            self._show_success("Elemento eliminato.")
        except HierarchyCrudError as error:
            self._show_error(str(error))

    def _on_move(self) -> None:
        node = self.selected_node()
        if node is None:
            return

        try:
            options = list_move_targets(node.node_type, node.entity_id)
        except HierarchyCrudError as error:
            self._show_error(str(error))
            return

        if not options:
            self._show_error("Nessuna destinazione disponibile.")
            return

        label = NODE_LABELS[node.node_type]
        new_parent_id = prompt_move(self.window(), f"Sposta {label.lower()}", options)
        if new_parent_id is None:
            return

        try:
            move_entity(validate_entity_move(node.node_type, node.entity_id, new_parent_id))
            self.refresh(keep_selection=node)
            self.data_changed.emit()
            self._show_success(f"{label} spostato.")
        except HierarchyCrudError as error:
            self._show_error(str(error))
