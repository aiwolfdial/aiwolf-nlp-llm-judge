"""単一ゲームの処理を担当するクラス（リファクタリング後）."""

import logging
from pathlib import Path
from typing import Any
from src.evaluation.models.result import EvaluationResult

from src.aiwolf_log.game_log import AIWolfGameLog

from .pipeline import (
    DataPreparationService,
    EvaluationExecutionService,
    LogFormattingService,
    ResultWritingService,
)

logger = logging.getLogger(__name__)


class GameProcessor:
    """単一ゲームの処理を担当するクラス（リファクタリング後）

    このクラスは、各サービスを組み合わせてゲームログの評価処理を
    オーケストレートする責任を持ちます。

    責任:
    - 処理フローの管理
    - サービス間の調整
    - エラーハンドリング
    """

    # クラス定数
    SUCCESS_INDICATOR = "✓"
    FAILURE_INDICATOR = "✗"

    def __init__(self, config: dict[str, Any]) -> None:
        """GameProcessorを初期化

        Args:
            config: アプリケーション設定辞書

        Raises:
            ConfigurationError: 設定が不正な場合
        """
        self.config = config

        # 各サービスを初期化
        self.data_prep_service = DataPreparationService(config)
        self.log_formatting_service = LogFormattingService(config)
        self.result_service = ResultWritingService()

        # 評価用スレッド数を取得して評価サービスを初期化
        max_threads = self.data_prep_service.get_evaluation_workers()
        self.evaluation_service = EvaluationExecutionService(config, max_threads)

    def process(
        self, game_log: AIWolfGameLog, output_dir: Path
    ) -> tuple[bool, dict | None]:
        """ゲームログを処理して評価結果を出力

        Args:
            game_log: 処理対象のゲームログ
            output_dir: 結果出力ディレクトリ

        Returns:
            (処理が成功したかどうか, 評価結果辞書またはNone)
        """
        try:
            logger.info(f"Processing game: {game_log.game_id}")

            # 1. 設定とゲーム情報の準備
            evaluation_config = self.data_prep_service.load_evaluation_config()
            game_info = self.data_prep_service.detect_game_info(game_log)

            # 2. ログデータのフォーマット変換
            formatted_data = self.log_formatting_service.format_game_log(
                game_log, game_info
            )

            # 3. キャラクター情報の取得
            character_info = self.log_formatting_service.get_character_info(game_log)

            # 4. チームマッピングの取得
            agent_to_team_mapping = game_log.get_agent_to_team_mapping()

            # 5. 評価実行（マルチスレッド）
            evaluation_result = self.evaluation_service.execute_evaluations(
                evaluation_config,
                game_info,
                formatted_data,
                character_info,
                agent_to_team_mapping,
            )

            # 6. 結果保存
            self.result_service.save_results(
                game_log, game_info, evaluation_result, output_dir
            )

            # 7. 評価結果を辞書形式に変換
            evaluation_dict = self._convert_evaluation_result_to_dict(evaluation_result)

            logger.info(f"Successfully processed game: {game_log.game_id}")
            return True, evaluation_dict

        except (FileNotFoundError, ValueError, KeyError) as e:
            logger.error(f"Expected error processing game {game_log.game_id}: {e}")
            return False, None
        except Exception as e:
            logger.error(
                f"Unexpected error processing game {game_log.game_id}: {e}",
                exc_info=True,
            )
            return False, None

    def _convert_evaluation_result_to_dict(
        self, evaluation_result: EvaluationResult
    ) -> dict:
        """評価結果をプロセス間通信用の辞書形式に変換

        Args:
            evaluation_result: 評価結果

        Returns:
            辞書形式の評価結果
        """
        evaluation_dict = {"evaluations": {}}

        for criteria_result in evaluation_result:
            evaluation_dict["evaluations"][criteria_result.criteria_name] = {
                "rankings": [
                    {
                        "player_name": elem.player_name,
                        "team": elem.team,
                        "ranking": elem.ranking,
                        "reasoning": elem.reasoning,
                    }
                    for elem in criteria_result
                ]
            }

        return evaluation_dict
