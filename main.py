"""AIWolf NLP LLM Judge エントリーポイント."""

import logging
from src.cli import main, setup_logging

if __name__ == "__main__":
    setup_logging()
    try:
        main()
    except KeyboardInterrupt:
        logging.info("処理が中断されました")
    except Exception as e:
        logging.error(f"エラーが発生しました: {e}", exc_info=True)
        exit(1)
