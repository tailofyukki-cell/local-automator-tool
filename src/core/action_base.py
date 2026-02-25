"""
アクション基底クラスモジュール
全アクションはこのクラスを継承して実装する。
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ActionStatus(Enum):
    """アクションの実行状態。"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ActionResult:
    """アクションの実行結果を格納するデータクラス。"""
    status: ActionStatus = ActionStatus.PENDING
    output: str = ""
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    error_message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換する（コンテキストへの保存用）。"""
        return {
            "status": self.status.value,
            "output": self.output,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "error_message": self.error_message,
            **self.data,
        }


class ActionBase:
    """
    全アクションの基底クラス。
    サブクラスは `execute` メソッドを実装する必要がある。
    """

    # アクションの種類を示す文字列 (例: "file.copy")
    ACTION_TYPE: str = ""
    # GUIに表示されるアクション名
    DISPLAY_NAME: str = ""
    # アクションの説明
    DESCRIPTION: str = ""
    # アクションが属するカテゴリ
    CATEGORY: str = ""
    # パラメータの定義リスト
    # 各要素は {"name": str, "label": str, "type": str, "default": Any, "required": bool, "description": str}
    PARAMS_SCHEMA: list = []

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        """
        アクションを実行する。サブクラスでオーバーライドする。

        Args:
            params: テンプレート展開済みのパラメータ辞書。
            context: ExecutionContextのインスタンス。

        Returns:
            ActionResult: 実行結果。
        """
        raise NotImplementedError(
            f"アクション '{self.ACTION_TYPE}' の execute メソッドが実装されていません。"
        )

    def get_default_params(self) -> Dict[str, Any]:
        """デフォルトパラメータを返す。"""
        return {
            schema["name"]: schema.get("default", "")
            for schema in self.PARAMS_SCHEMA
        }
