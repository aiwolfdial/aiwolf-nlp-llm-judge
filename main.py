import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.cli import main, setup_logging

if __name__ == "__main__":
    setup_logging()
    try:
        main()
    except KeyboardInterrupt:
        import logging

        logging.info("処理が中断されました")
    except Exception as e:
        import logging

        logging.error(f"エラーが発生しました: {e}")
        exit(1)
