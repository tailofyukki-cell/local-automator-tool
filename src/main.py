"""
Local Automator - メインエントリポイント
Power Automate風の完全ローカル動作Windows専用自動化ツール
"""
import os
import sys


def get_base_dir() -> str:
    """
    exeが配置されているディレクトリを返す。
    PyInstallerでビルドされた場合は sys.executable のディレクトリ、
    開発時は main.py の2階層上のディレクトリを返す。
    """
    if getattr(sys, "frozen", False):
        # PyInstallerでビルドされた場合
        return os.path.dirname(sys.executable)
    else:
        # 開発時（src/main.py からの相対パス）
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    """アプリケーションのメイン関数。"""
    # PySide6のインポート
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont
    except ImportError as e:
        print(f"PySide6のインポートに失敗しました: {e}")
        print("pip install PySide6 を実行してください。")
        sys.exit(1)

    # src ディレクトリをパスに追加（開発時）
    src_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(src_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    base_dir = get_base_dir()

    # アプリケーション作成
    app = QApplication(sys.argv)
    app.setApplicationName("Local Automator")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("LocalAutomator")

    # High DPI対応
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    # デフォルトフォント設定
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # メインウィンドウ起動
    from src.gui.main_window import MainWindow
    window = MainWindow(base_dir)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
