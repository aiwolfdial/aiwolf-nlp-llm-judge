from dataclasses import dataclass
from enum import Enum


class RankingType(Enum):
    """ランキングの型を表す列挙型."""

    ORDINAL = "ordinal"  # 順序付け（1位、2位...）
    COMPARATIVE = "comparative"  # 比較ベース（A > B > C）


class CriteriaCategory(Enum):
    """評価基準のカテゴリーを表す列挙型."""

    COMMON = "common"  # 全ゲーム形式共通
    GAME_SPECIFIC = "game_specific"  # ゲーム形式固有


@dataclass
class EvaluationCriteria:
    """評価基準を表すデータクラス."""

    name: str
    description: str
    ranking_type: RankingType
    applicable_games: list[int]
    category: CriteriaCategory
