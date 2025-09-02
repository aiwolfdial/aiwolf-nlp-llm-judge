"""結果保存・チームマッピングサービス."""

import json
import logging
from pathlib import Path
from typing import Any

from src.aiwolf_log.game_log import AIWolfGameLog
from src.evaluation.models.result import EvaluationResult
from src.game.models import GameInfo

logger = logging.getLogger(__name__)


class ResultWritingService:
    """結果保存・チームマッピングを担当するサービス

    責任:
    - 評価結果データの構築
    - チームマッピングの処理
    - ファイル保存
    """

    def save_results(
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
    ) -> dict[str, Any]:
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
        self, evaluation_result: EvaluationResult, player_to_team: dict[str, str]
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
