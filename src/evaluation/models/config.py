from src.evaluation.models.criteria import EvaluationCriteria


class EvaluationConfig(list[EvaluationCriteria]):
    """評価設定を表すクラス（EvaluationCriteriaのリストを継承）."""

    def get_criteria_for_game(self, player_count: int) -> list[EvaluationCriteria]:
        """指定されたプレイヤー数の評価基準を取得."""
        return [
            criteria for criteria in self if player_count in criteria.applicable_games
        ]

    def get_criteria_by_name(
        self, criteria_name: str, player_count: int
    ) -> EvaluationCriteria:
        """基準名で評価基準を取得."""
        all_criteria = self.get_criteria_for_game(player_count)
        for criteria in all_criteria:
            if criteria.name == criteria_name:
                return criteria
        raise KeyError(
            f"Criteria '{criteria_name}' not found for player count {player_count}"
        )
