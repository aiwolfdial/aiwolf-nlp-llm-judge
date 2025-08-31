"""AIWolf ゲームログのバッチ処理システム

このモジュールは、AIWolfのゲームログを並列処理で評価するためのシステムを提供します。
プロセス間並列処理とスレッド並列処理を組み合わせて効率的な処理を実現します。
"""

import json
import logging
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.aiwolf_log.game_log import AIWolfGameLog
from src.evaluator.config_loader import ConfigLoader
from src.evaluator.game_detector import GameDetector
from src.llm.evaluator import Evaluator
from src.llm.formatter import GameLogFormatter
from src.models.evaluation.config import EvaluationConfig
from src.models.evaluation.llm_response import EvaluationLLMResponse
from src.models.evaluation.result import EvaluationResult
from src.models.game import GameFormat, GameInfo
from src.utils.game_log_finder import find_all_game_logs

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessingConfig:
    """処理設定を表すデータクラス"""

    input_dir: Path
    output_dir: Path
    max_workers: int
    game_format: GameFormat


@dataclass
class ProcessingResult:
    """処理結果を表すデータクラス"""

    total: int = 0
    completed: int = 0
    failed: int = 0

    @property
    def success_rate(self) -> float:
        """成功率を計算"""
        return self.completed / self.total if self.total > 0 else 0.0


