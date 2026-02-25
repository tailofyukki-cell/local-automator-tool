"""
トリガーアクションモジュール
フロー内でトリガーを設定するアクションを提供する。
（実際のトリガー管理はTriggerManagerが担当）
"""
from typing import Any, Dict

from src.core.action_base import ActionBase, ActionResult, ActionStatus


class ScheduleTriggerAction(ActionBase):
    ACTION_TYPE = "trigger.schedule"
    DISPLAY_NAME = "スケジュール実行"
    DESCRIPTION = "フローを定期的またはスケジュールに従って実行するトリガーを設定します。"
    CATEGORY = "トリガー"
    PARAMS_SCHEMA = [
        {"name": "schedule_type", "label": "スケジュール種別", "type": "select",
         "options": ["interval", "daily"],
         "default": "interval", "required": True,
         "description": "interval: 一定間隔, daily: 毎日指定時刻"},
        {"name": "interval_seconds", "label": "実行間隔（秒）", "type": "number", "default": "3600", "required": False,
         "description": "interval選択時: 実行間隔（秒）"},
        {"name": "daily_time", "label": "実行時刻", "type": "string", "default": "09:00", "required": False,
         "description": "daily選択時: 実行時刻（HH:MM形式）"},
        {"name": "note", "label": "メモ", "type": "string", "default": "", "required": False,
         "description": "このトリガーの説明メモ"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        schedule_type = params.get("schedule_type", "interval")
        interval = params.get("interval_seconds", "3600")
        daily_time = params.get("daily_time", "09:00")
        return ActionResult(
            status=ActionStatus.SUCCESS,
            output=f"スケジュールトリガー設定: {schedule_type} / {interval}秒 / {daily_time}",
            data={"schedule_type": schedule_type, "interval_seconds": interval, "daily_time": daily_time},
        )


class FolderWatchTriggerAction(ActionBase):
    ACTION_TYPE = "trigger.folder_watch"
    DISPLAY_NAME = "フォルダ監視"
    DESCRIPTION = "指定フォルダに新しいファイルが追加された時にフローを実行するトリガーを設定します。"
    CATEGORY = "トリガー"
    PARAMS_SCHEMA = [
        {"name": "watch_folder", "label": "監視フォルダ", "type": "string", "default": "", "required": True,
         "description": "監視するフォルダのパス"},
        {"name": "file_pattern", "label": "ファイルパターン", "type": "string", "default": "*", "required": False,
         "description": "監視するファイルのglobパターン（例: *.csv）"},
        {"name": "new_file_var", "label": "新規ファイル変数名", "type": "string", "default": "new_file", "required": False,
         "description": "新規ファイルのパスを保存する変数名"},
        {"name": "note", "label": "メモ", "type": "string", "default": "", "required": False,
         "description": "このトリガーの説明メモ"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        watch_folder = params.get("watch_folder", "")
        file_pattern = params.get("file_pattern", "*")
        new_file_var = params.get("new_file_var", "new_file")
        # コンテキストから新規ファイルパスを取得（トリガー発火時に設定済みの場合）
        new_file = context.get_variable("__trigger_new_file__", "")
        if new_file:
            context.set_variable(new_file_var, new_file)
        return ActionResult(
            status=ActionStatus.SUCCESS,
            output=f"フォルダ監視トリガー: {watch_folder} / パターン: {file_pattern}",
            data={"watch_folder": watch_folder, "file_pattern": file_pattern},
        )
