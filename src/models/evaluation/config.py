from dataclasses import dataclass
from typing import List, Dict

from models.game import ParticipantNum
from models.evaluation.criteria import EvaluationCriteria


@dataclass
class EvaluationConfig:
    """評価設定を表すデータクラス"""

    common_criteria: List[EvaluationCriteria]
    game_specific_criteria: Dict[ParticipantNum, List[EvaluationCriteria]]

    def get_criteria_for_game(
        self, participant_num: ParticipantNum
    ) -> List[EvaluationCriteria]:
        """指定された参加人数の全評価基準を取得"""
        criteria = self.common_criteria.copy()
        if participant_num in self.game_specific_criteria:
            criteria.extend(self.game_specific_criteria[participant_num])
        return criteria

    def get_criteria_by_name(
        self, criteria_name: str, participant_num: ParticipantNum
    ) -> EvaluationCriteria:
        """基準名で評価基準を取得"""
        all_criteria = self.get_criteria_for_game(participant_num)
        for criteria in all_criteria:
            if criteria.name == criteria_name:
                return criteria
        raise KeyError(
            f"Criteria '{criteria_name}' not found for participant num {participant_num.value}"
        )
