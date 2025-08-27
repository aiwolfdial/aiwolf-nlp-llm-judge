from dataclasses import dataclass
from enum import Enum


class ScoreType(Enum):
    """評価スコアの型を表す列挙型"""

    INT = "int"
    FLOAT = "float"


@dataclass
class EvaluationCriteria:
    """評価基準を表すデータクラス"""

    name: str
    description: str
    min_value: int | float
    max_value: int | float
    score_type: ScoreType


@dataclass
class EvaluationScore:
    """個別評価スコアを表すデータクラス"""

    criteria_name: str
    value: int | float
    min_value: int | float
    max_value: int | float
    score_type: ScoreType

    def __post_init__(self):
        """値の範囲チェックと型チェック"""
        if self.score_type == ScoreType.INT and not isinstance(self.value, int):
            raise TypeError(
                f"Score type is {self.score_type.value} but value is {type(self.value)}"
            )

        if self.score_type == ScoreType.FLOAT and not isinstance(
            self.value, (int, float)
        ):
            raise TypeError(
                f"Score type is {self.score_type.value} but value is {type(self.value)}"
            )

        if not (self.min_value <= self.value <= self.max_value):
            raise ValueError(
                f"Score {self.value} is out of range [{self.min_value}, {self.max_value}]"
            )
