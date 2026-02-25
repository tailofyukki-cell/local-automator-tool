# プロジェクトアーキテクチャ

## 1. 概要

本ドキュメントは、完全ローカル動作のWindows専用自動化ツール「Local Automator」のアーキテクチャを定義する。

## 2. プロジェクト構造

```
local_automator/
├── dist/                # ビルドされた.exeファイル
├── docs/                # ドキュメント
│   └── architecture.md
├── samples/             # サンプルフローのJSONファイル
├── src/                 # ソースコード
│   ├── actions/         # 自動化アクションモジュール
│   ├── core/            # 実行エンジン、変数管理などコア機能
│   ├── gui/             # GUIコンポーネント
│   ├── triggers/        # トリガーモジュール
│   ├── utils/           # ユーティリティ
│   └── main.py          # アプリケーションのエントリポイント
├── build.spec           # PyInstallerビルド設定
└── README.md            # プロジェクトのREADME
```

## 3. フローJSON仕様

フローは以下のJSON形式で `/flows` フォルダに保存される。

```json
{
  "name": "フロー名",
  "description": "フローの説明",
  "actions": [
    {
      "id": "ユニークなID",
      "type": "アクションの種類 (例: command.run)",
      "name": "アクションの表示名",
      "params": {
        // アクション固有のパラメータ
      },
      "enabled": true // アクションの有効/無効フラグ
    }
    // ... 他のアクション
  ]
}
```

### 3.1. アクションの共通構造

- **id**: 各アクションを一意に識別するためのUUID。
- **type**: `category.action` の形式（例: `file.copy`, `command.run`）。
- **name**: GUIに表示されるユーザー定義のアクション名。
- **params**: アクションの実行に必要なパラメータのオブジェクト。
- **enabled**: このアクションが実行時に有効かどうかを示すブール値。

## 4. コアコンポーネント

### 4.1. 実行エンジン (`src/core/engine.py`)

- フローJSONを読み込み、`actions` 配列を上から順に実行する。
- 各アクションの実行前に、パラメータ内の `{{...}}` 形式の変数を展開する。
- アクションの実行結果（stdout, stderr, exit_codeなど）をコンテキストに保存し、後続のアクションから参照できるようにする (`{{step_id.output}}`)。
- `condition.if` アクションがfalseを返した場合、後続の `condition.endif` までのアクションをスキップする。
- 実行ログを生成し、`/logs` フォルダに保存する。

### 4.2. 変数管理 (`src/core/context.py`)

- フロー実行中の変数を管理する。
- グローバル変数と、各アクションの実行結果を保持する。
- テンプレート展開機能 (`{{var}}`, `{{step_id.stdout}}`) を提供する。

### 4.3. アクションディスパッチャ (`src/core/dispatcher.py`)

- アクションの `type` 文字列に基づいて、`src/actions` ディレクトリから対応するアクションモジュールを動的にロードして実行する。

## 5. GUI (`src/gui/`)

- **`main_window.py`**: アプリケーションのメインウィンドウ。左にアクション一覧、中央にフローエディタ、右に設定パネルを配置。
- **`flow_editor.py`**: ドラッグ＆ドロップでアクションを並べ替えられるフローの表示・編集エリア。
- **`node_widget.py`**: フローエディタ内の各アクションを表すUIコンポーネント。
- **`settings_panel.py`**: 選択されたアクションのパラメータを編集するためのUI。

## 6. 技術スタック

- **言語**: Python 3.11+
- **GUIフレームワーク**: PySide6
- **ビルドツール**: PyInstaller (`--onefile` モード)
