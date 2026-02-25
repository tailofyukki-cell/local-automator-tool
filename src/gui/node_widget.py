"""
フローノードウィジェット
フローエディタ内の各アクションを表すUIコンポーネント。
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.core.action_base import ActionStatus

# ステータスに対応する色の定義
STATUS_COLORS = {
    ActionStatus.PENDING:  ("#3a3a4a", "#888888"),   # (背景, テキスト)
    ActionStatus.RUNNING:  ("#1a3a5a", "#4fc3f7"),
    ActionStatus.SUCCESS:  ("#1a3a2a", "#66bb6a"),
    ActionStatus.FAILED:   ("#3a1a1a", "#ef5350"),
    ActionStatus.SKIPPED:  ("#2a2a2a", "#9e9e9e"),
}

# カテゴリに対応するアイコン文字
CATEGORY_ICONS = {
    "ファイル操作": "📁",
    "コマンド実行": "⚙",
    "変数処理":     "📦",
    "条件分岐":     "🔀",
    "トリガー":     "⏰",
    "その他":       "▶",
}


class NodeWidget(QFrame):
    """フローエディタ内の1つのアクションノードを表すウィジェット。"""

    clicked = Signal(object)      # クリック時に自身を渡す
    delete_requested = Signal(object)
    duplicate_requested = Signal(object)
    toggle_requested = Signal(object)

    def __init__(self, action_data: dict, parent=None):
        super().__init__(parent)
        self.action_data = action_data
        self._status = ActionStatus.PENDING
        self._selected = False
        self._setup_ui()
        self._apply_status_style()

    def _setup_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedHeight(72)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 6, 6)
        layout.setSpacing(8)

        # ドラッグハンドル
        self._handle = QLabel("⠿")
        self._handle.setFixedWidth(16)
        self._handle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._handle.setStyleSheet("color: #666; font-size: 18px;")
        layout.addWidget(self._handle)

        # ステータスインジケーター
        self._status_dot = QLabel("●")
        self._status_dot.setFixedWidth(14)
        self._status_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_dot.setStyleSheet("font-size: 10px;")
        layout.addWidget(self._status_dot)

        # メイン情報エリア
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)

        action_type = self.action_data.get("type", "")
        category = action_type.split(".")[0] if "." in action_type else "その他"
        icon = CATEGORY_ICONS.get(
            self._get_category_from_type(action_type), "▶"
        )

        # アクション名
        name = self.action_data.get("name", action_type)
        self._name_label = QLabel(f"{icon}  {name}")
        self._name_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._name_label.setStyleSheet("color: #e0e0e0;")
        info_layout.addWidget(self._name_label)

        # アクションタイプ
        self._type_label = QLabel(action_type)
        self._type_label.setFont(QFont("Segoe UI", 8))
        self._type_label.setStyleSheet("color: #888;")
        info_layout.addWidget(self._type_label)

        layout.addLayout(info_layout, stretch=1)

        # 有効/無効トグルボタン
        self._toggle_btn = QPushButton("●")
        self._toggle_btn.setFixedSize(24, 24)
        self._toggle_btn.setToolTip("有効/無効を切り替え")
        self._toggle_btn.clicked.connect(lambda: self.toggle_requested.emit(self))
        layout.addWidget(self._toggle_btn)

        # 複製ボタン
        self._dup_btn = QPushButton("⧉")
        self._dup_btn.setFixedSize(24, 24)
        self._dup_btn.setToolTip("複製")
        self._dup_btn.clicked.connect(lambda: self.duplicate_requested.emit(self))
        layout.addWidget(self._dup_btn)

        # 削除ボタン
        self._del_btn = QPushButton("✕")
        self._del_btn.setFixedSize(24, 24)
        self._del_btn.setToolTip("削除")
        self._del_btn.clicked.connect(lambda: self.delete_requested.emit(self))
        layout.addWidget(self._del_btn)

        self._update_toggle_style()

    def _get_category_from_type(self, action_type: str) -> str:
        prefix_map = {
            "file": "ファイル操作",
            "command": "コマンド実行",
            "variable": "変数処理",
            "condition": "条件分岐",
            "trigger": "トリガー",
        }
        prefix = action_type.split(".")[0] if "." in action_type else ""
        return prefix_map.get(prefix, "その他")

    def _apply_status_style(self):
        bg, fg = STATUS_COLORS.get(self._status, ("#3a3a4a", "#888888"))
        selected_border = "2px solid #4fc3f7" if self._selected else "1px solid #555"
        enabled = self.action_data.get("enabled", True)
        opacity = "1.0" if enabled else "0.5"

        self.setStyleSheet(f"""
            NodeWidget {{
                background-color: {bg};
                border: {selected_border};
                border-radius: 6px;
            }}
        """)

        dot_colors = {
            ActionStatus.PENDING:  "#888888",
            ActionStatus.RUNNING:  "#4fc3f7",
            ActionStatus.SUCCESS:  "#66bb6a",
            ActionStatus.FAILED:   "#ef5350",
            ActionStatus.SKIPPED:  "#9e9e9e",
        }
        dot_color = dot_colors.get(self._status, "#888888")
        self._status_dot.setStyleSheet(f"color: {dot_color}; font-size: 10px;")

        for btn in [self._dup_btn, self._del_btn, self._toggle_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: 1px solid #555;
                    border-radius: 4px;
                    color: #aaa;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #555;
                    color: #fff;
                }
            """)

    def set_status(self, status: ActionStatus):
        """ノードの実行ステータスを更新する。"""
        self._status = status
        self._apply_status_style()

    def set_selected(self, selected: bool):
        """選択状態を更新する。"""
        self._selected = selected
        self._apply_status_style()

    def update_from_data(self):
        """action_dataからUIを更新する。"""
        action_type = self.action_data.get("type", "")
        name = self.action_data.get("name", action_type)
        icon = CATEGORY_ICONS.get(self._get_category_from_type(action_type), "▶")
        self._name_label.setText(f"{icon}  {name}")
        self._type_label.setText(action_type)
        self._update_toggle_style()
        self._apply_status_style()

    def _update_toggle_style(self):
        enabled = self.action_data.get("enabled", True)
        if enabled:
            self._toggle_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: 1px solid #66bb6a;
                    border-radius: 4px;
                    color: #66bb6a;
                    font-size: 10px;
                }
                QPushButton:hover { background: #1a3a2a; }
            """)
            self._toggle_btn.setToolTip("クリックで無効化")
        else:
            self._toggle_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: 1px solid #555;
                    border-radius: 4px;
                    color: #555;
                    font-size: 10px;
                }
                QPushButton:hover { background: #333; }
            """)
            self._toggle_btn.setToolTip("クリックで有効化")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self)
        super().mousePressEvent(event)
