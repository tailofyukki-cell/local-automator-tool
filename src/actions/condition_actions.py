"""
条件分岐アクションモジュール
IF条件とENDIFアクションを提供する。
"""
from typing import Any, Dict

from src.core.action_base import ActionBase, ActionResult, ActionStatus


class IfConditionAction(ActionBase):
    ACTION_TYPE = "condition.if"
    DISPLAY_NAME = "IF 条件分岐"
    DESCRIPTION = "条件を評価し、falseの場合は次のENDIFまでのアクションをスキップします。"
    CATEGORY = "条件分岐"
    PARAMS_SCHEMA = [
        {"name": "left", "label": "左辺", "type": "string", "default": "", "required": True,
         "description": "比較する左辺の値（{{変数名}}使用可）"},
        {"name": "operator", "label": "演算子", "type": "select",
         "options": ["=", "!=", ">", "<", ">=", "<=", "contains", "not_contains", "starts_with", "ends_with",
                     "is_empty", "is_not_empty"],
         "default": "=", "required": True,
         "description": "比較演算子"},
        {"name": "right", "label": "右辺", "type": "string", "default": "", "required": False,
         "description": "比較する右辺の値（{{変数名}}使用可）"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        left = str(params.get("left", ""))
        operator = params.get("operator", "=").strip()
        right = str(params.get("right", ""))

        try:
            condition_met = self._evaluate(left, operator, right)
            status = ActionStatus.SUCCESS if condition_met else ActionStatus.FAILED
            return ActionResult(
                status=status,
                output=f"条件: '{left}' {operator} '{right}' -> {'TRUE' if condition_met else 'FALSE'}",
                data={"condition_met": condition_met},
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                error_message=f"条件評価エラー: {e}",
            )

    def _evaluate(self, left: str, operator: str, right: str) -> bool:
        """条件を評価する。"""
        if operator == "=":
            return left == right
        elif operator == "!=":
            return left != right
        elif operator == ">":
            try:
                return float(left) > float(right)
            except ValueError:
                return left > right
        elif operator == "<":
            try:
                return float(left) < float(right)
            except ValueError:
                return left < right
        elif operator == ">=":
            try:
                return float(left) >= float(right)
            except ValueError:
                return left >= right
        elif operator == "<=":
            try:
                return float(left) <= float(right)
            except ValueError:
                return left <= right
        elif operator == "contains":
            return right in left
        elif operator == "not_contains":
            return right not in left
        elif operator == "starts_with":
            return left.startswith(right)
        elif operator == "ends_with":
            return left.endswith(right)
        elif operator == "is_empty":
            return left.strip() == ""
        elif operator == "is_not_empty":
            return left.strip() != ""
        else:
            raise ValueError(f"不明な演算子: {operator}")


class EndIfAction(ActionBase):
    ACTION_TYPE = "condition.endif"
    DISPLAY_NAME = "END IF"
    DESCRIPTION = "IF条件分岐の終端を示します。"
    CATEGORY = "条件分岐"
    PARAMS_SCHEMA = []

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS, output="ENDIF")
