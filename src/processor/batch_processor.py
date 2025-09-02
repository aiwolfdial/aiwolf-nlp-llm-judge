"""バッチ処理を管理するクラス."""

import logging
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from src.aiwolf_log import AIWolfGameLog
from src.utils.game_log_finder import find_all_game_logs

from .config import ProcessingConfig
from .game_processor import GameProcessor
from .result import ProcessingResult

logger = logging.getLogger(__name__)


class BatchProcessor:
    """バッチ処理を管理するクラス

    このクラスは、複数のゲームログに対して並列処理を実行し、
    処理結果の統計情報を管理する責任を持ちます。
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """BatchProcessorを初期化

        Args:
            config: アプリケーション設定辞書
        """
        self.config = config
        self.processing_config = ProcessingConfig.from_config_dict(config)

    def process_all_games(self) -> ProcessingResult:
        """すべてのゲームログを並列処理

        Returns:
            処理結果統計
        """
        logger.info(
            f"Starting batch processing with {self.processing_config.max_workers} workers"
        )

        # ゲームログ検索
        game_logs = self._find_game_logs()
        if not game_logs:
            logger.warning("No game logs found")
            return ProcessingResult()

        # 出力ディレクトリ準備
        self.processing_config.output_dir.mkdir(parents=True, exist_ok=True)

        # 並列処理実行
        result = self._execute_parallel_processing(game_logs)

        # 結果ログ出力
        self._log_processing_summary(result)

        return result

    def _find_game_logs(self) -> list[AIWolfGameLog]:
        """ゲームログを検索

        Returns:
            発見されたゲームログのリスト
        """
        logger.info(f"Searching for game logs in: {self.processing_config.input_dir}")
        game_logs = find_all_game_logs(self.processing_config.input_dir)
        logger.info(f"Found {len(game_logs)} game logs")
        return game_logs

    def _execute_parallel_processing(
        self, game_logs: list[AIWolfGameLog]
    ) -> ProcessingResult:
        """並列処理を実行

        Args:
            game_logs: 処理対象のゲームログリスト

        Returns:
            処理結果統計
        """
        result = ProcessingResult(total=len(game_logs))

        with ProcessPoolExecutor(
            max_workers=self.processing_config.max_workers
        ) as executor:
            # タスク投入
            futures = [
                (
                    executor.submit(
                        self._process_single_game_worker,
                        game_log,
                        self.config,
                        self.processing_config.output_dir,
                    ),
                    game_log,
                )
                for game_log in game_logs
            ]

            # 結果収集
            for future, game_log in futures:
                try:
                    success = future.result()
                    if success:
                        result.completed += 1
                        logger.info(
                            f"{GameProcessor.SUCCESS_INDICATOR} Completed: {game_log.game_id}"
                        )
                    else:
                        result.failed += 1
                        logger.error(
                            f"{GameProcessor.FAILURE_INDICATOR} Failed: {game_log.game_id}"
                        )
                except Exception as e:
                    result.failed += 1
                    logger.error(
                        f"{GameProcessor.FAILURE_INDICATOR} Error processing {game_log.game_id}: {e}"
                    )

        return result

    def _log_processing_summary(self, result: ProcessingResult) -> None:
        """処理結果のサマリーをログ出力

        Args:
            result: 処理結果統計
        """
        logger.info(
            f"Batch processing completed - "
            f"Total: {result.total}, Success: {result.completed}, "
            f"Failed: {result.failed}, Success rate: {result.success_rate:.2%}"
        )

    @staticmethod
    def _process_single_game_worker(
        game_log: AIWolfGameLog, config: dict[str, Any], output_dir: Path
    ) -> bool:
        """プロセス間で実行される単一ゲーム処理のワーカー関数

        Args:
            game_log: 処理対象のゲームログ
            config: アプリケーション設定辞書
            output_dir: 出力ディレクトリ

        Returns:
            処理が成功したかどうか
        """
        processor = GameProcessor(config)
        return processor.process(game_log, output_dir)
