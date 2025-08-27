from dataclasses import dataclass
from typing import List, Dict

from models.game import GameFormat
from models.evaluation.criteria import EvaluationCriteria


@dataclass
class EvaluationConfig:
    """評価設定を表すデータクラス"""

    common_criteria: List[EvaluationCriteria]
    game_specific_criteria: Dict[GameFormat, List[EvaluationCriteria]]

    def get_criteria_for_game(
        self, game_format: GameFormat
    ) -> List[EvaluationCriteria]:
        """指定されたゲーム形式の全評価基準を取得"""
        criteria = self.common_criteria.copy()
        if game_format in self.game_specific_criteria:
            criteria.extend(self.game_specific_criteria[game_format])
        return criteria

    def get_criteria_by_name(
        self, criteria_name: str, game_format: GameFormat
    ) -> EvaluationCriteria:
        """基準名で評価基準を取得"""
        all_criteria = self.get_criteria_for_game(game_format)
        for criteria in all_criteria:
            if criteria.name == criteria_name:
                return criteria
        raise KeyError(
            f"Criteria '{criteria_name}' not found for game format {game_format.value}"
        )
