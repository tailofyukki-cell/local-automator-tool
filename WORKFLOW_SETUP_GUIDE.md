# GitHub Actions ワークフロー追加手順

ソースコードはリポジトリにプッシュ済みです。  
以下の手順でワークフローファイルを追加すると、自動的に `.exe` のビルドが開始されます。

---

## 手順（PCブラウザから操作）

### 1. リポジトリを開く

https://github.com/tailofyukki-cell/local-automator-tool

### 2. 新しいファイルを作成する

- 「Add file」ボタン → 「Create new file」をクリック

### 3. ファイルパスを入力する

ファイル名の欄に以下を入力してください（スラッシュを入力するとフォルダが自動作成されます）：

```
.github/workflows/build.yml
```

### 4. ファイルの内容を貼り付ける

以下の内容をそのままコピーして貼り付けてください：

```yaml
name: Build Windows Executable

on:
  push:
    branches:
      - main

jobs:
  build:
    runs-on: windows-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install PySide6
          pip install pyinstaller

      - name: Build executable (onefile)
        run: |
          pyinstaller build.spec

      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: LocalAutomator-exe
          path: dist/LocalAutomator.exe
```

### 5. コミットする

- ページ下部の「Commit new file」ボタンをクリック

---

## ビルド完了後の手順

1. リポジトリの「Actions」タブを開く
2. 「Build Windows Executable」ワークフローをクリック
3. 最新の実行結果を開く
4. 「Artifacts」セクションの「LocalAutomator-exe」をダウンロード
5. zip を展開すると `LocalAutomator.exe` が取得できます

---

## ビルド所要時間

Windows環境でのビルドのため、**約5〜10分**かかります。
