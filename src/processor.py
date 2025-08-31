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
from typing import Any, Dict, List, Tuple

from src.aiwolf_log.game_log import AIWolfGameLog
from src.evaluator.config_loader import ConfigLoader
from src.evaluator.game_detector import GameDetector
from src.llm.evaluator import Evaluator
from src.llm.formatter import GameLogFormatter
from src.models.evaluation.config import EvaluationConfig
from src.models.evaluation.criteria import EvaluationCriteria
from src.models.evaluation.llm_response import EvaluationLLMResponse
from src.models.evaluation.result import EvaluationResult
from src.models.game import GameFormat, GameInfo
from src.utils.game_log_finder import find_all_game_logs

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessingConfig:
    """処理設定を表すデータクラス

    Attributes:
        input_dir: 入力ディレクトリのパス
        output_dir: 出力ディレクトリのパス
        max_workers: 並列処理の最大ワーカー数
        game_format: ゲーム形式
    """

    input_dir: Path
    output_dir: Path
    max_workers: int
    game_format: GameFormat


@dataclass
class ProcessingResult:
    """処理結果を表すデータクラス

    Attributes:
        total: 処理対象の総数
        completed: 正常完了した数
        failed: 失敗した数
    """

    total: int = 0
    completed: int = 0
    failed: int = 0

    @property
    def success_rate(self) -> float:
        """成功率を計算

        Returns:
            成功率（0.0-1.0）
        """
        return self.completed / self.total if self.total > 0 else 0.0


class ProcessingError(Exception):
    """処理エラーの基底クラス"""

    pass


class GameLogProcessingError(ProcessingError):
    """ゲームログ処理に関するエラー"""

    pass


class EvaluationExecutionError(ProcessingError):
    """評価実行に関するエラー"""

    pass


class ConfigurationError(ProcessingError):
    """設定に関するエラー"""

    pass


