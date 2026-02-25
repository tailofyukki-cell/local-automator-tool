"""
メインウィンドウ
アプリケーションのメインウィンドウ。
左：アクション一覧、中央：フローエディタ、右：設定パネル、下：ログパネル
"""
import copy
import json
import os
import sys
import threading
import uuid
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Qt, Signal, QObject
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.core.action_base import ActionStatus
from src.core.dispatcher import ActionDispatcher
from src.core.engine import FlowEngine
from src.gui.action_panel import ActionPanel
from src.gui.flow_editor import FlowEditor
from src.gui.log_panel import LogPanel
from src.gui.settings_panel import SettingsPanel


class FlowRunnerSignals(QObject):
    """フロー実行スレッドからGUIスレッドへの通知用シグナル。"""
    step_start = Signal(int, dict)
    step_complete = Signal(int, dict, object)
    flow_complete = Signal(bool, str)
    log_message = Signal(str)


class FlowRunnerThread(QThread):
    """フローを別スレッドで実行するスレッドクラス。"""

    def __init__(self, engine: FlowEngine, flow_data: dict, signals: FlowRunnerSignals):
        super().__init__()
        self.engine = engine
        self.flow_data = flow_data
        self.signals = signals

    def run(self):
        self.engine.on_step_start = lambda i, a: self.signals.step_start.emit(i, a)
        self.engine.on_step_complete = lambda i, a, r: self.signals.step_complete.emit(i, a, r)
        self.engine.on_flow_complete = lambda s, p: self.signals.flow_complete.emit(s, p)
        self.engine.on_log = lambda m: self.signals.log_message.emit(m)
        self.engine.run_flow(self.flow_data)


