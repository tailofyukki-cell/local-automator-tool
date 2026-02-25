"""
ファイル操作アクションモジュール
フォルダ作成/削除、ファイルのコピー/移動/削除/リネーム、
テキスト読み書きなどのアクションを提供する。
"""
import glob
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict

from src.core.action_base import ActionBase, ActionResult, ActionStatus


class CreateFolderAction(ActionBase):
    ACTION_TYPE = "file.create_folder"
    DISPLAY_NAME = "フォルダ作成"
    DESCRIPTION = "指定したパスにフォルダを作成します。"
    CATEGORY = "ファイル操作"
    PARAMS_SCHEMA = [
        {"name": "path", "label": "フォルダパス", "type": "string", "default": "", "required": True,
         "description": "作成するフォルダのパス"},
        {"name": "exist_ok", "label": "既存でもエラーにしない", "type": "bool", "default": True, "required": False,
         "description": "フォルダが既に存在する場合にエラーにしない"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        path = params.get("path", "").strip()
        exist_ok = str(params.get("exist_ok", "true")).lower() not in ("false", "0", "no")
        if not path:
            return ActionResult(status=ActionStatus.FAILED, error_message="パスが指定されていません。")
        try:
            Path(path).mkdir(parents=True, exist_ok=exist_ok)
            return ActionResult(status=ActionStatus.SUCCESS, output=f"フォルダを作成しました: {path}")
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=str(e))


class DeleteFolderAction(ActionBase):
    ACTION_TYPE = "file.delete_folder"
    DISPLAY_NAME = "フォルダ削除"
    DESCRIPTION = "指定したフォルダを削除します（中身ごと削除）。"
    CATEGORY = "ファイル操作"
    PARAMS_SCHEMA = [
        {"name": "path", "label": "フォルダパス", "type": "string", "default": "", "required": True,
         "description": "削除するフォルダのパス"},
        {"name": "ignore_errors", "label": "エラーを無視", "type": "bool", "default": False, "required": False,
         "description": "削除中のエラーを無視する"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        path = params.get("path", "").strip()
        ignore_errors = str(params.get("ignore_errors", "false")).lower() in ("true", "1", "yes")
        if not path:
            return ActionResult(status=ActionStatus.FAILED, error_message="パスが指定されていません。")
        try:
            shutil.rmtree(path, ignore_errors=ignore_errors)
            return ActionResult(status=ActionStatus.SUCCESS, output=f"フォルダを削除しました: {path}")
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=str(e))


class CopyFileAction(ActionBase):
    ACTION_TYPE = "file.copy"
    DISPLAY_NAME = "ファイルコピー"
    DESCRIPTION = "ファイルを指定した場所にコピーします。"
    CATEGORY = "ファイル操作"
    PARAMS_SCHEMA = [
        {"name": "src", "label": "コピー元パス", "type": "string", "default": "", "required": True,
         "description": "コピー元のファイルパス"},
        {"name": "dst", "label": "コピー先パス", "type": "string", "default": "", "required": True,
         "description": "コピー先のファイルパスまたはフォルダパス"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        src = params.get("src", "").strip()
        dst = params.get("dst", "").strip()
        if not src or not dst:
            return ActionResult(status=ActionStatus.FAILED, error_message="コピー元またはコピー先が指定されていません。")
        try:
            shutil.copy2(src, dst)
            return ActionResult(status=ActionStatus.SUCCESS, output=f"コピーしました: {src} -> {dst}")
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=str(e))


class MoveFileAction(ActionBase):
    ACTION_TYPE = "file.move"
    DISPLAY_NAME = "ファイル移動"
    DESCRIPTION = "ファイルを指定した場所に移動します。"
    CATEGORY = "ファイル操作"
    PARAMS_SCHEMA = [
        {"name": "src", "label": "移動元パス", "type": "string", "default": "", "required": True,
         "description": "移動元のファイルパス"},
        {"name": "dst", "label": "移動先パス", "type": "string", "default": "", "required": True,
         "description": "移動先のファイルパスまたはフォルダパス"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        src = params.get("src", "").strip()
        dst = params.get("dst", "").strip()
        if not src or not dst:
            return ActionResult(status=ActionStatus.FAILED, error_message="移動元または移動先が指定されていません。")
        try:
            shutil.move(src, dst)
            return ActionResult(status=ActionStatus.SUCCESS, output=f"移動しました: {src} -> {dst}")
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=str(e))


class DeleteFileAction(ActionBase):
    ACTION_TYPE = "file.delete"
    DISPLAY_NAME = "ファイル削除"
    DESCRIPTION = "指定したファイルを削除します。"
    CATEGORY = "ファイル操作"
    PARAMS_SCHEMA = [
        {"name": "path", "label": "ファイルパス", "type": "string", "default": "", "required": True,
         "description": "削除するファイルのパス"},
        {"name": "missing_ok", "label": "存在しなくてもエラーにしない", "type": "bool", "default": False, "required": False,
         "description": "ファイルが存在しない場合にエラーにしない"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        path = params.get("path", "").strip()
        missing_ok = str(params.get("missing_ok", "false")).lower() in ("true", "1", "yes")
        if not path:
            return ActionResult(status=ActionStatus.FAILED, error_message="パスが指定されていません。")
        try:
            p = Path(path)
            if not p.exists():
                if missing_ok:
                    return ActionResult(status=ActionStatus.SUCCESS, output=f"ファイルが存在しません（スキップ）: {path}")
                else:
                    return ActionResult(status=ActionStatus.FAILED, error_message=f"ファイルが存在しません: {path}")
            p.unlink()
            return ActionResult(status=ActionStatus.SUCCESS, output=f"削除しました: {path}")
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=str(e))


class RenameFileAction(ActionBase):
    ACTION_TYPE = "file.rename"
    DISPLAY_NAME = "ファイルリネーム"
    DESCRIPTION = "ファイルまたはフォルダの名前を変更します。"
    CATEGORY = "ファイル操作"
    PARAMS_SCHEMA = [
        {"name": "src", "label": "元のパス", "type": "string", "default": "", "required": True,
         "description": "リネーム前のファイル/フォルダパス"},
        {"name": "dst", "label": "新しいパス", "type": "string", "default": "", "required": True,
         "description": "リネーム後のファイル/フォルダパス"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        src = params.get("src", "").strip()
        dst = params.get("dst", "").strip()
        if not src or not dst:
            return ActionResult(status=ActionStatus.FAILED, error_message="元のパスまたは新しいパスが指定されていません。")
        try:
            Path(src).rename(dst)
            return ActionResult(status=ActionStatus.SUCCESS, output=f"リネームしました: {src} -> {dst}")
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=str(e))


class ListFilesAction(ActionBase):
    ACTION_TYPE = "file.list"
    DISPLAY_NAME = "ファイル一覧取得"
    DESCRIPTION = "フォルダ内のファイル一覧を取得して変数に保存します。"
    CATEGORY = "ファイル操作"
    PARAMS_SCHEMA = [
        {"name": "folder", "label": "フォルダパス", "type": "string", "default": "", "required": True,
         "description": "一覧を取得するフォルダのパス"},
        {"name": "pattern", "label": "ファイルパターン", "type": "string", "default": "*", "required": False,
         "description": "ファイル名のglobパターン（例: *.txt）"},
        {"name": "var_name", "label": "変数名", "type": "string", "default": "file_list", "required": False,
         "description": "結果を保存する変数名"},
        {"name": "recursive", "label": "サブフォルダも検索", "type": "bool", "default": False, "required": False,
         "description": "サブフォルダも再帰的に検索する"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        folder = params.get("folder", "").strip()
        pattern = params.get("pattern", "*").strip() or "*"
        var_name = params.get("var_name", "file_list").strip() or "file_list"
        recursive = str(params.get("recursive", "false")).lower() in ("true", "1", "yes")
        if not folder:
            return ActionResult(status=ActionStatus.FAILED, error_message="フォルダパスが指定されていません。")
        try:
            search_pattern = os.path.join(folder, "**", pattern) if recursive else os.path.join(folder, pattern)
            files = glob.glob(search_pattern, recursive=recursive)
            files_str = "\n".join(files)
            context.set_variable(var_name, files_str)
            context.set_variable(f"{var_name}_count", str(len(files)))
            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"{len(files)}件のファイルを取得しました",
                data={"files": files, "count": len(files)},
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=str(e))


class ReadTextAction(ActionBase):
    ACTION_TYPE = "file.read_text"
    DISPLAY_NAME = "テキスト読み込み"
    DESCRIPTION = "テキストファイルを読み込んで変数に保存します。"
    CATEGORY = "ファイル操作"
    PARAMS_SCHEMA = [
        {"name": "path", "label": "ファイルパス", "type": "string", "default": "", "required": True,
         "description": "読み込むファイルのパス"},
        {"name": "var_name", "label": "変数名", "type": "string", "default": "file_content", "required": False,
         "description": "読み込んだ内容を保存する変数名"},
        {"name": "encoding", "label": "エンコーディング", "type": "string", "default": "utf-8", "required": False,
         "description": "ファイルのエンコーディング（例: utf-8, shift_jis）"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        path = params.get("path", "").strip()
        var_name = params.get("var_name", "file_content").strip() or "file_content"
        encoding = params.get("encoding", "utf-8").strip() or "utf-8"
        if not path:
            return ActionResult(status=ActionStatus.FAILED, error_message="ファイルパスが指定されていません。")
        try:
            with open(path, "r", encoding=encoding) as f:
                content = f.read()
            context.set_variable(var_name, content)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"ファイルを読み込みました: {path} ({len(content)}文字)",
                data={"content": content},
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=str(e))


class WriteTextAction(ActionBase):
    ACTION_TYPE = "file.write_text"
    DISPLAY_NAME = "テキスト上書き"
    DESCRIPTION = "テキストファイルに内容を上書き保存します。"
    CATEGORY = "ファイル操作"
    PARAMS_SCHEMA = [
        {"name": "path", "label": "ファイルパス", "type": "string", "default": "", "required": True,
         "description": "書き込むファイルのパス"},
        {"name": "content", "label": "内容", "type": "multiline", "default": "", "required": True,
         "description": "書き込む内容（{{変数名}}でテンプレート展開可能）"},
        {"name": "encoding", "label": "エンコーディング", "type": "string", "default": "utf-8", "required": False,
         "description": "ファイルのエンコーディング"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        path = params.get("path", "").strip()
        content = params.get("content", "")
        encoding = params.get("encoding", "utf-8").strip() or "utf-8"
        if not path:
            return ActionResult(status=ActionStatus.FAILED, error_message="ファイルパスが指定されていません。")
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding=encoding) as f:
                f.write(content)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"ファイルに書き込みました: {path} ({len(content)}文字)",
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=str(e))


class AppendTextAction(ActionBase):
    ACTION_TYPE = "file.append_text"
    DISPLAY_NAME = "テキスト追記"
    DESCRIPTION = "テキストファイルに内容を追記します。"
    CATEGORY = "ファイル操作"
    PARAMS_SCHEMA = [
        {"name": "path", "label": "ファイルパス", "type": "string", "default": "", "required": True,
         "description": "追記するファイルのパス"},
        {"name": "content", "label": "追記内容", "type": "multiline", "default": "", "required": True,
         "description": "追記する内容（{{変数名}}でテンプレート展開可能）"},
        {"name": "newline", "label": "前に改行を追加", "type": "bool", "default": True, "required": False,
         "description": "追記前に改行を挿入する"},
        {"name": "encoding", "label": "エンコーディング", "type": "string", "default": "utf-8", "required": False,
         "description": "ファイルのエンコーディング"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        path = params.get("path", "").strip()
        content = params.get("content", "")
        newline = str(params.get("newline", "true")).lower() not in ("false", "0", "no")
        encoding = params.get("encoding", "utf-8").strip() or "utf-8"
        if not path:
            return ActionResult(status=ActionStatus.FAILED, error_message="ファイルパスが指定されていません。")
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding=encoding) as f:
                if newline and Path(path).exists() and Path(path).stat().st_size > 0:
                    f.write("\n")
                f.write(content)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"ファイルに追記しました: {path} ({len(content)}文字)",
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=str(e))
