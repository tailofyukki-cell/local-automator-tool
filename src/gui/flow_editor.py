"""
フローエディタウィジェット
ノードの追加・削除・複製・ドラッグ並び替えを提供する。
"""
import uuid
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.core.action_base import ActionStatus
from src.gui.node_widget import NodeWidget


class FlowEditor(QScrollArea):
    """ドラッグ並び替え可能なフローエディタ。"""

    node_selected = Signal(dict)      # ノード選択時にaction_dataを渡す
    flow_changed = Signal()           # フローが変更された時

    def __init__(self, parent=None):
        super().__init__(parent)
        self._nodes: List[NodeWidget] = []
        self._selected_node: Optional[NodeWidget] = None
        self._drag_node: Optional[NodeWidget] = None
        self._drag_start_y: int = 0
        self._drag_original_index: int = -1
        self._setup_ui()

    def _setup_ui(self):
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e2e;
                border: none;
            }
        """)

        self._container = QWidget()
        self._container.setStyleSheet("background-color: #1e1e2e;")
        self._layout = QVBoxLayout(self._container)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(4)

        # 空の状態のプレースホルダー
        self._placeholder = QLabel("← 左のパネルからアクションをダブルクリックして追加")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("color: #555; font-size: 13px; padding: 40px;")
        self._layout.addWidget(self._placeholder)

        self.setWidget(self._container)

    def _update_placeholder(self):
        if self._nodes:
            self._placeholder.hide()
        else:
            self._placeholder.show()

    def add_action(self, action_data: dict, index: int = -1) -> NodeWidget:
        """アクションをフローに追加する。"""
        if "id" not in action_data:
            action_data["id"] = str(uuid.uuid4())[:8]
        if "enabled" not in action_data:
            action_data["enabled"] = True

        node = NodeWidget(action_data)
        node.clicked.connect(self._on_node_clicked)
        node.delete_requested.connect(self._on_delete_requested)
        node.duplicate_requested.connect(self._on_duplicate_requested)
        node.toggle_requested.connect(self._on_toggle_requested)

        # ドラッグ&ドロップの設定
        node.setAcceptDrops(True)

        if index < 0 or index >= len(self._nodes):
            self._nodes.append(node)
            self._layout.addWidget(node)
        else:
            self._nodes.insert(index, node)
            self._layout.insertWidget(index, node)

        self._update_placeholder()
        self.flow_changed.emit()
        return node

    def remove_node(self, node: NodeWidget):
        """ノードをフローから削除する。"""
        if node in self._nodes:
            if self._selected_node == node:
                self._selected_node = None
                self.node_selected.emit({})
            self._nodes.remove(node)
            self._layout.removeWidget(node)
            node.deleteLater()
            self._update_placeholder()
            self.flow_changed.emit()

    def _on_node_clicked(self, node: NodeWidget):
        """ノードがクリックされた時の処理。"""
        if self._selected_node:
            self._selected_node.set_selected(False)
        self._selected_node = node
        node.set_selected(True)
        self.node_selected.emit(node.action_data)

    def _on_delete_requested(self, node: NodeWidget):
        """削除ボタンが押された時の処理。"""
        self.remove_node(node)

    def _on_duplicate_requested(self, node: NodeWidget):
        """複製ボタンが押された時の処理。"""
        import copy
        new_data = copy.deepcopy(node.action_data)
        new_data["id"] = str(uuid.uuid4())[:8]
        new_data["name"] = new_data.get("name", "") + " (コピー)"
        idx = self._nodes.index(node)
        self.add_action(new_data, idx + 1)

    def _on_toggle_requested(self, node: NodeWidget):
        """有効/無効トグルボタンが押された時の処理。"""
        node.action_data["enabled"] = not node.action_data.get("enabled", True)
        node.update_from_data()
        self.flow_changed.emit()

    def get_flow_actions(self) -> List[dict]:
        """現在のフローのアクションリストを返す。"""
        return [node.action_data for node in self._nodes]

    def load_flow(self, actions: List[dict]):
        """フローデータを読み込んでノードを再構築する。"""
        # 既存ノードをクリア
        for node in self._nodes[:]:
            self._layout.removeWidget(node)
            node.deleteLater()
        self._nodes.clear()
        self._selected_node = None

        for action_data in actions:
            self.add_action(action_data)

        self._update_placeholder()

    def clear_flow(self):
        """フローをクリアする。"""
        self.load_flow([])

    def set_node_status(self, action_id: str, status: ActionStatus):
        """指定IDのノードのステータスを更新する。"""
        for node in self._nodes:
            if node.action_data.get("id") == action_id:
                node.set_status(status)
                break

    def reset_all_status(self):
        """全ノードのステータスをPENDINGにリセットする。"""
        for node in self._nodes:
            node.set_status(ActionStatus.PENDING)

    def get_selected_node(self) -> Optional[NodeWidget]:
        """選択中のノードを返す。"""
        return self._selected_node

    def update_selected_node_data(self):
        """選択中のノードのUIを更新する。"""
        if self._selected_node:
            self._selected_node.update_from_data()
            self.flow_changed.emit()

    # ドラッグ&ドロップによる並び替え
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            child = self._container.childAt(self._container.mapFromGlobal(event.globalPosition().toPoint()))
            # NodeWidgetまたはその子ウィジェットを探す
            node = self._find_node_at(event.globalPosition().toPoint())
            if node:
                self._drag_node = node
                self._drag_start_y = event.globalPosition().toPoint().y()
                self._drag_original_index = self._nodes.index(node)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_node and (event.buttons() & Qt.MouseButton.LeftButton):
            current_y = event.globalPosition().toPoint().y()
            delta = current_y - self._drag_start_y
            if abs(delta) > 10:
                self._perform_drag(current_y)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_node = None
        super().mouseReleaseEvent(event)

    def _find_node_at(self, global_pos) -> Optional[NodeWidget]:
        """グローバル座標にあるNodeWidgetを返す。"""
        for node in self._nodes:
            local_pos = node.mapFromGlobal(global_pos)
            if node.rect().contains(local_pos):
                return node
        return None

    def _perform_drag(self, current_global_y: int):
        """ドラッグ中のノードを適切な位置に移動する。"""
        if not self._drag_node:
            return
        current_idx = self._nodes.index(self._drag_node)
        # 上下のノードとの境界を判定
        if current_idx > 0:
            prev_node = self._nodes[current_idx - 1]
            prev_center_y = prev_node.mapToGlobal(prev_node.rect().center()).y()
            if current_global_y < prev_center_y:
                self._swap_nodes(current_idx, current_idx - 1)
                return
        if current_idx < len(self._nodes) - 1:
            next_node = self._nodes[current_idx + 1]
            next_center_y = next_node.mapToGlobal(next_node.rect().center()).y()
            if current_global_y > next_center_y:
                self._swap_nodes(current_idx, current_idx + 1)
                return

    def _swap_nodes(self, idx1: int, idx2: int):
        """2つのノードの位置を入れ替える。"""
        if 0 <= idx1 < len(self._nodes) and 0 <= idx2 < len(self._nodes):
            # リストを入れ替え
            self._nodes[idx1], self._nodes[idx2] = self._nodes[idx2], self._nodes[idx1]
            # レイアウトを再構築
            for node in self._nodes:
                self._layout.removeWidget(node)
            for node in self._nodes:
                self._layout.addWidget(node)
            self.flow_changed.emit()
