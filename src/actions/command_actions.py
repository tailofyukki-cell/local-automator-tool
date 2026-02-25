"""
コマンド実行アクションモジュール
任意の.exe / bat / powershellを実行するアクションを提供する。
"""
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

from src.core.action_base import ActionBase, ActionResult, ActionStatus


class RunCommandAction(ActionBase):
    ACTION_TYPE = "command.run"
    DISPLAY_NAME = "コマンド実行"
    DESCRIPTION = "任意のコマンド（.exe / .bat / PowerShell）を実行します。"
    CATEGORY = "コマンド実行"
    PARAMS_SCHEMA = [
        {"name": "command", "label": "コマンド", "type": "string", "default": "", "required": True,
         "description": "実行するコマンド（{{変数名}}でテンプレート展開可能）"},
        {"name": "working_dir", "label": "作業ディレクトリ", "type": "string", "default": "", "required": False,
         "description": "コマンドを実行するディレクトリ（空の場合はカレントディレクトリ）"},
        {"name": "timeout", "label": "タイムアウト（秒）", "type": "number", "default": "60", "required": False,
         "description": "コマンドのタイムアウト秒数（0で無制限）"},
        {"name": "shell", "label": "シェル経由で実行", "type": "bool", "default": True, "required": False,
         "description": "シェル（cmd.exe）経由でコマンドを実行する"},
        {"name": "output_var", "label": "出力変数名", "type": "string", "default": "", "required": False,
         "description": "stdoutを保存する変数名（空の場合は保存しない）"},
        {"name": "encoding", "label": "出力エンコーディング", "type": "string", "default": "utf-8", "required": False,
         "description": "コマンド出力のエンコーディング（例: utf-8, cp932）"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        command = params.get("command", "").strip()
        working_dir = params.get("working_dir", "").strip() or None
        timeout_str = str(params.get("timeout", "60")).strip()
        use_shell = str(params.get("shell", "true")).lower() not in ("false", "0", "no")
        output_var = params.get("output_var", "").strip()
        encoding = params.get("encoding", "utf-8").strip() or "utf-8"

        if not command:
            return ActionResult(status=ActionStatus.FAILED, error_message="コマンドが指定されていません。")

        try:
            timeout = float(timeout_str) if timeout_str else 60.0
            timeout = None if timeout == 0 else timeout
        except ValueError:
            timeout = 60.0

        if working_dir and not Path(working_dir).exists():
            return ActionResult(
                status=ActionStatus.FAILED,
                error_message=f"作業ディレクトリが存在しません: {working_dir}",
            )

        try:
            proc = subprocess.run(
                command,
                shell=use_shell,
                cwd=working_dir,
                capture_output=True,
                timeout=timeout,
                encoding=encoding,
                errors="replace",
            )
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            exit_code = proc.returncode

            if output_var:
                context.set_variable(output_var, stdout.strip())

            status = ActionStatus.SUCCESS if exit_code == 0 else ActionStatus.FAILED
            output = f"exit code: {exit_code}"
            if stdout:
                output += f"\nstdout: {stdout[:200]}"

            return ActionResult(
                status=status,
                output=output,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                error_message=f"exit code: {exit_code}" if exit_code != 0 else "",
            )

        except subprocess.TimeoutExpired:
            return ActionResult(
                status=ActionStatus.FAILED,
                error_message=f"タイムアウトしました（{timeout}秒）",
            )
        except FileNotFoundError as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                error_message=f"コマンドが見つかりません: {e}",
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                error_message=f"コマンド実行エラー: {e}",
            )
