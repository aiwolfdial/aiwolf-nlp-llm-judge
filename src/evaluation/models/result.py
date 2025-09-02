from typing import Self, Optional
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


class CriteriaEvaluationResult(list[EvaluationResultElement]):
    """単一の評価基準に対する結果を表すクラス."""

    def __init__(
        self,
        criteria_name: str,
        elements: Optional[list[EvaluationResultElement]] = None,
    ):
        """初期化

        Args:
            criteria_name: 評価基準名
            elements: 評価結果要素のリスト
        """
        super().__init__(elements or [])
        self.criteria_name = criteria_name

    @classmethod
    def from_llm_response(
        cls,
        criteria_name: str,
        llm_response: EvaluationLLMResponse,
        agent_to_team_mapping: dict[str, str],
    ) -> Self:
        """LLMレスポンスから評価結果を作成

        Args:
            criteria_name: 評価基準名
            llm_response: LLMからの評価レスポンス
            agent_to_team_mapping: エージェント名→チーム名のマッピング

        Returns:
            評価結果
        """
        result_elements = []
        for element in llm_response.rankings:
            team = agent_to_team_mapping.get(element.player_name, "unknown")
            result_element = EvaluationResultElement.from_evaluation_element(
                element, team
            )
            result_elements.append(result_element)

        return cls(criteria_name=criteria_name, elements=result_elements)


class EvaluationResult(list[CriteriaEvaluationResult]):
    """全評価基準の結果を管理するクラス（リストを継承）."""

    def append(self, criteria_result: CriteriaEvaluationResult) -> None:
        """評価結果を追加（重複チェック付き）

        Args:
            criteria_result: 追加する評価結果

        Raises:
            ValueError: 同一のcriteria_nameが既に存在する場合
        """
        if self.get_result_by_criteria_name(criteria_result.criteria_name) is not None:
            raise ValueError(
                f"Criteria '{criteria_result.criteria_name}' already exists in EvaluationResult"
            )
        super().append(criteria_result)

    def add_result(self, criteria_result: CriteriaEvaluationResult) -> None:
        """評価結果を安全に追加（appendのエイリアス）

        Args:
            criteria_result: 追加する評価結果

        Raises:
            ValueError: 同一のcriteria_nameが既に存在する場合
        """
        self.append(criteria_result)

    def get_result_by_criteria_name(
        self, criteria_name: str
    ) -> Optional[CriteriaEvaluationResult]:
        """指定された評価基準名の結果を取得

        Args:
            criteria_name: 評価基準名

        Returns:
            該当する評価結果、見つからない場合はNone
        """
        for result in self:
            if result.criteria_name == criteria_name:
                return result
        return None

    def get_criteria_names(self) -> list[str]:
        """全ての評価基準名を取得

        Returns:
            評価基準名のリスト
        """
        return [result.criteria_name for result in self]
