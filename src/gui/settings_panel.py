"""
設定パネルウィジェット
選択されたアクションのパラメータを編集するためのUI。
"""
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class SettingsPanel(QScrollArea):
    """選択されたアクションのパラメータを編集するパネル。"""

    params_changed = Signal(dict)  # パラメータが変更された時

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_action_data: Optional[dict] = None
        self._param_widgets: Dict[str, QWidget] = {}
        self._setup_ui()

    def _setup_ui(self):
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("""
            QScrollArea {
                background-color: #252535;
                border: none;
            }
        """)

        self._content = QWidget()
        self._content.setStyleSheet("background-color: #252535;")
        self._main_layout = QVBoxLayout(self._content)
        self._main_layout.setContentsMargins(10, 10, 10, 10)
        self._main_layout.setSpacing(8)
        self._main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._placeholder = QLabel("← フローからアクションを選択してください")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("color: #555; font-size: 12px; padding: 20px;")
        self._main_layout.addWidget(self._placeholder)

        self.setWidget(self._content)

    def load_action(self, action_data: dict, params_schema: List[dict]):
        """アクションデータとスキーマからフォームを構築する。"""
        self._current_action_data = action_data
        self._param_widgets.clear()

        # 既存のウィジェットをクリア
        while self._main_layout.count():
            item = self._main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not action_data:
            self._placeholder = QLabel("← フローからアクションを選択してください")
            self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._placeholder.setStyleSheet("color: #555; font-size: 12px; padding: 20px;")
            self._main_layout.addWidget(self._placeholder)
            return

        # アクション名フィールド
        name_label = QLabel("アクション名")
        name_label.setStyleSheet("color: #aaa; font-size: 11px; font-weight: bold;")
        self._main_layout.addWidget(name_label)

        name_edit = QLineEdit(action_data.get("name", ""))
        name_edit.setStyleSheet(self._input_style())
        name_edit.textChanged.connect(self._on_name_changed)
        self._main_layout.addWidget(name_edit)
        self._param_widgets["__name__"] = name_edit

        # 区切り線
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #444;")
        self._main_layout.addWidget(sep)

        # アクションタイプ表示
        type_label = QLabel(f"タイプ: {action_data.get('type', '')}")
        type_label.setStyleSheet("color: #666; font-size: 10px;")
        self._main_layout.addWidget(type_label)

        # パラメータフィールド
        params = action_data.get("params", {})
        for schema in params_schema:
            param_name = schema["name"]
            label_text = schema.get("label", param_name)
            param_type = schema.get("type", "string")
            description = schema.get("description", "")
            current_value = params.get(param_name, schema.get("default", ""))

            # ラベル
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color: #ccc; font-size: 11px;")
            if description:
                lbl.setToolTip(description)
            self._main_layout.addWidget(lbl)

            # 入力ウィジェット
            widget = self._create_input_widget(param_type, current_value, schema)
            widget.setToolTip(description)
            self._main_layout.addWidget(widget)
            self._param_widgets[param_name] = widget

        # 変数ヘルプ
        help_label = QLabel("💡 {{変数名}} でテンプレート展開が使えます")
        help_label.setStyleSheet("color: #555; font-size: 10px; padding-top: 8px;")
        self._main_layout.addWidget(help_label)

        self._main_layout.addStretch()

    def _create_input_widget(self, param_type: str, current_value: Any, schema: dict) -> QWidget:
        """パラメータタイプに応じた入力ウィジェットを作成する。"""
        if param_type == "bool":
            widget = QCheckBox()
            checked = str(current_value).lower() not in ("false", "0", "no", "")
            widget.setChecked(checked)
            widget.setStyleSheet("color: #ccc;")
            widget.stateChanged.connect(self._on_param_changed)
            return widget

        elif param_type == "select":
            widget = QComboBox()
            options = schema.get("options", [])
            widget.addItems(options)
            if current_value in options:
                widget.setCurrentText(str(current_value))
            widget.setStyleSheet(self._combo_style())
            widget.currentTextChanged.connect(self._on_param_changed)
            return widget

        elif param_type == "multiline":
            widget = QPlainTextEdit()
            widget.setPlainText(str(current_value))
            widget.setMaximumHeight(120)
            widget.setStyleSheet(self._input_style())
            widget.textChanged.connect(self._on_param_changed)
            return widget

        else:  # string, number
            widget = QLineEdit(str(current_value))
            widget.setStyleSheet(self._input_style())
            widget.textChanged.connect(self._on_param_changed)
            return widget

    def _input_style(self) -> str:
        return """
            QLineEdit, QPlainTextEdit {
                background-color: #1e1e2e;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px 6px;
                font-size: 11px;
            }
            QLineEdit:focus, QPlainTextEdit:focus {
                border: 1px solid #4fc3f7;
            }
        """

    def _combo_style(self) -> str:
        return """
            QComboBox {
                background-color: #1e1e2e;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px 6px;
                font-size: 11px;
            }
            QComboBox:focus { border: 1px solid #4fc3f7; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #2a2a3a;
                color: #e0e0e0;
                selection-background-color: #3a3a5a;
            }
        """

    def _on_name_changed(self, text: str):
        if self._current_action_data is not None:
            self._current_action_data["name"] = text
            self.params_changed.emit(self._current_action_data)

    def _on_param_changed(self, *args):
        if self._current_action_data is None:
            return
        params = self._current_action_data.setdefault("params", {})
        for param_name, widget in self._param_widgets.items():
            if param_name == "__name__":
                continue
            if isinstance(widget, QCheckBox):
                params[param_name] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                params[param_name] = widget.currentText()
            elif isinstance(widget, QPlainTextEdit):
                params[param_name] = widget.toPlainText()
            elif isinstance(widget, QLineEdit):
                params[param_name] = widget.text()
        self.params_changed.emit(self._current_action_data)

    def clear(self):
        """パネルをクリアする。"""
        self.load_action({}, [])
