from dataclasses import dataclass
from typing import Union, Literal, Dict, List
from enum import Enum


class GameFormat(Enum):
    """ゲーム形式を表す列挙型"""
    FIVE_PLAYER = "5_player"
    THIRTEEN_PLAYER = "13_player"


@dataclass
class EvaluationCriteria:
    """評価基準を表すデータクラス"""
    name: str
    description: str
    min_value: Union[int, float]
    max_value: Union[int, float]
    score_type: Literal["integer", "float"]


@dataclass
class EvaluationScore:
    """個別評価スコアを表すデータクラス"""
    criteria_name: str
    value: Union[int, float]
    min_value: Union[int, float]
    max_value: Union[int, float]
    score_type: Literal["integer", "float"]

    def __post_init__(self):
        """値の範囲チェックと型チェック"""
        if self.score_type == "integer" and not isinstance(self.value, int):
            raise TypeError(f"Score type is integer but value is {type(self.value)}")
        
        if self.score_type == "float" and not isinstance(self.value, (int, float)):
            raise TypeError(f"Score type is float but value is {type(self.value)}")
        
        if not (self.min_value <= self.value <= self.max_value):
            raise ValueError(f"Score {self.value} is out of range [{self.min_value}, {self.max_value}]")


@dataclass
class GameInfo:
    """ゲーム情報を表すデータクラス"""
    format: GameFormat
    player_count: int
    game_id: str = ""


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


@dataclass
class EvaluationConfig:
    """評価設定を表すデータクラス"""
    common_criteria: List[EvaluationCriteria]
    game_specific_criteria: Dict[GameFormat, List[EvaluationCriteria]]
    
    def get_criteria_for_game(self, game_format: GameFormat) -> List[EvaluationCriteria]:
        """指定されたゲーム形式の全評価基準を取得"""
        criteria = self.common_criteria.copy()
        if game_format in self.game_specific_criteria:
            criteria.extend(self.game_specific_criteria[game_format])
        return criteria
    
    def get_criteria_by_name(self, criteria_name: str, game_format: GameFormat) -> EvaluationCriteria:
        """基準名で評価基準を取得"""
        all_criteria = self.get_criteria_for_game(game_format)
        for criteria in all_criteria:
            if criteria.name == criteria_name:
                return criteria
        raise KeyError(f"Criteria '{criteria_name}' not found for game format {game_format.value}")