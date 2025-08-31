import logging
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from src.aiwolf_log.game_log import AIWolfGameLog
from src.utils.game_log_finder import find_all_game_logs


logger = logging.getLogger(__name__)


def process_all_games(
    input_dir: Path,
    output_dir: Path,
    config: dict[str, Any],
    max_workers: int | None = None,
) -> None:
    """すべてのゲームログを並列処理で評価

    Args:
        input_dir: 入力ディレクトリ
        output_dir: 出力ディレクトリ
        config: 設定辞書
        max_workers: 最大ワーカー数（Noneの場合はCPU数を使用）
    """
    max_workers = max_workers or mp.cpu_count()
    logger.info(f"Starting batch processing with {max_workers} workers")

    logger.info(f"Searching for game logs in: {input_dir}")
    game_logs = find_all_game_logs(input_dir)
    logger.info(f"Found {len(game_logs)} game logs")

    if not game_logs:
        logger.warning("No game logs found")
        return

    # 出力ディレクトリの作成
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Processing {len(game_logs)} games with {max_workers} workers")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []

        for game_log in game_logs:
            future = executor.submit(process_single_game, game_log, config, output_dir)
            futures.append((future, game_log.game_id))

        # 結果を収集
        completed = 0
        failed = 0

        for future, game_id in futures:
            try:
                result = future.result()
                if result:
                    completed += 1
                    logger.info(f"Completed processing: {game_id}")
                else:
                    failed += 1
                    logger.error(f"Failed processing: {game_id}")
            except Exception as e:
                failed += 1
                logger.error(f"Error processing {game_id}: {e}")

    logger.info(f"Batch processing completed. Success: {completed}, Failed: {failed}")


def process_single_game(
    game_log: AIWolfGameLog, config: dict[str, Any], output_dir: Path
) -> bool:
    """単一ゲームの処理（プロセス間で実行される関数）"""
    try:
        logger.info(f"Processing game: {game_log.game_id}")

        # TODO: 実際の評価処理を実装
        # 1. ゲーム形式の検出
        # game_info = GameDetector.detect_game_format(game_log.log_path, config)

        # 2. 評価設定の読み込み
        # evaluation_config = ConfigLoader.load_from_config(config)

        # 3. 評価実行
        # evaluator = SomeEvaluator(evaluation_config)
        # result = evaluator.evaluate(game_log, game_info)

        # 4. 結果の保存
        # output_path = output_dir / f"{game_log.game_id}_result.json"
        # result.save(output_path)

        # 仮実装：成功を返す
        return True

    except Exception as e:
        logger.error(f"Failed to process game {game_log.game_id}: {e}")
        return False
