"""評価実行・並列処理サービス."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from src.evaluation.models.config import EvaluationConfig
from src.evaluation.models.criteria import EvaluationCriteria
from src.evaluation.models.llm_response import EvaluationLLMResponse
from src.evaluation.models.result import EvaluationResult, CriteriaEvaluationResult
from src.game.models import GameInfo
from src.llm.evaluator import Evaluator
from src.processor.models.exceptions import EvaluationExecutionError

logger = logging.getLogger(__name__)


class EvaluationExecutionService:
    """評価実行・並列処理を担当するサービス

    責任:
    - マルチスレッド評価の管理
    - 単一評価基準の実行
    """

    def __init__(self, config: dict[str, Any], max_evaluation_threads: int = 8) -> None:
        """初期化

        Args:
            config: アプリケーション設定辞書
            max_evaluation_threads: 評価用最大スレッド数
        """
        self.config = config
        self.max_evaluation_threads = max_evaluation_threads

    def execute_evaluations(
        self,
        evaluation_config: EvaluationConfig,
        game_info: GameInfo,
        formatted_data: list[dict[str, Any]],
        character_info: str,
        agent_to_team_mapping: dict[str, str],
    ) -> EvaluationResult:
        """評価を並列実行

        Args:
            evaluation_config: 評価設定
            game_info: ゲーム情報
            formatted_data: フォーマット済みログデータ
            character_info: キャラクター情報
            agent_to_team_mapping: エージェント名→チーム名のマッピング

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
                        # CriteriaEvaluationResultを作成してリストに追加
                        criteria_result = CriteriaEvaluationResult.from_llm_response(
                            criteria_name, llm_response, agent_to_team_mapping
                        )
                        evaluation_result.append(criteria_result)
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
        formatted_data: list[dict[str, Any]],
        evaluator: Evaluator,
        character_info: str,
    ) -> tuple[str, EvaluationLLMResponse]:
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