class MainWindow(QMainWindow):
    """アプリケーションのメインウィンドウ。"""

    def __init__(self, base_dir: str):
        super().__init__()
        self.base_dir = base_dir
        self.engine = FlowEngine(base_dir)
        self.dispatcher = ActionDispatcher()
        self._current_flow_path: Optional[str] = None
        self._current_flow_data = {"name": "新しいフロー", "description": "", "actions": []}
        self._runner_thread: Optional[FlowRunnerThread] = None
        self._runner_signals = FlowRunnerSignals()
        self._command_warning_shown = False

        self._setup_ui()
        self._connect_signals()
        self._apply_stylesheet()
        self._update_title()

    def _setup_ui(self):
        self.setWindowTitle("Local Automator")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)

        # ツールバー
        self._setup_toolbar()

        # メインレイアウト
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 水平スプリッター（左：アクション、中：フロー、右：設定）
        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        h_splitter.setHandleWidth(2)
        h_splitter.setStyleSheet("QSplitter::handle { background: #333; }")

        # 左パネル：アクション一覧
        categories = self.dispatcher.get_categories()
        self._action_panel = ActionPanel(categories)
        self._action_panel.setMinimumWidth(180)
        self._action_panel.setMaximumWidth(280)
        h_splitter.addWidget(self._action_panel)

        # 中央パネル：フローエディタ
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        # フロー名ヘッダー
        self._flow_header = QLabel()
        self._flow_header.setFixedHeight(36)
        self._flow_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._flow_header.setStyleSheet("""
            background-color: #1a1a2a;
            color: #ccc;
            font-size: 13px;
            font-weight: bold;
            border-bottom: 1px solid #333;
        """)
        center_layout.addWidget(self._flow_header)

        self._flow_editor = FlowEditor()
        center_layout.addWidget(self._flow_editor)
        h_splitter.addWidget(center_widget)

        # 右パネル：設定
        self._settings_panel = SettingsPanel()
        self._settings_panel.setMinimumWidth(220)
        self._settings_panel.setMaximumWidth(360)
        h_splitter.addWidget(self._settings_panel)

        h_splitter.setSizes([220, 700, 280])

        # 垂直スプリッター（上：メイン、下：ログ）
        v_splitter = QSplitter(Qt.Orientation.Vertical)
        v_splitter.setHandleWidth(2)
        v_splitter.setStyleSheet("QSplitter::handle { background: #333; }")
        v_splitter.addWidget(h_splitter)

        self._log_panel = LogPanel()
        self._log_panel.setMinimumHeight(80)
        v_splitter.addWidget(self._log_panel)
        v_splitter.setSizes([550, 180])

        main_layout.addWidget(v_splitter)

        # ステータスバー
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet("background-color: #1a1a2a; color: #888; font-size: 10px;")
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("準備完了")

    def _setup_toolbar(self):
        """ツールバーを設定する。"""
        toolbar = QToolBar("メインツールバー")
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #1a1a2a;
                border-bottom: 1px solid #333;
                spacing: 4px;
                padding: 4px;
            }
            QToolButton {
                background-color: #2a2a3a;
                color: #ccc;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
            }
            QToolButton:hover { background-color: #3a3a5a; color: #fff; }
            QToolButton:pressed { background-color: #1a2a4a; }
        """)
        self.addToolBar(toolbar)

        # 新規
        new_action = QAction("📄 新規", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_flow)
        toolbar.addAction(new_action)

        # 開く
        open_action = QAction("📂 開く", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_flow)
        toolbar.addAction(open_action)

        # 保存
        save_action = QAction("💾 保存", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_flow)
        toolbar.addAction(save_action)

        # 名前を付けて保存
        saveas_action = QAction("💾 名前を付けて保存", self)
        saveas_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        saveas_action.triggered.connect(self._save_flow_as)
        toolbar.addAction(saveas_action)

        toolbar.addSeparator()

        # フロー名編集
        rename_action = QAction("✏ フロー名変更", self)
        rename_action.triggered.connect(self._rename_flow)
        toolbar.addAction(rename_action)

        toolbar.addSeparator()

        # 実行ボタン
        self._run_btn = QAction("▶ 実行", self)
        self._run_btn.setShortcut(QKeySequence("F5"))
        self._run_btn.triggered.connect(self._run_flow)
        toolbar.addAction(self._run_btn)

        # 停止ボタン
        self._stop_btn = QAction("⏹ 停止", self)
        self._stop_btn.setShortcut(QKeySequence("F6"))
        self._stop_btn.triggered.connect(self._stop_flow)
        self._stop_btn.setEnabled(False)
        toolbar.addAction(self._stop_btn)

        toolbar.addSeparator()

        # フロー管理ボタン
        flows_action = QAction("📋 フロー管理", self)
        flows_action.triggered.connect(self._show_flows_folder)
        toolbar.addAction(flows_action)

        logs_action = QAction("📊 ログ一覧", self)
        logs_action.triggered.connect(self._show_logs_folder)
        toolbar.addAction(logs_action)

    def _connect_signals(self):
        """シグナルを接続する。"""
        self._action_panel.action_double_clicked.connect(self._add_action_to_flow)
        self._flow_editor.node_selected.connect(self._on_node_selected)
        self._flow_editor.flow_changed.connect(self._on_flow_changed)
        self._settings_panel.params_changed.connect(self._on_params_changed)

        self._runner_signals.step_start.connect(self._on_step_start)
        self._runner_signals.step_complete.connect(self._on_step_complete)
        self._runner_signals.flow_complete.connect(self._on_flow_complete)
        self._runner_signals.log_message.connect(self._log_panel.append_log)

    def _apply_stylesheet(self):
        """アプリケーション全体のスタイルシートを適用する。"""
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; }
            QWidget { background-color: #1e1e2e; color: #e0e0e0; }
            QSplitter { background-color: #1e1e2e; }
            QScrollBar:vertical {
                background: #1a1a2a;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #444;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background: #666; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QMessageBox { background-color: #252535; color: #e0e0e0; }
            QInputDialog { background-color: #252535; color: #e0e0e0; }
        """)

    def _update_title(self):
        """タイトルバーを更新する。"""
        flow_name = self._current_flow_data.get("name", "新しいフロー")
        path_info = f" - {self._current_flow_path}" if self._current_flow_path else " (未保存)"
        self.setWindowTitle(f"Local Automator - {flow_name}{path_info}")
        self._flow_header.setText(f"フロー: {flow_name}")

    def _new_flow(self):
        """新しいフローを作成する。"""
        reply = QMessageBox.question(
            self, "新規フロー",
            "現在のフローを破棄して新しいフローを作成しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._current_flow_data = {"name": "新しいフロー", "description": "", "actions": []}
            self._current_flow_path = None
            self._flow_editor.clear_flow()
            self._settings_panel.clear()
            self._log_panel.clear()
            self._update_title()

    def _open_flow(self):
        """フローJSONファイルを開く。"""
        flows_dir = str(self.engine.flows_dir)
        path, _ = QFileDialog.getOpenFileName(
            self, "フローを開く", flows_dir, "フローファイル (*.json);;全てのファイル (*)"
        )
        if path:
            try:
                flow_data = self.engine.load_flow(path)
                self._current_flow_data = flow_data
                self._current_flow_path = path
                self._flow_editor.load_flow(flow_data.get("actions", []))
                self._settings_panel.clear()
                self._update_title()
                self._status_bar.showMessage(f"フローを読み込みました: {path}")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"フローの読み込みに失敗しました:\n{e}")

    def _save_flow(self):
        """フローを保存する。"""
        if self._current_flow_path:
            self._do_save(self._current_flow_path)
        else:
            self._save_flow_as()

    def _save_flow_as(self):
        """名前を付けてフローを保存する。"""
        flows_dir = str(self.engine.flows_dir)
        flow_name = self._current_flow_data.get("name", "新しいフロー")
        safe_name = "".join(c if c.isalnum() or c in "_- " else "_" for c in flow_name)
        default_path = os.path.join(flows_dir, f"{safe_name}.json")
        path, _ = QFileDialog.getSaveFileName(
            self, "フローを保存", default_path, "フローファイル (*.json);;全てのファイル (*)"
        )
        if path:
            self._current_flow_path = path
            self._do_save(path)

    def _do_save(self, path: str):
        """実際の保存処理。"""
        try:
            # フローエディタからアクションリストを取得して更新
            self._current_flow_data["actions"] = self._flow_editor.get_flow_actions()
            self.engine.save_flow(self._current_flow_data, path)
            self._update_title()
            self._status_bar.showMessage(f"保存しました: {path}")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"フローの保存に失敗しました:\n{e}")

    def _rename_flow(self):
        """フロー名を変更する。"""
        current_name = self._current_flow_data.get("name", "")
        new_name, ok = QInputDialog.getText(
            self, "フロー名変更", "新しいフロー名:", text=current_name
        )
        if ok and new_name.strip():
            self._current_flow_data["name"] = new_name.strip()
            self._update_title()

    def _add_action_to_flow(self, action_class):
        """アクションをフローに追加する。"""
        action_data = {
            "id": str(uuid.uuid4())[:8],
            "type": action_class.ACTION_TYPE,
            "name": action_class.DISPLAY_NAME,
            "params": action_class().get_default_params(),
            "enabled": True,
        }
        self._flow_editor.add_action(action_data)
        self._status_bar.showMessage(f"アクションを追加しました: {action_class.DISPLAY_NAME}")

    def _on_node_selected(self, action_data: dict):
        """ノードが選択された時の処理。"""
        if not action_data:
            self._settings_panel.clear()
            return
        action_type = action_data.get("type", "")
        action_class = self.dispatcher.get_action_class(action_type)
        schema = action_class.PARAMS_SCHEMA if action_class else []
        self._settings_panel.load_action(action_data, schema)

    def _on_flow_changed(self):
        """フローが変更された時の処理。"""
        self._current_flow_data["actions"] = self._flow_editor.get_flow_actions()

    def _on_params_changed(self, action_data: dict):
        """パラメータが変更された時の処理。"""
        node = self._flow_editor.get_selected_node()
        if node:
            node.update_from_data()

    def _run_flow(self):
        """フローを実行する。"""
        if self.engine.is_running():
            return

        # コマンド実行の警告
        actions = self._flow_editor.get_flow_actions()
        has_command = any(a.get("type") == "command.run" for a in actions)
        if has_command and not self._command_warning_shown:
            reply = QMessageBox.warning(
                self, "コマンド実行の警告",
                "このフローにはコマンド実行アクションが含まれています。\n"
                "信頼できるフローのみ実行してください。\n\n"
                "実行しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            self._command_warning_shown = True

        # フローデータを更新
        self._current_flow_data["actions"] = self._flow_editor.get_flow_actions()

        if not self._current_flow_data.get("actions"):
            QMessageBox.information(self, "情報", "フローにアクションがありません。")
            return

        # ステータスリセット
        self._flow_editor.reset_all_status()
        self._log_panel.clear()

        # ボタン状態更新
        self._run_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._status_bar.showMessage("実行中...")

        # スレッドで実行
        self._runner_thread = FlowRunnerThread(
            self.engine, copy.deepcopy(self._current_flow_data), self._runner_signals
        )
        self._runner_thread.start()

    def _stop_flow(self):
        """フローを停止する。"""
        self.engine.stop()
        self._status_bar.showMessage("停止中...")

    def _on_step_start(self, index: int, action: dict):
        """ステップ開始時の処理。"""
        action_id = action.get("id", "")
        self._flow_editor.set_node_status(action_id, ActionStatus.RUNNING)

    def _on_step_complete(self, index: int, action: dict, result):
        """ステップ完了時の処理。"""
        action_id = action.get("id", "")
        self._flow_editor.set_node_status(action_id, result.status)

    def _on_flow_complete(self, success: bool, log_path: str):
        """フロー完了時の処理。"""
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        if success:
            self._status_bar.showMessage(f"実行完了 - ログ: {log_path}")
        else:
            self._status_bar.showMessage(f"実行失敗 - ログ: {log_path}")

    def _show_flows_folder(self):
        """フローフォルダをエクスプローラーで開く。"""
        path = str(self.engine.flows_dir)
        os.makedirs(path, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(path)
        else:
            import subprocess
            subprocess.Popen(["xdg-open", path])

    def _show_logs_folder(self):
        """ログフォルダをエクスプローラーで開く。"""
        path = str(self.engine.logs_dir)
        os.makedirs(path, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(path)
        else:
            import subprocess
            subprocess.Popen(["xdg-open", path])

    def closeEvent(self, event):
        """ウィンドウを閉じる時の処理。"""
        if self.engine.is_running():
            reply = QMessageBox.question(
                self, "確認",
                "フローが実行中です。停止して終了しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.engine.stop()
                if self._runner_thread:
                    self._runner_thread.wait(3000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
