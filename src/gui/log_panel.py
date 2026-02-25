"""
ログパネルウィジェット
フロー実行のログをリアルタイムで表示するパネル。
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LogPanel(QWidget):
    """実行ログをリアルタイムで表示するパネル。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ヘッダー
        header_widget = QWidget()
        header_widget.setFixedHeight(32)
        header_widget.setStyleSheet("background-color: #1a1a2a; border-top: 1px solid #333;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(8, 0, 8, 0)

        header_label = QLabel("実行ログ")
        header_label.setStyleSheet("color: #aaa; font-size: 11px; font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        clear_btn = QPushButton("クリア")
        clear_btn.setFixedHeight(22)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #444;
                border-radius: 3px;
                color: #888;
                font-size: 10px;
                padding: 0 8px;
            }
            QPushButton:hover { background: #333; color: #ccc; }
        """)
        clear_btn.clicked.connect(self.clear)
        header_layout.addWidget(clear_btn)

        layout.addWidget(header_widget)

        # ログテキストエリア
        self._log_area = QPlainTextEdit()
        self._log_area.setReadOnly(True)
        self._log_area.setMaximumBlockCount(5000)
        self._log_area.setFont(QFont("Consolas", 9))
        self._log_area.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0d0d1a;
                color: #b0b0c0;
                border: none;
                padding: 4px;
            }
        """)
        layout.addWidget(self._log_area)

    def append_log(self, message: str):
        """ログメッセージを追加する。"""
        self._log_area.appendPlainText(message)
        # 最下部にスクロール
        cursor = self._log_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._log_area.setTextCursor(cursor)

    def clear(self):
        """ログをクリアする。"""
        self._log_area.clear()
