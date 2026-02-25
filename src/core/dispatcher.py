"""
アクションディスパッチャーモジュール
アクションタイプ文字列に基づいて対応するアクションクラスを管理・実行する。
"""
from typing import Dict, List, Optional, Type

from src.core.action_base import ActionBase, ActionResult, ActionStatus
from src.core.context import ExecutionContext


class ActionDispatcher:
    """アクションの登録と実行を管理するクラス。"""

    def __init__(self):
        self._registry: Dict[str, Type[ActionBase]] = {}
        self._register_all_actions()

    def _register_all_actions(self):
        """全アクションモジュールをインポートして登録する。"""
        # ファイル操作アクション
        from src.actions.file_actions import (
            CreateFolderAction,
            DeleteFolderAction,
            CopyFileAction,
            MoveFileAction,
            DeleteFileAction,
            RenameFileAction,
            ListFilesAction,
            ReadTextAction,
            WriteTextAction,
            AppendTextAction,
        )
        # コマンド実行アクション
        from src.actions.command_actions import RunCommandAction

        # 変数処理アクション
        from src.actions.variable_actions import (
            SetVariableAction,
            StringConcatAction,
            StringReplaceAction,
            GetDateAction,
            MathCalcAction,
        )

        # 条件分岐アクション
        from src.actions.condition_actions import (
            IfConditionAction,
            EndIfAction,
        )

        # トリガーアクション
        from src.actions.trigger_actions import (
            ScheduleTriggerAction,
            FolderWatchTriggerAction,
        )

        # 全アクションをリストアップして登録
        all_actions = [
            CreateFolderAction,
            DeleteFolderAction,
            CopyFileAction,
            MoveFileAction,
            DeleteFileAction,
            RenameFileAction,
            ListFilesAction,
            ReadTextAction,
            WriteTextAction,
            AppendTextAction,
            RunCommandAction,
            SetVariableAction,
            StringConcatAction,
            StringReplaceAction,
            GetDateAction,
            MathCalcAction,
            IfConditionAction,
            EndIfAction,
            ScheduleTriggerAction,
            FolderWatchTriggerAction,
        ]

        for action_class in all_actions:
            self.register(action_class)

    def register(self, action_class: Type[ActionBase]):
        """アクションクラスを登録する。"""
        if not action_class.ACTION_TYPE:
            raise ValueError(f"アクションクラス {action_class.__name__} に ACTION_TYPE が設定されていません。")
        self._registry[action_class.ACTION_TYPE] = action_class

    def get_action_class(self, action_type: str) -> Optional[Type[ActionBase]]:
        """アクションタイプに対応するクラスを返す。"""
        return self._registry.get(action_type)

    def execute(
        self, action_type: str, params: Dict, context: ExecutionContext
    ) -> ActionResult:
        """アクションを実行する。"""
        action_class = self.get_action_class(action_type)
        if action_class is None:
            result = ActionResult(
                status=ActionStatus.FAILED,
                error_message=f"不明なアクションタイプ: '{action_type}'",
            )
            return result

        action_instance = action_class()
        # パラメータのテンプレート展開
        expanded_params = context.expand_params(params)
        return action_instance.execute(expanded_params, context)

    def get_all_action_classes(self) -> List[Type[ActionBase]]:
        """登録されている全アクションクラスのリストを返す。"""
        return list(self._registry.values())

    def get_categories(self) -> Dict[str, List[Type[ActionBase]]]:
        """カテゴリ別にアクションを分類して返す。"""
        categories: Dict[str, List[Type[ActionBase]]] = {}
        for action_class in self._registry.values():
            cat = action_class.CATEGORY or "その他"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(action_class)
        return categories
