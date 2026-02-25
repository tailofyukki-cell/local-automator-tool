"""
アクション一覧パネル
利用可能なアクションをカテゴリ別に表示するパネル。
"""
from typing import Dict, List, Type

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.core.action_base import ActionBase
from src.gui.node_widget import CATEGORY_ICONS


class ActionItemButton(QPushButton):
    """アクション一覧内の各アクションを表すボタン。"""

    def __init__(self, action_class: Type[ActionBase], parent=None):
        super().__init__(parent)
        self.action_class = action_class
        icon = CATEGORY_ICONS.get(action_class.CATEGORY, "▶")
        self.setText(f"{icon}  {action_class.DISPLAY_NAME}")
        self.setToolTip(action_class.DESCRIPTION)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(34)
        self.setStyleSheet("""
            QPushButton {
                background-color: #2a2a3a;
                color: #ccc;
                border: 1px solid #444;
                border-radius: 4px;
                text-align: left;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #3a3a5a;
                color: #fff;
                border: 1px solid #4fc3f7;
            }
            QPushButton:pressed {
                background-color: #1a2a4a;
            }
        """)


class ActionPanel(QWidget):
    """利用可能なアクションをカテゴリ別に表示するパネル。"""

    action_double_clicked = Signal(object)  # ダブルクリックされたアクションクラスを渡す

    def __init__(self, categories: Dict[str, List[Type[ActionBase]]], parent=None):
        super().__init__(parent)
        self._categories = categories
        self._all_buttons: List[ActionItemButton] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ヘッダー
        header = QLabel("アクション")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFixedHeight(36)
        header.setStyleSheet("""
            background-color: #1a1a2a;
            color: #aaa;
            font-size: 12px;
            font-weight: bold;
            border-bottom: 1px solid #333;
        """)
        layout.addWidget(header)

        # 検索ボックス
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("🔍 アクションを検索...")
        self._search_box.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e2e;
                color: #ccc;
                border: none;
                border-bottom: 1px solid #333;
                padding: 6px 10px;
                font-size: 11px;
            }
            QLineEdit:focus { border-bottom: 1px solid #4fc3f7; }
        """)
        self._search_box.textChanged.connect(self._filter_actions)
        layout.addWidget(self._search_box)

        # スクロールエリア
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background-color: #1e1e2e; border: none; }
        """)

        self._scroll_content = QWidget()
        self._scroll_content.setStyleSheet("background-color: #1e1e2e;")
        self._scroll_layout = QVBoxLayout(self._scroll_content)
        self._scroll_layout.setContentsMargins(6, 6, 6, 6)
        self._scroll_layout.setSpacing(4)
        self._scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # カテゴリ別にボタンを追加
        category_order = ["ファイル操作", "コマンド実行", "変数処理", "条件分岐", "トリガー", "その他"]
        sorted_categories = sorted(
            self._categories.items(),
            key=lambda x: category_order.index(x[0]) if x[0] in category_order else 99
        )

        for category, action_classes in sorted_categories:
            # カテゴリラベル
            cat_label = QLabel(f"  {CATEGORY_ICONS.get(category, '▶')} {category}")
            cat_label.setFixedHeight(26)
            cat_label.setStyleSheet("""
                color: #888;
                font-size: 10px;
                font-weight: bold;
                background-color: #252535;
                border-radius: 3px;
                padding-left: 4px;
            """)
            self._scroll_layout.addWidget(cat_label)

            for action_class in action_classes:
                btn = ActionItemButton(action_class)
                btn.clicked.connect(lambda checked, ac=action_class: self.action_double_clicked.emit(ac))
                self._scroll_layout.addWidget(btn)
                self._all_buttons.append(btn)

        self._scroll_layout.addStretch()
        scroll.setWidget(self._scroll_content)
        layout.addWidget(scroll)

    def _filter_actions(self, text: str):
        """検索テキストに基づいてアクションをフィルタリングする。"""
        text = text.lower()
        for btn in self._all_buttons:
            visible = (
                text in btn.action_class.DISPLAY_NAME.lower()
                or text in btn.action_class.DESCRIPTION.lower()
                or text in btn.action_class.ACTION_TYPE.lower()
            )
            btn.setVisible(visible)
