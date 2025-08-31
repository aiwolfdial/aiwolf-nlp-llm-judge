from dataclasses import dataclass
from pydantic import BaseModel, Field

from models.game import GameInfo
from models.evaluation.criteria import EvaluationRanking


class EvaluationLLMResponse(BaseModel):
    rankings: list[str] = Field(description="評価対象のIDのリスト（評価の高い順）")
    reasoning: dict[str, str] = Field(description="各評価対象に対する順位付けの理由")


@dataclass
class EvaluationResult:
    """評価結果全体を表すデータクラス"""

    game_info: GameInfo
    common_rankings: dict[str, EvaluationRanking]
    specific_rankings: dict[str, EvaluationRanking]
    evaluation_targets: list[str]  # 評価対象のIDリスト

    def get_all_rankings(self) -> dict[str, EvaluationRanking]:
        """全ての評価ランキングを取得"""
        return {**self.common_rankings, **self.specific_rankings}

    def get_ranking_by_name(self, criteria_name: str) -> EvaluationRanking:
        """基準名で評価ランキングを取得"""
        all_rankings = self.get_all_rankings()
        if criteria_name not in all_rankings:
            raise KeyError(f"Criteria '{criteria_name}' not found in evaluation result")
        return all_rankings[criteria_name]
