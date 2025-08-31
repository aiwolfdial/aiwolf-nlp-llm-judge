import argparse
import logging
from pathlib import Path
import yaml

from src.processor import BatchProcessor


def setup_logging() -> None:
    """ロギングの設定."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def main() -> None:
    """メイン処理."""
    parser = argparse.ArgumentParser(description="")

    # 設定ファイルオプション
    parser.add_argument(
        "-c", "--config", type=Path, required=True, help="設定ファイルのパス"
    )

    # デバッグモードオプション
    parser.add_argument("--debug", action="store_true", help="デバッグモードで実行")

    args = parser.parse_args()

    # ロギング設定
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # 設定ファイルの検証
    if not args.config.is_file():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {args.config}")

    # 設定ファイルの読み込み
    try:
        with args.config.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logging.info(f"設定ファイルを読み込みました: {args.config}")
    except Exception as e:
        raise RuntimeError(f"設定ファイルの読み込みに失敗しました: {e}")

    # settings_pathを設定に追加
    config["settings_path"] = str(args.config)

    # バッチ処理の実行
    processor = BatchProcessor(config)
    result = processor.process_all_games()

    logging.info(
        f"処理完了 - 成功: {result.completed}/{result.total}, 成功率: {result.success_rate:.2%}"
    )


if __name__ == "__main__":
    setup_logging()
    try:
        main()
    except KeyboardInterrupt:
        logging.info("処理が中断されました")
    except Exception as e:
        logging.error(f"エラーが発生しました: {e}")
        exit(1)