class GameProcessor:
    """単一ゲームの処理を担当するクラス

    このクラスは、AIWolfのゲームログを読み込み、LLMによる評価を実行し、
    結果を構造化されたJSON形式で出力する責任を持ちます。

    主な機能:
    - ゲームログの読み込みとフォーマット変換
    - 評価基準に基づく並列評価の実行
    - 結果のチームマッピングと出力
    """

    # クラス定数
    MAX_EVALUATION_THREADS = 8
    DEFAULT_SETTINGS_PATH = "config/settings.yaml"
    SUCCESS_INDICATOR = "✓"
    FAILURE_INDICATOR = "✗"

    def __init__(self, config: Dict[str, Any]) -> None:
        """GameProcessorを初期化

        Args:
            config: アプリケーション設定辞書

        Raises:
            ConfigurationError: 設定が不正な場合
        """
        self.config = config
        self.settings_path = Path(
            config.get("settings_path", self.DEFAULT_SETTINGS_PATH)
        )

        if not self.settings_path.exists():
            raise ConfigurationError(f"Settings file not found: {self.settings_path}")

    def process(self, game_log: AIWolfGameLog, output_dir: Path) -> bool:
        """ゲームログを処理して評価結果を出力

        Args:
            game_log: 処理対象のゲームログ
            output_dir: 結果出力ディレクトリ

        Returns:
            処理が成功したかどうか
        """
        try:
            logger.info(f"Processing game: {game_log.game_id}")

            # 1. 設定とゲーム情報の準備
            evaluation_config = self._load_evaluation_config()
            game_info = self._detect_game_info(game_log)

            # 2. ログデータのフォーマット変換
            formatted_data = self._format_game_log(game_log, game_info)

            # 3. キャラクター情報の取得
            character_info = self._get_character_info(game_log)

            # 4. 評価実行（マルチスレッド）
            evaluation_result = self._execute_evaluations(
                evaluation_config, game_info, formatted_data, character_info
            )

            # 5. 結果保存
            self._save_results(game_log, game_info, evaluation_result, output_dir)

            logger.info(f"Successfully processed game: {game_log.game_id}")
            return True

        except (FileNotFoundError, ValueError, KeyError) as e:
            logger.error(f"Expected error processing game {game_log.game_id}: {e}")
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error processing game {game_log.game_id}: {e}",
                exc_info=True,
            )
            return False

    def _load_evaluation_config(self) -> EvaluationConfig:
        """評価設定を読み込み

        Returns:
            評価設定オブジェクト

        Raises:
            ConfigurationError: 設定読み込みに失敗した場合
        """
        try:
            config = ConfigLoader.load_from_settings(self.settings_path)
            logger.debug(f"Loaded {len(config)} evaluation criteria")
            return config
        except Exception as e:
            raise ConfigurationError(f"Failed to load evaluation config: {e}") from e

    def _detect_game_info(self, game_log: AIWolfGameLog) -> GameInfo:
        """ゲーム情報を検出

        Args:
            game_log: ゲームログ

        Returns:
            検出されたゲーム情報

        Raises:
            GameLogProcessingError: ゲーム情報の検出に失敗した場合
        """
        try:
            game_info = GameDetector.detect_game_format(
                game_log.log_path, self.settings_path
            )
            logger.debug(
                f"Detected game - format: {game_info.game_format.value}, "
                f"players: {game_info.player_count}"
            )
            return game_info
        except Exception as e:
            raise GameLogProcessingError(f"Failed to detect game info: {e}") from e

    def _format_game_log(
        self, game_log: AIWolfGameLog, game_info: GameInfo
    ) -> List[Dict[str, Any]]:
        """ゲームログをフォーマット変換

        Args:
            game_log: ゲームログ
            game_info: ゲーム情報

        Returns:
            フォーマット済みのログデータリスト

        Raises:
            GameLogProcessingError: フォーマット変換に失敗した場合
        """
        try:
            formatter = GameLogFormatter(game_log, self.config, parser=None)
            formatted_data = formatter.convert_to_jsonl(game_info.game_format)
            logger.debug(f"Formatted {len(formatted_data)} log entries")
            return formatted_data
        except Exception as e:
            raise GameLogProcessingError(f"Failed to format game log: {e}") from e

    def _get_character_info(self, game_log: AIWolfGameLog) -> str:
        """キャラクター情報を取得してフォーマット

        Args:
            game_log: ゲームログ

        Returns:
            フォーマット済みのキャラクター情報文字列
        """
        try:
            json_reader = game_log.get_json_reader()
            profiles = json_reader.get_initialize_profiles()

            if not profiles:
                logger.warning(
                    f"No character profiles found for game: {game_log.game_id}"
                )
                return ""

            character_lines = [
                f"- {agent_name}: {profile}" for agent_name, profile in profiles.items()
            ]
            return "\n".join(character_lines)

        except Exception as e:
            logger.warning(
                f"Failed to get character info for game {game_log.game_id}: {e}"
            )
            return ""

    def _execute_evaluations(
        self,
        evaluation_config: EvaluationConfig,
        game_info: GameInfo,
        formatted_data: List[Dict[str, Any]],
        character_info: str,
    ) -> EvaluationResult:
        """評価を並列実行

        Args:
            evaluation_config: 評価設定
            game_info: ゲーム情報
            formatted_data: フォーマット済みログデータ
            character_info: キャラクター情報

        Returns:
            評価結果

        Raises:
            EvaluationExecutionError: 評価実行に失敗した場合
        """
        criteria_for_game = evaluation_config.get_criteria_for_game(
            game_info.player_count
        )

        if not criteria_for_game:
            logger.warning(
                f"No evaluation criteria found for {game_info.player_count} players"
            )
            return EvaluationResult()

        logger.info(f"Starting evaluation for {len(criteria_for_game)} criteria")

        try:
            evaluator = Evaluator(self.config)
            evaluation_result = EvaluationResult()

            # ThreadPoolExecutorを使用した並列評価
            max_workers = min(len(criteria_for_game), self.MAX_EVALUATION_THREADS)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # タスク投入
                future_to_criteria = {
                    executor.submit(
                        self._evaluate_criterion,
                        criteria,
                        formatted_data,
                        evaluator,
                        character_info,
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
                        error_msg = f"Evaluation failed for {criteria.name}: {e}"
                        logger.error(error_msg, exc_info=True)
                        raise EvaluationExecutionError(error_msg) from e

            logger.info(f"Completed all {len(criteria_for_game)} evaluations")
            return evaluation_result

        except Exception as e:
            if isinstance(e, EvaluationExecutionError):
                raise
            raise EvaluationExecutionError(f"Failed to execute evaluations: {e}") from e

    @staticmethod
    def _evaluate_criterion(
        criteria: EvaluationCriteria,
        formatted_data: List[Dict[str, Any]],
        evaluator: Evaluator,
        character_info: str,
    ) -> Tuple[str, EvaluationLLMResponse]:
        """単一評価基準の評価を実行

        Args:
            criteria: 評価基準
            formatted_data: フォーマット済みログデータ
            evaluator: LLM評価器
            character_info: キャラクター情報

        Returns:
            (評価基準名, LLMレスポンス)のタプル
        """
        logger.debug(f"Evaluating: {criteria.name}")

        llm_response = evaluator.evaluation(
            criteria=criteria,
            log=formatted_data,
            output_structure=EvaluationLLMResponse,
            character_info=character_info,
        )

        return criteria.name, llm_response

    def _save_results(
        self,
        game_log: AIWolfGameLog,
        game_info: GameInfo,
        evaluation_result: EvaluationResult,
        output_dir: Path,
    ) -> None:
        """評価結果を保存

        Args:
            game_log: ゲームログ
            game_info: ゲーム情報
            evaluation_result: 評価結果
            output_dir: 出力ディレクトリ
        """
        result_data = self._build_result_data(game_log, game_info, evaluation_result)
        output_path = output_dir / f"{game_log.game_id}_result.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        logger.debug(f"Saved results to: {output_path}")

    def _build_result_data(
        self,
        game_log: AIWolfGameLog,
        game_info: GameInfo,
        evaluation_result: EvaluationResult,
    ) -> Dict[str, Any]:
        """評価結果データを構築

        Args:
            game_log: ゲームログ
            game_info: ゲーム情報
            evaluation_result: 評価結果

        Returns:
            構築された結果データ辞書
        """
        # プレイヤー名からチーム名へのマッピングを取得
        json_reader = game_log.get_json_reader()
        player_to_team = json_reader.get_agent_to_team_mapping()

        # デバッグ用ログ
        self._log_debug_info(evaluation_result, player_to_team)

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

    def _log_debug_info(
        self, evaluation_result: EvaluationResult, player_to_team: Dict[str, str]
    ) -> None:
        """デバッグ情報をログ出力

        Args:
            evaluation_result: 評価結果
            player_to_team: プレイヤー→チームマッピング
        """
        logger.debug(f"Player to team mapping: {player_to_team}")

        criteria_names = evaluation_result.get_all_criteria_names()
        if criteria_names:
            sample_criteria = criteria_names[0]
            sample_response = evaluation_result.get_by_criteria(sample_criteria)
            if sample_response.rankings:
                sample_players = [
                    elem.player_name for elem in sample_response.rankings[:3]
                ]
                logger.debug(f"Sample player names from LLM: {sample_players}")


class BatchProcessor:
    """バッチ処理を管理するクラス

    このクラスは、複数のゲームログに対して並列処理を実行し、
    処理結果の統計情報を管理する責任を持ちます。
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """BatchProcessorを初期化

        Args:
            config: アプリケーション設定辞書
        """
        self.config = config
        self.processing_config = self._extract_processing_config(config)

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

    def _find_game_logs(self) -> List[AIWolfGameLog]:
        """ゲームログを検索

        Returns:
            発見されたゲームログのリスト
        """
        logger.info(f"Searching for game logs in: {self.processing_config.input_dir}")
        game_logs = find_all_game_logs(self.processing_config.input_dir)
        logger.info(f"Found {len(game_logs)} game logs")
        return game_logs

    def _execute_parallel_processing(
        self, game_logs: List[AIWolfGameLog]
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
    def _extract_processing_config(config: Dict[str, Any]) -> ProcessingConfig:
        """設定から処理設定を抽出

        Args:
            config: アプリケーション設定辞書

        Returns:
            処理設定オブジェクト

        Raises:
            ConfigurationError: 設定が不正な場合
        """
        try:
            processing_config = config["processing"]
            input_dir = Path(processing_config["input_dir"])
            output_dir = Path(processing_config["output_dir"])
            max_workers = processing_config.get("max_workers") or mp.cpu_count()

            # ゲーム形式を文字列からEnumに変換
            game_format_str = config.get("game", {}).get("format", "self_match")
            try:
                game_format = GameFormat(game_format_str)
            except ValueError as e:
                valid_formats = [fmt.value for fmt in GameFormat]
                error_msg = (
                    f"Invalid game format: '{game_format_str}'. "
                    f"Valid values are: {valid_formats}"
                )
                logger.error(error_msg)
                raise ConfigurationError(error_msg) from e

            return ProcessingConfig(
                input_dir=input_dir,
                output_dir=output_dir,
                max_workers=max_workers,
                game_format=game_format,
            )

        except KeyError as e:
            raise ConfigurationError(f"Missing required config key: {e}") from e

    @staticmethod
    def _process_single_game_worker(
        game_log: AIWolfGameLog, config: Dict[str, Any], output_dir: Path
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
