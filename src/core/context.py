"""
実行コンテキスト管理モジュール
フロー実行中の変数と各ステップの結果を管理し、テンプレート展開機能を提供する。
"""
import re
from datetime import datetime
from typing import Any, Dict, Optional


class ExecutionContext:
    """フロー実行中の変数と結果を管理するクラス。"""

    def __init__(self):
        self._variables: Dict[str, Any] = {}
        self._step_results: Dict[str, Dict[str, Any]] = {}
        self._initialize_builtin_vars()

    def _initialize_builtin_vars(self):
        """組み込み変数を初期化する。"""
        now = datetime.now()
        self._variables["now.date"] = now.strftime("%Y-%m-%d")
        self._variables["now.time"] = now.strftime("%H:%M:%S")
        self._variables["now.datetime"] = now.strftime("%Y-%m-%d %H:%M:%S")
        self._variables["now.year"] = str(now.year)
        self._variables["now.month"] = str(now.month).zfill(2)
        self._variables["now.day"] = str(now.day).zfill(2)
        self._variables["now.hour"] = str(now.hour).zfill(2)
        self._variables["now.minute"] = str(now.minute).zfill(2)
        self._variables["now.second"] = str(now.second).zfill(2)
        self._variables["now.timestamp"] = now.strftime("%Y%m%d_%H%M%S")

    def set_variable(self, name: str, value: Any):
        """変数を設定する。"""
        self._variables[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        """変数を取得する。"""
        return self._variables.get(name, default)

    def set_step_result(self, step_id: str, result: Dict[str, Any]):
        """ステップの実行結果を保存する。"""
        self._step_results[step_id] = result

    def get_step_result(self, step_id: str) -> Optional[Dict[str, Any]]:
        """ステップの実行結果を取得する。"""
        return self._step_results.get(step_id)

    def expand_template(self, text: str) -> str:
        """
        テンプレート文字列内の {{...}} を展開する。
        対応形式:
          {{varName}}           -> 変数の値
          {{step_id.stdout}}    -> ステップ結果のフィールド
          {{step_id.stderr}}    -> ステップ結果のフィールド
          {{step_id.exit_code}} -> ステップ結果のフィールド
          {{step_id.output}}    -> ステップ結果のフィールド
        """
        if not isinstance(text, str):
            return text

        def replacer(match: re.Match) -> str:
            key = match.group(1).strip()
            # まず変数辞書から検索
            if key in self._variables:
                return str(self._variables[key])
            # ドット区切りでステップ結果を検索 (例: step_id.stdout)
            if "." in key:
                parts = key.split(".", 1)
                step_id, field = parts[0], parts[1]
                if step_id in self._step_results:
                    result = self._step_results[step_id]
                    if field in result:
                        return str(result[field])
            # 展開できない場合はそのまま返す
            return match.group(0)

        return re.sub(r"\{\{([^}]+)\}\}", replacer, text)

    def expand_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """パラメータ辞書内の全文字列値にテンプレート展開を適用する。"""
        expanded = {}
        for key, value in params.items():
            if isinstance(value, str):
                expanded[key] = self.expand_template(value)
            elif isinstance(value, dict):
                expanded[key] = self.expand_params(value)
            elif isinstance(value, list):
                expanded[key] = [
                    self.expand_template(v) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                expanded[key] = value
        return expanded

    def get_all_variables(self) -> Dict[str, Any]:
        """全変数の辞書を返す（デバッグ用）。"""
        return dict(self._variables)
