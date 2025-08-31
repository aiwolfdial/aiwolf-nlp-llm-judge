"""LLMレスポンス関連のデータモデル"""

from pydantic import BaseModel, Field


class EvaluationElement(BaseModel):
    """個々のプレイヤーに対する評価要素"""

    player_name: str = Field(description="評価対象者の名前")
    reasoning: str = Field(description="各評価対象に対する順位付けの理由")
    ranking: int = Field(description="評価対象者の順位(他のプレイヤーとの重複はなし)")


class EvaluationLLMResponse(BaseModel):
    """LLMからの評価レスポンス全体"""

    rankings: list[EvaluationElement] = Field(description="各プレイヤーに対する評価")

    def __iter__(self):
        """リストのように反復処理可能にする"""
        return iter(self.rankings)

    def __len__(self):
        """リストのようにlen()を使用可能にする"""
        return len(self.rankings)

    def __getitem__(self, index):
        """リストのようにインデックスアクセス可能にする"""
        return self.rankings[index]
