"""
トリガー管理モジュール
スケジュール実行とフォルダ監視トリガーを管理する。
"""
import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class ScheduleTrigger:
    """
    スケジュール実行トリガー。
    指定した間隔または時刻でフローを実行する。
    """

    def __init__(
        self,
        trigger_id: str,
        flow_path: str,
        schedule_type: str,  # "interval" or "daily"
        interval_seconds: int = 3600,
        daily_time: str = "09:00",  # HH:MM形式
        on_trigger: Optional[Callable[[str], None]] = None,
    ):
        self.trigger_id = trigger_id
        self.flow_path = flow_path
        self.schedule_type = schedule_type
        self.interval_seconds = interval_seconds
        self.daily_time = daily_time
        self.on_trigger = on_trigger
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_run: Optional[datetime] = None

    def start(self):
        """トリガーを開始する。"""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """トリガーを停止する。"""
        self._stop_event.set()

    def _run_loop(self):
        """トリガーのメインループ。"""
        while not self._stop_event.is_set():
            if self._should_trigger():
                self._last_run = datetime.now()
                if self.on_trigger:
                    self.on_trigger(self.flow_path)
            self._stop_event.wait(timeout=10)  # 10秒ごとにチェック

    def _should_trigger(self) -> bool:
        """トリガーを発火すべきかどうかを判定する。"""
        now = datetime.now()
        if self.schedule_type == "interval":
            if self._last_run is None:
                return True
            elapsed = (now - self._last_run).total_seconds()
            return elapsed >= self.interval_seconds
        elif self.schedule_type == "daily":
            try:
                target_hour, target_minute = map(int, self.daily_time.split(":"))
                if now.hour == target_hour and now.minute == target_minute:
                    if self._last_run is None or self._last_run.date() < now.date():
                        return True
            except ValueError:
                pass
        return False

    def to_dict(self) -> Dict:
        return {
            "trigger_id": self.trigger_id,
            "flow_path": self.flow_path,
            "schedule_type": self.schedule_type,
            "interval_seconds": self.interval_seconds,
            "daily_time": self.daily_time,
        }


class FolderWatchTrigger:
    """
    フォルダ監視トリガー。
    指定したフォルダに新しいファイルが追加された時にフローを実行する。
    """

    def __init__(
        self,
        trigger_id: str,
        flow_path: str,
        watch_folder: str,
        file_pattern: str = "*",
        on_trigger: Optional[Callable[[str, str], None]] = None,
    ):
        self.trigger_id = trigger_id
        self.flow_path = flow_path
        self.watch_folder = watch_folder
        self.file_pattern = file_pattern
        self.on_trigger = on_trigger
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._known_files: set = set()

    def start(self):
        """トリガーを開始する（既存ファイルを記録してから監視開始）。"""
        self._stop_event.clear()
        self._scan_existing()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """トリガーを停止する。"""
        self._stop_event.set()

    def _scan_existing(self):
        """既存のファイルを記録する。"""
        import glob
        folder = self.watch_folder
        pattern = os.path.join(folder, self.file_pattern)
        try:
            self._known_files = set(glob.glob(pattern))
        except Exception:
            self._known_files = set()

    def _run_loop(self):
        """フォルダ監視のメインループ。"""
        import glob
        while not self._stop_event.is_set():
            try:
                pattern = os.path.join(self.watch_folder, self.file_pattern)
                current_files = set(glob.glob(pattern))
                new_files = current_files - self._known_files
                for new_file in new_files:
                    self._known_files.add(new_file)
                    if self.on_trigger:
                        self.on_trigger(self.flow_path, new_file)
            except Exception:
                pass
            self._stop_event.wait(timeout=2)  # 2秒ごとにチェック

    def to_dict(self) -> Dict:
        return {
            "trigger_id": self.trigger_id,
            "flow_path": self.flow_path,
            "watch_folder": self.watch_folder,
            "file_pattern": self.file_pattern,
        }


class TriggerManager:
    """全トリガーを管理するクラス。"""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self._triggers: Dict[str, Any] = {}
        self._config_path = self.data_dir / "triggers.json"
        self._on_trigger_callback: Optional[Callable] = None

    def set_trigger_callback(self, callback: Callable):
        """トリガー発火時のコールバックを設定する。"""
        self._on_trigger_callback = callback

    def add_schedule_trigger(
        self,
        trigger_id: str,
        flow_path: str,
        schedule_type: str,
        interval_seconds: int = 3600,
        daily_time: str = "09:00",
    ) -> ScheduleTrigger:
        """スケジュールトリガーを追加する。"""
        trigger = ScheduleTrigger(
            trigger_id=trigger_id,
            flow_path=flow_path,
            schedule_type=schedule_type,
            interval_seconds=interval_seconds,
            daily_time=daily_time,
            on_trigger=self._on_schedule_trigger,
        )
        self._triggers[trigger_id] = trigger
        self._save_config()
        return trigger

    def add_folder_watch_trigger(
        self,
        trigger_id: str,
        flow_path: str,
        watch_folder: str,
        file_pattern: str = "*",
    ) -> FolderWatchTrigger:
        """フォルダ監視トリガーを追加する。"""
        trigger = FolderWatchTrigger(
            trigger_id=trigger_id,
            flow_path=flow_path,
            watch_folder=watch_folder,
            file_pattern=file_pattern,
            on_trigger=self._on_folder_trigger,
        )
        self._triggers[trigger_id] = trigger
        self._save_config()
        return trigger

    def remove_trigger(self, trigger_id: str):
        """トリガーを削除する。"""
        if trigger_id in self._triggers:
            self._triggers[trigger_id].stop()
            del self._triggers[trigger_id]
            self._save_config()

    def start_all(self):
        """全トリガーを開始する。"""
        for trigger in self._triggers.values():
            trigger.start()

    def stop_all(self):
        """全トリガーを停止する。"""
        for trigger in self._triggers.values():
            trigger.stop()

    def get_all_triggers(self) -> List[Dict]:
        """全トリガーの情報を返す。"""
        return [t.to_dict() for t in self._triggers.values()]

    def _on_schedule_trigger(self, flow_path: str):
        """スケジュールトリガー発火時の処理。"""
        if self._on_trigger_callback:
            self._on_trigger_callback("schedule", flow_path, {})

    def _on_folder_trigger(self, flow_path: str, new_file: str):
        """フォルダ監視トリガー発火時の処理。"""
        if self._on_trigger_callback:
            self._on_trigger_callback("folder_watch", flow_path, {"new_file": new_file})

    def _save_config(self):
        """トリガー設定をJSONに保存する。"""
        try:
            config = [t.to_dict() for t in self._triggers.values()]
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
