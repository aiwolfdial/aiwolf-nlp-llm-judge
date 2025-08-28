from models.game import ParticipantNum
from models.evaluation.criteria import EvaluationCriteria


class EvaluationConfig(list[EvaluationCriteria]):
    """評価設定を表すクラス（EvaluationCriteriaのリストを継承）"""

    def get_criteria_for_game(
        self, participant_num: ParticipantNum
    ) -> list[EvaluationCriteria]:
        """指定された参加人数の評価基準を取得"""
        return [
            criteria
            for criteria in self
            if participant_num in criteria.applicable_games
        ]

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