class GameProcessor:
    """単一ゲームの処理を担当するクラス"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.settings_path = Path(config.get("settings_path", "config/settings.yaml"))

    def process(self, game_log: AIWolfGameLog, output_dir: Path) -> bool:
        """ゲームログを処理して評価結果を出力"""
        try:
            logger.info(f"Processing game: {game_log.game_id}")

            # 1. 設定読み込みとゲーム情報検出
            evaluation_config = self._load_evaluation_config()
            game_info = self._detect_game_info(game_log)

            # 2. ログデータのフォーマット変換
            formatted_data = self._format_game_log(game_log, game_info)

            # 3. 評価実行（マルチスレッド）
            evaluation_result = self._execute_evaluations(
                evaluation_config, game_info, formatted_data
            )

            # 4. 結果保存
            self._save_results(game_log, game_info, evaluation_result, output_dir)

            logger.info(f"Successfully processed game: {game_log.game_id}")
            return True

        except FileNotFoundError as e:
            logger.error(f"Required file not found for game {game_log.game_id}: {e}")
            return False
        except ValueError as e:
            logger.error(f"Invalid data in game {game_log.game_id}: {e}")
            return False
        except KeyError as e:
            logger.error(f"Missing required key in game {game_log.game_id}: {e}")
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error processing game {game_log.game_id}: {e}", 
                exc_info=True
            )
            return False

    def _load_evaluation_config(self) -> EvaluationConfig:
        """評価設定を読み込み"""
        config = ConfigLoader.load_from_settings(self.settings_path)
        logger.debug(f"Loaded {len(config)} evaluation criteria")
        return config

    def _detect_game_info(self, game_log: AIWolfGameLog) -> GameInfo:
        """ゲーム情報を検出"""
        game_info = GameDetector.detect_game_format(
            game_log.log_path, self.settings_path
        )
        logger.debug(
            f"Detected game - format: {game_info.game_format.value}, "
            f"players: {game_info.player_count}"
        )
        return game_info

    def _format_game_log(
        self, game_log: AIWolfGameLog, game_info: GameInfo
    ) -> list[dict[str, Any]]:
        """ゲームログをフォーマット変換"""
        formatter = GameLogFormatter(game_log, self.config, parser=None)
        formatted_data = formatter.convert_to_jsonl(game_info.game_format)
        logger.debug(f"Formatted {len(formatted_data)} log entries")
        return formatted_data

    def _execute_evaluations(
        self,
        evaluation_config: EvaluationConfig,
        game_info: GameInfo,
        formatted_data: list[dict[str, Any]],
    ) -> EvaluationResult:
        """評価を並列実行"""
        criteria_for_game = evaluation_config.get_criteria_for_game(
            game_info.player_count
        )

        if not criteria_for_game:
            logger.warning(
                f"No evaluation criteria found for {game_info.player_count} players"
            )
            return EvaluationResult()

        logger.info(f"Starting evaluation for {len(criteria_for_game)} criteria")

        evaluator = Evaluator(self.config)
        evaluation_result = EvaluationResult()

        # ThreadPoolExecutorを使用した並列評価（最大スレッド数を制限）
        max_workers = min(len(criteria_for_game), 8)  # 最大8スレッドに制限
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # タスク投入
            future_to_criteria = {
                executor.submit(
                    self._evaluate_criterion, criteria, formatted_data, evaluator
                ): criteria
                for criteria in criteria_for_game
            }

            # 結果収集
            for future in as_completed(future_to_criteria):
                criteria = future_to_criteria[future]
                try:
                    criteria_name, llm_response = future.result()
                    evaluation_result.add_response(criteria_name, llm_response)
                    logger.debug(f"Completed evaluation: {criteria_name}")
                except Exception as e:
                    logger.error(
                        f"Evaluation failed for {criteria.name}: {e}", exc_info=True
                    )
                    raise

        logger.info(f"Completed all {len(criteria_for_game)} evaluations")
        return evaluation_result

    @staticmethod
    def _evaluate_criterion(
        criteria, formatted_data: list[dict[str, Any]], evaluator: Evaluator
    ) -> tuple[str, EvaluationLLMResponse]:
        """単一評価基準の評価を実行"""
        logger.debug(f"Evaluating: {criteria.name}")

        llm_response = evaluator.evaluation(
            criteria=criteria,
            log=formatted_data,
            output_structure=EvaluationLLMResponse,
        )

        return criteria.name, llm_response

    def _save_results(
        self,
        game_log: AIWolfGameLog,
        game_info: GameInfo,
        evaluation_result: EvaluationResult,
        output_dir: Path,
    ) -> None:
        """評価結果を保存"""
        result_data = self._build_result_data(game_log, game_info, evaluation_result)
        output_path = output_dir / f"{game_log.game_id}_result.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        logger.debug(f"Saved results to: {output_path}")

    @staticmethod
    def _build_result_data(
        game_log: AIWolfGameLog,
        game_info: GameInfo,
        evaluation_result: EvaluationResult,
    ) -> dict[str, Any]:
        """評価結果データを構築"""
        # プレイヤー名からチーム名へのマッピングを取得
        json_reader = game_log.get_json_reader()
        player_to_team = json_reader.get_agent_to_team_mapping()
        
        # デバッグ用ログ
        logger.debug(f"Player to team mapping: {player_to_team}")
        if evaluation_result.get_all_criteria_names():
            sample_criteria = evaluation_result.get_all_criteria_names()[0]
            sample_response = evaluation_result.get_by_criteria(sample_criteria)
            if sample_response.rankings:
                logger.debug(f"Sample player names from LLM: {[elem.player_name for elem in sample_response.rankings[:3]]}")

        result_data = {
            "game_id": game_log.game_id,
            "game_info": {
                "format": game_info.game_format.value,
                "player_count": game_info.player_count,
            },
            "evaluations": {},
        }

        for criteria_name in evaluation_result.get_all_criteria_names():
            response = evaluation_result.get_by_criteria(criteria_name)
            result_data["evaluations"][criteria_name] = {
                "rankings": [
                    {
                        "player_name": elem.player_name,
                        "team": player_to_team.get(elem.player_name, "unknown"),
                        "ranking": elem.ranking,
                        "reasoning": elem.reasoning,
                    }
                    for elem in response.rankings
                ]
            }

        return result_data


class BatchProcessor:
    """バッチ処理を管理するクラス"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.processing_config = self._extract_processing_config(config)

    def process_all_games(self) -> ProcessingResult:
        """すべてのゲームログを並列処理"""
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
        logger.info(
            f"Batch processing completed - "
            f"Total: {result.total}, Success: {result.completed}, "
            f"Failed: {result.failed}, Success rate: {result.success_rate:.2%}"
        )

        return result

    def _find_game_logs(self) -> list[AIWolfGameLog]:
        """ゲームログを検索"""
        logger.info(f"Searching for game logs in: {self.processing_config.input_dir}")
        game_logs = find_all_game_logs(self.processing_config.input_dir)
        logger.info(f"Found {len(game_logs)} game logs")
        return game_logs

    def _execute_parallel_processing(
        self, game_logs: list[AIWolfGameLog]
    ) -> ProcessingResult:
        """並列処理を実行"""
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
                        logger.info(f"✓ Completed: {game_log.game_id}")
                    else:
                        result.failed += 1
                        logger.error(f"✗ Failed: {game_log.game_id}")
                except Exception as e:
                    result.failed += 1
                    logger.error(f"✗ Error processing {game_log.game_id}: {e}")

        return result

    @staticmethod
    def _extract_processing_config(config: dict[str, Any]) -> ProcessingConfig:
        """設定から処理設定を抽出"""
        try:
            processing_config = config["processing"]
            input_dir = Path(processing_config["input_dir"])
            output_dir = Path(processing_config["output_dir"])
            max_workers = processing_config.get("max_workers") or mp.cpu_count()

            # ゲーム形式を文字列からEnumに変換（無効な値の場合は処理を停止）
            game_format_str = config.get("game", {}).get("format", "self_match")
            try:
                game_format = GameFormat(game_format_str)
            except ValueError as e:
                logger.error(f"Invalid game format: '{game_format_str}'. Valid values are: {[fmt.value for fmt in GameFormat]}")
                raise ValueError(f"Invalid game format '{game_format_str}' in configuration") from e

            return ProcessingConfig(
                input_dir=input_dir,
                output_dir=output_dir,
                max_workers=max_workers,
                game_format=game_format,
            )

        except KeyError as e:
            raise ValueError(f"Missing required config key: {e}") from e

    @staticmethod
    def _process_single_game_worker(
        game_log: AIWolfGameLog, config: dict[str, Any], output_dir: Path
    ) -> bool:
        """プロセス間で実行される単一ゲーム処理のワーカー関数"""
        processor = GameProcessor(config)
        return processor.process(game_log, output_dir)
