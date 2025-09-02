"""バッチ処理を管理するクラス."""

import json
import logging
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from src.aiwolf_log import AIWolfGameLog
from src.utils.game_log_finder import find_all_game_logs
from src.evaluation.models.result import TeamAggregator

from .game_processor import GameProcessor
from .models import ProcessingConfig, ProcessingResult

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

        # チーム集計実行
        if result.completed > 0:
            self._generate_team_aggregation(result.evaluation_results)

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
                    success, evaluation_dict = future.result()
                    if success and evaluation_dict:
                        result.completed += 1
                        result.evaluation_results.append(evaluation_dict)
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
    ) -> tuple[bool, dict | None]:
        """プロセス間で実行される単一ゲーム処理のワーカー関数

        Args:
            game_log: 処理対象のゲームログ
            config: アプリケーション設定辞書
            output_dir: 出力ディレクトリ

        Returns:
            (処理が成功したかどうか, 評価結果辞書またはNone)
        """
        processor = GameProcessor(config)
        return processor.process(game_log, output_dir)

    def _generate_team_aggregation(self, evaluation_results: list[dict]) -> None:
        """チーム集計結果を生成して保存

        Args:
            evaluation_results: 評価結果辞書のリスト
        """
        logger.info("Generating team aggregation results")

        try:
            # 評価設定を読み込んで、criteria_name -> description のマッピングを作成
            from src.processor.pipeline import DataPreparationService

            data_prep_service = DataPreparationService(self.config)
            evaluation_config = data_prep_service.load_evaluation_config()

            # criteria_name -> description のマッピングを作成
            criteria_name_to_description = {
                criteria.name: criteria.description for criteria in evaluation_config
            }

            aggregator = TeamAggregator()

            # 各評価結果辞書をTeamAggregatorに変換して追加
            for evaluation_dict in evaluation_results:
                evaluation_result = self._convert_dict_to_evaluation_result(
                    evaluation_dict
                )
                aggregator.add_game_result(evaluation_result)

            # チーム集計結果を計算・保存
            team_averages = aggregator.calculate_team_averages()
            team_counts = aggregator.get_team_count_by_criteria()

            # criteria_name を description に変換
            def convert_criteria_names_to_descriptions(
                data: dict[str, dict[str, Any]],
            ) -> dict[str, dict[str, Any]]:
                """criteria_name を description に変換"""
                converted = {}
                for team, criteria_dict in data.items():
                    converted[team] = {}
                    for criteria_name, value in criteria_dict.items():
                        description = criteria_name_to_description.get(
                            criteria_name, criteria_name
                        )
                        converted[team][description] = value
                return converted

            # 変換された集計結果
            team_averages_with_descriptions = convert_criteria_names_to_descriptions(
                team_averages
            )
            team_counts_with_descriptions = convert_criteria_names_to_descriptions(
                team_counts
            )

            aggregation_data = {
                "team_averages": team_averages_with_descriptions,
                "team_sample_counts": team_counts_with_descriptions,
                "summary": {
                    "total_games_processed": len(evaluation_results),
                    "teams_found": list(team_averages_with_descriptions.keys()),
                    "criteria_evaluated": list(
                        next(iter(team_averages_with_descriptions.values()), {}).keys()
                    ),
                },
            }

            # 集計結果をファイル保存
            aggregation_file = (
                self.processing_config.output_dir / "team_aggregation.json"
            )
            with open(aggregation_file, "w", encoding="utf-8") as f:
                json.dump(aggregation_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Team aggregation saved to: {aggregation_file}")
            logger.info(
                f"Teams processed: {list(team_averages_with_descriptions.keys())}"
            )

        except Exception as e:
            logger.error(f"Failed to generate team aggregation: {e}", exc_info=True)

    def _convert_dict_to_evaluation_result(self, evaluation_dict: dict):
        """辞書形式の評価結果をEvaluationResultオブジェクトに変換

        Args:
            evaluation_dict: 辞書形式の評価結果

        Returns:
            EvaluationResult オブジェクト
        """
        from src.evaluation.models.result import (
            EvaluationResult,
            CriteriaEvaluationResult,
            EvaluationResultElement,
        )

        evaluation_result = EvaluationResult()

        for criteria_name, criteria_data in evaluation_dict.get(
            "evaluations", {}
        ).items():
            elements = []
            for ranking_data in criteria_data.get("rankings", []):
                element = EvaluationResultElement(
                    player_name=ranking_data["player_name"],
                    reasoning=ranking_data["reasoning"],
                    ranking=ranking_data["ranking"],
                    team=ranking_data["team"],
                )
                elements.append(element)

            criteria_result = CriteriaEvaluationResult(
                criteria_name=criteria_name, elements=elements
            )
            evaluation_result.append(criteria_result)

        return evaluation_result
