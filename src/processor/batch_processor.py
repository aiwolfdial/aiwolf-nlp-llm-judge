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
from .pipeline.aggregation_output import AggregationOutputService

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
        self.aggregation_output = AggregationOutputService()

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
            # 評価設定マッピングを作成
            criteria_mappings = self._load_evaluation_criteria_mappings()

            # チーム集計データを作成
            aggregation_data = self._create_team_aggregation_data(
                evaluation_results, criteria_mappings
            )

            # 集計結果を保存
            self._save_team_aggregation_results(aggregation_data)

        except Exception as e:
            logger.error(f"Failed to generate team aggregation: {e}", exc_info=True)

    def _load_evaluation_criteria_mappings(self) -> dict[str, dict[str, Any]]:
        """評価基準のマッピング情報を読み込み

        Returns:
            criteria_name_to_description: criteria名 -> description のマッピング
            criteria_name_to_order: criteria名 -> order のマッピング
        """
        from src.processor.pipeline import DataPreparationService

        # settings_pathが存在しない場合はconfigから追加
        config_with_settings = self.config.copy()
        if "settings_path" not in config_with_settings:
            # path.evaluation_criteriaからsettings.yamlのパスを推定
            criteria_path = Path(
                self.config.get("path", {}).get(
                    "evaluation_criteria", "config/evaluation_criteria.yaml"
                )
            )
            settings_path = criteria_path.parent / "settings.yaml"
            config_with_settings["settings_path"] = str(settings_path)

        data_prep_service = DataPreparationService(config_with_settings)
        evaluation_config = data_prep_service.load_evaluation_config()

        return {
            "criteria_name_to_description": {
                criteria.name: criteria.description for criteria in evaluation_config
            },
            "criteria_name_to_order": {
                criteria.name: criteria.order for criteria in evaluation_config
            },
        }

    def _create_team_aggregation_data(
        self,
        evaluation_results: list[dict],
        criteria_mappings: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """チーム集計データを作成

        Args:
            evaluation_results: 評価結果辞書のリスト
            criteria_mappings: 評価基準マッピング情報

        Returns:
            集計データ辞書
        """
        aggregator = TeamAggregator()

        # 各評価結果辞書をTeamAggregatorに変換して追加
        for evaluation_dict in evaluation_results:
            evaluation_result = self._convert_dict_to_evaluation_result(evaluation_dict)
            aggregator.add_game_result(evaluation_result)

        # チーム集計結果を計算
        team_averages = aggregator.calculate_team_averages()
        team_counts = aggregator.get_team_count_by_criteria()

        # criteria名をdescriptionに変換
        team_averages_with_descriptions = self._convert_criteria_names_to_descriptions(
            team_averages, criteria_mappings
        )
        team_counts_with_descriptions = self._convert_criteria_names_to_descriptions(
            team_counts, criteria_mappings
        )

        # 評価基準リストを作成（orderでソート済み）
        criteria_evaluated = self._create_sorted_criteria_list(
            team_averages_with_descriptions, criteria_mappings
        )

        return {
            "team_averages": team_averages_with_descriptions,
            "team_sample_counts": team_counts_with_descriptions,
            "summary": {
                "total_games_processed": len(evaluation_results),
                "teams_found": list(team_averages_with_descriptions.keys()),
                "criteria_evaluated": criteria_evaluated,
            },
        }

    def _convert_criteria_names_to_descriptions(
        self,
        data: dict[str, dict[str, Any]],
        criteria_mappings: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """criteria_name を description に変換し、orderでソート

        Args:
            data: 変換対象のデータ
            criteria_mappings: 評価基準マッピング情報

        Returns:
            変換・ソート済みデータ
        """
        criteria_name_to_description = criteria_mappings["criteria_name_to_description"]
        criteria_name_to_order = criteria_mappings["criteria_name_to_order"]

        converted = {}
        for team, criteria_dict in data.items():
            # criteria_nameをorderでソートしてからdescriptionに変換
            sorted_criteria = sorted(
                criteria_dict.items(),
                key=lambda x: criteria_name_to_order.get(x[0], 999),
            )
            converted[team] = {}
            for criteria_name, value in sorted_criteria:
                description = criteria_name_to_description.get(
                    criteria_name, criteria_name
                )
                converted[team][description] = value
        return converted

    def _create_sorted_criteria_list(
        self,
        team_averages_with_descriptions: dict[str, dict[str, Any]],
        criteria_mappings: dict[str, dict[str, Any]],
    ) -> list[str]:
        """orderでソートされた評価基準リストを作成

        Args:
            team_averages_with_descriptions: description変換済みチーム平均データ
            criteria_mappings: 評価基準マッピング情報

        Returns:
            ソート済み評価基準リスト
        """
        if not team_averages_with_descriptions:
            return []

        criteria_name_to_description = criteria_mappings["criteria_name_to_description"]
        criteria_name_to_order = criteria_mappings["criteria_name_to_order"]

        first_team_criteria = next(iter(team_averages_with_descriptions.values()), {})

        # descriptionからcriteria_nameに逆変換してソート
        description_to_criteria_name = {
            v: k for k, v in criteria_name_to_description.items()
        }
        criteria_with_order = []
        for description in first_team_criteria.keys():
            criteria_name = description_to_criteria_name.get(description, description)
            order = criteria_name_to_order.get(criteria_name, 999)
            criteria_with_order.append((order, description))

        return [desc for _, desc in sorted(criteria_with_order)]

    def _save_team_aggregation_results(self, aggregation_data: dict[str, Any]) -> None:
        """チーム集計結果をJSONとCSVで保存

        Args:
            aggregation_data: 集計データ
        """
        self.aggregation_output.save_both(
            aggregation_data, self.processing_config.output_dir
        )

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

        # evaluation_dictがevaluationsフィールドを含む場合（個別結果ファイル）と
        # evaluationsの内容のみの場合（並列処理の戻り値）を判断
        evaluations_data = evaluation_dict.get("evaluations", evaluation_dict)

        for criteria_name, criteria_data in evaluations_data.items():
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

    def regenerate_aggregation_only(self) -> None:
        """既存の評価結果JSONファイルからチーム集計を再生成

        output_dir内の*_result.jsonファイルを読み込み、
        team_aggregation.jsonとteam_aggregation.csvを再生成する。
        """
        logger.info(
            f"Loading existing evaluation results from {self.processing_config.output_dir}"
        )

        # 評価結果JSONファイルを検索
        result_files = list(self.processing_config.output_dir.glob("*_result.json"))

        if not result_files:
            logger.warning(
                f"No evaluation result JSON files found in {self.processing_config.output_dir}"
            )
            return

        logger.info(f"Found {len(result_files)} evaluation result files")

        # 各JSONファイルを読み込み
        evaluation_results = []
        for result_file in result_files:
            try:
                with result_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    # evaluationsフィールドを取得（ファイル形式）
                    if "evaluations" in data:
                        evaluation_results.append(data["evaluations"])
                        logger.info(f"Loaded: {result_file.name}")
                    else:
                        logger.warning(
                            f"No evaluations field found in {result_file.name}"
                        )
            except Exception as e:
                logger.error(f"Failed to load {result_file.name}: {e}")

        if not evaluation_results:
            logger.error("No valid evaluation results loaded")
            return

        logger.info(f"Successfully loaded {len(evaluation_results)} evaluation results")

        # チーム集計を生成
        self._generate_team_aggregation(evaluation_results)
