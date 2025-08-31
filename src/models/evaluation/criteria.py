from dataclasses import dataclass
from enum import Enum


class RankingType(Enum):
    """ランキングの型を表す列挙型"""

    ORDINAL = "ordinal"  # 順序付け（1位、2位...）
    COMPARATIVE = "comparative"  # 比較ベース（A > B > C）


class CriteriaCategory(Enum):
    """評価基準のカテゴリーを表す列挙型"""

    COMMON = "common"  # 全ゲーム形式共通
    GAME_SPECIFIC = "game_specific"  # ゲーム形式固有


@dataclass
class EvaluationCriteria:
    """評価基準を表すデータクラス"""

    name: str
    description: str
    ranking_type: RankingType
    applicable_games: list[int]
    category: CriteriaCategory


@dataclass
class EvaluationRanking:
    """個別評価ランキングを表すデータクラス"""

    criteria_name: str
    rankings: list[str]  # 評価対象のIDリスト（高評価順）
    ranking_type: RankingType
    reasoning: dict[str, str]  # 各評価対象に対する理由

    def __post_init__(self):
        """ランキングの整合性チェック"""
        if len(self.rankings) != len(set(self.rankings)):
            raise ValueError("Rankings contain duplicate entries")

        if set(self.rankings) != set(self.reasoning.keys()):
            raise ValueError("Rankings and reasoning keys must match")
