"""
変数処理アクションモジュール
変数の作成/更新、文字列操作、日付取得、数値計算などを提供する。
"""
import math
import re
from datetime import datetime
from typing import Any, Dict

from src.core.action_base import ActionBase, ActionResult, ActionStatus


class SetVariableAction(ActionBase):
    ACTION_TYPE = "variable.set"
    DISPLAY_NAME = "変数を設定"
    DESCRIPTION = "変数を作成または更新します。"
    CATEGORY = "変数処理"
    PARAMS_SCHEMA = [
        {"name": "name", "label": "変数名", "type": "string", "default": "", "required": True,
         "description": "設定する変数の名前"},
        {"name": "value", "label": "値", "type": "string", "default": "", "required": True,
         "description": "設定する値（{{変数名}}でテンプレート展開可能）"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        name = params.get("name", "").strip()
        value = params.get("value", "")
        if not name:
            return ActionResult(status=ActionStatus.FAILED, error_message="変数名が指定されていません。")
        context.set_variable(name, value)
        return ActionResult(
            status=ActionStatus.SUCCESS,
            output=f"変数を設定しました: {name} = {str(value)[:100]}",
            data={"var_name": name, "var_value": value},
        )


class StringConcatAction(ActionBase):
    ACTION_TYPE = "variable.string_concat"
    DISPLAY_NAME = "文字列結合"
    DESCRIPTION = "複数の文字列を結合して変数に保存します。"
    CATEGORY = "変数処理"
    PARAMS_SCHEMA = [
        {"name": "parts", "label": "結合する文字列（改行区切り）", "type": "multiline", "default": "", "required": True,
         "description": "結合する文字列を改行で区切って入力（各行に{{変数名}}使用可）"},
        {"name": "separator", "label": "区切り文字", "type": "string", "default": "", "required": False,
         "description": "各文字列の間に挿入する区切り文字"},
        {"name": "var_name", "label": "変数名", "type": "string", "default": "result", "required": True,
         "description": "結果を保存する変数名"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        parts_str = params.get("parts", "")
        separator = params.get("separator", "")
        var_name = params.get("var_name", "result").strip() or "result"
        parts = [p for p in parts_str.split("\n") if p]
        result = separator.join(parts)
        context.set_variable(var_name, result)
        return ActionResult(
            status=ActionStatus.SUCCESS,
            output=f"文字列を結合しました: {var_name} = {result[:100]}",
            data={"var_name": var_name, "var_value": result},
        )


class StringReplaceAction(ActionBase):
    ACTION_TYPE = "variable.string_replace"
    DISPLAY_NAME = "文字列置換"
    DESCRIPTION = "文字列内の特定のテキストを置換して変数に保存します。"
    CATEGORY = "変数処理"
    PARAMS_SCHEMA = [
        {"name": "source", "label": "元の文字列", "type": "string", "default": "", "required": True,
         "description": "置換対象の文字列（{{変数名}}使用可）"},
        {"name": "find", "label": "検索文字列", "type": "string", "default": "", "required": True,
         "description": "検索する文字列"},
        {"name": "replace", "label": "置換後文字列", "type": "string", "default": "", "required": False,
         "description": "置換後の文字列"},
        {"name": "var_name", "label": "変数名", "type": "string", "default": "result", "required": True,
         "description": "結果を保存する変数名"},
        {"name": "use_regex", "label": "正規表現を使用", "type": "bool", "default": False, "required": False,
         "description": "検索文字列を正規表現として扱う"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        source = params.get("source", "")
        find = params.get("find", "")
        replace = params.get("replace", "")
        var_name = params.get("var_name", "result").strip() or "result"
        use_regex = str(params.get("use_regex", "false")).lower() in ("true", "1", "yes")
        try:
            if use_regex:
                result = re.sub(find, replace, source)
            else:
                result = source.replace(find, replace)
            context.set_variable(var_name, result)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"文字列を置換しました: {var_name} = {result[:100]}",
                data={"var_name": var_name, "var_value": result},
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=str(e))


class GetDateAction(ActionBase):
    ACTION_TYPE = "variable.get_date"
    DISPLAY_NAME = "日付取得"
    DESCRIPTION = "現在の日付/時刻を指定のフォーマットで変数に保存します。"
    CATEGORY = "変数処理"
    PARAMS_SCHEMA = [
        {"name": "format", "label": "フォーマット", "type": "string", "default": "%Y-%m-%d %H:%M:%S", "required": False,
         "description": "日付フォーマット（例: %Y-%m-%d, %H:%M:%S）"},
        {"name": "var_name", "label": "変数名", "type": "string", "default": "current_date", "required": True,
         "description": "結果を保存する変数名"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        fmt = params.get("format", "%Y-%m-%d %H:%M:%S").strip() or "%Y-%m-%d %H:%M:%S"
        var_name = params.get("var_name", "current_date").strip() or "current_date"
        try:
            now = datetime.now()
            result = now.strftime(fmt)
            context.set_variable(var_name, result)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"日付を取得しました: {var_name} = {result}",
                data={"var_name": var_name, "var_value": result},
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=str(e))


class MathCalcAction(ActionBase):
    ACTION_TYPE = "variable.math_calc"
    DISPLAY_NAME = "数値計算"
    DESCRIPTION = "数式を計算して変数に保存します。"
    CATEGORY = "変数処理"
    PARAMS_SCHEMA = [
        {"name": "expression", "label": "数式", "type": "string", "default": "", "required": True,
         "description": "計算する数式（例: 1 + 2 * 3, {{count}} + 1）"},
        {"name": "var_name", "label": "変数名", "type": "string", "default": "calc_result", "required": True,
         "description": "結果を保存する変数名"},
        {"name": "decimal_places", "label": "小数点以下桁数", "type": "number", "default": "-1", "required": False,
         "description": "結果の小数点以下桁数（-1で自動）"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        expression = params.get("expression", "").strip()
        var_name = params.get("var_name", "calc_result").strip() or "calc_result"
        decimal_places_str = str(params.get("decimal_places", "-1")).strip()

        if not expression:
            return ActionResult(status=ActionStatus.FAILED, error_message="数式が指定されていません。")

        try:
            decimal_places = int(decimal_places_str)
        except ValueError:
            decimal_places = -1

        # 安全な数式評価（限定的な関数のみ許可）
        allowed_names = {
            "abs": abs, "round": round, "min": min, "max": max,
            "int": int, "float": float, "pow": pow,
            "sqrt": math.sqrt, "floor": math.floor, "ceil": math.ceil,
            "pi": math.pi, "e": math.e,
        }
        try:
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            if decimal_places >= 0:
                result = round(float(result), decimal_places)
                if decimal_places == 0:
                    result = int(result)
            result_str = str(result)
            context.set_variable(var_name, result_str)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"計算しました: {expression} = {result_str}",
                data={"var_name": var_name, "var_value": result_str},
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"数式評価エラー: {e}")
