"""単一ゲームの処理を担当するクラス."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.aiwolf_log.game_log import AIWolfGameLog
from src.evaluation.loaders.criteria_loader import CriteriaLoader
from src.evaluation.loaders.settings_loader import SettingsLoader
from src.game.detector import GameDetector
from src.llm.evaluator import Evaluator
from src.llm.formatter import GameLogFormatter
from src.evaluation.models.config import EvaluationConfig
from src.evaluation.models.criteria import EvaluationCriteria
from src.evaluation.models.llm_response import EvaluationLLMResponse
from src.evaluation.models.result import EvaluationResult
from src.game.models import GameInfo

from .errors import (
    ConfigurationError,
    EvaluationExecutionError,
    GameLogProcessingError,
)

logger = logging.getLogger(__name__)


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

        # 設定から評価用スレッド数を読み込み（デフォルト8）
        self.max_evaluation_threads = self._load_evaluation_workers()

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
            criteria_path = SettingsLoader.get_evaluation_criteria_path(
                self.settings_path
            )
            config = CriteriaLoader.load_evaluation_config(criteria_path)
            logger.debug(f"Loaded {len(config)} evaluation criteria")
            return config
        except Exception as e:
            raise ConfigurationError(f"Failed to load evaluation config: {e}") from e

    def _load_evaluation_workers(self) -> int:
        """設定から評価用スレッド数を読み込み

        Returns:
            評価用スレッド数（デフォルト: 8）

        Raises:
            ConfigurationError: 設定読み込みに失敗した場合
        """
        try:
            from src.utils.yaml_loader import YAMLLoader

            config_data = YAMLLoader.load_yaml(self.settings_path)
            evaluation_workers = config_data.get("processing", {}).get(
                "evaluation_workers", 8
            )

            # 値の妥当性チェック
            if not isinstance(evaluation_workers, int) or evaluation_workers < 1:
                logger.warning(
                    f"Invalid evaluation_workers value: {evaluation_workers}, using default: 8"
                )
                return 8

            logger.debug(f"Loaded evaluation_workers: {evaluation_workers}")
            return evaluation_workers

        except Exception as e:
            logger.warning(f"Failed to load evaluation_workers: {e}, using default: 8")
            return 8

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
            max_workers = min(len(criteria_for_game), self.max_evaluation_threads)

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
