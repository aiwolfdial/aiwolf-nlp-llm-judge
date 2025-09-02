from typing import Self
from pydantic import BaseModel, Field
from src.evaluation.models.llm_response import EvaluationLLMResponse, EvaluationElement


class EvaluationResultElement(BaseModel):
    """チーム情報を含む評価結果要素."""

    player_name: str = Field(description="評価対象者の名前")
    reasoning: str = Field(description="各評価対象に対する順位付けの理由")
    ranking: int = Field(description="評価対象者の順位(他のプレイヤーとの重複はなし)")
    team: str = Field(description="プレイヤーの所属チーム名")

    @classmethod
    def from_evaluation_element(cls, element: EvaluationElement, team: str) -> Self:
        """EvaluationElementからチーム情報付きの結果要素を作成

        Args:
            element: LLMからの評価要素
            team: チーム名

        Returns:
            チーム情報付きの評価結果要素
        """
        return cls(
            player_name=element.player_name,
            reasoning=element.reasoning,
            ranking=element.ranking,
            team=team,
        )


class EvaluationResult(list[EvaluationLLMResponse]):
    """評価結果全体を表すクラス（EvaluationLLMResponseのリストを継承）."""

    def __init__(self):
        super().__init__()
        self._criteria_index: dict[str, int] = {}  # criteria_name -> index

    def add_response(self, criteria_name: str, response: EvaluationLLMResponse) -> None:
        """評価レスポンスを追加."""
        if criteria_name in self._criteria_index:
            # 既存の基準を更新
            index = self._criteria_index[criteria_name]
            self[index] = response
        else:
            # 新しい基準を追加
            self.append(response)
            self._criteria_index[criteria_name] = len(self) - 1

    def get_by_criteria(self, criteria_name: str) -> EvaluationLLMResponse:
        """評価基準名でレスポンスを取得."""
        if criteria_name not in self._criteria_index:
            raise KeyError(f"Criteria '{criteria_name}' not found")
        index = self._criteria_index[criteria_name]
        return self[index]

    def get_by_criteria_with_team(
        self, criteria_name: str, agent_to_team_mapping: dict[str, str]
    ) -> list[EvaluationResultElement]:
        """評価基準名でチーム情報付きレスポンスを取得."""
        llm_response = self.get_by_criteria(criteria_name)
        result_elements = []
        for element in llm_response.rankings:
            team = agent_to_team_mapping.get(element.player_name, "unknown")
            result_element = EvaluationResultElement.from_evaluation_element(
                element, team
            )
            result_elements.append(result_element)
        return result_elements

    def get_all_criteria_names(self) -> list[str]:
        """すべての評価基準名を取得."""
        return list(self._criteria_index.keys())

    def has_criteria(self, criteria_name: str) -> bool:
        """指定した評価基準が存在するか確認."""
        return criteria_name in self._criteria_index
