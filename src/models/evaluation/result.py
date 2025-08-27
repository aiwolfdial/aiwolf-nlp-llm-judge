from dataclasses import dataclass
from typing import Dict

from models.game import GameInfo
from models.evaluation.criteria import EvaluationScore


@dataclass
class EvaluationResult:
    """評価結果全体を表すデータクラス"""

    game_info: GameInfo
    common_scores: Dict[str, EvaluationScore]
    specific_scores: Dict[str, EvaluationScore]

    def get_all_scores(self) -> Dict[str, EvaluationScore]:
        """全ての評価スコアを取得"""
        return {**self.common_scores, **self.specific_scores}

    def get_score_by_name(self, criteria_name: str) -> EvaluationScore:
        """基準名で評価スコアを取得"""
        all_scores = self.get_all_scores()
        if criteria_name not in all_scores:
            raise KeyError(f"Criteria '{criteria_name}' not found in evaluation result")
        return all_scores[criteria_name]
