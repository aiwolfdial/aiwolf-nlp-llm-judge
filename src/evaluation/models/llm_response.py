"""LLMレスポンス関連のデータモデル."""

from typing import Self
from pydantic import BaseModel, Field, model_validator


class EvaluationElement(BaseModel):
    """個々のプレイヤーに対する評価要素."""

    player_name: str = Field(description="評価対象者の名前")
    reasoning: str = Field(description="各評価対象に対する順位付けの理由")
    ranking: int = Field(
        description="評価対象者の順位(他のプレイヤーとの重複はなし)", ge=1
    )


class EvaluationLLMResponse(BaseModel):
    """LLMからの評価レスポンス全体."""

    rankings: list[EvaluationElement] = Field(description="各プレイヤーに対する評価")

    @model_validator(mode="after")
    def validate_rankings_consistency(self) -> Self:
        """ランキングの整合性を検証（空チェック含む）"""
        # 空のランキングリストの検証
        if not self.rankings:
            raise ValueError("ランキングリストは空にできません")

        # ランキング値の重複チェック
        ranking_values = [elem.ranking for elem in self.rankings]
        if len(ranking_values) != len(set(ranking_values)):
            raise ValueError("ランキング値に重複があります")

        # ランキング値が連続した整数（1, 2, 3, ...）であることを検証
        expected_rankings = set(range(1, len(self.rankings) + 1))
        actual_rankings = set(ranking_values)
        if actual_rankings != expected_rankings:
            raise ValueError(
                f"ランキングは1から{len(self.rankings)}までの連続した整数である必要があります。"
                f"実際: {sorted(actual_rankings)}, 期待: {sorted(expected_rankings)}"
            )

        return self

    @classmethod
    def create_with_validation(
        cls,
        rankings: list[EvaluationElement],
        player_count: int,
        valid_player_names: set[str],
    ) -> Self:
        """バリデーション付きでインスタンスを作成

        Args:
            rankings: ランキングデータ
            player_count: 期待するプレイヤー数
            valid_player_names: 有効なプレイヤー名のセット

        Returns:
            検証済みのEvaluationLLMResponseインスタンス

        Raises:
            ValueError: バリデーションに失敗した場合
        """
        # プレイヤー数の検証
        if len(rankings) != player_count:
            raise ValueError(
                f"ランキング数（{len(rankings)}）がプレイヤー数（{player_count}）と一致しません"
            )

        # プレイヤー名の検証
        response_player_names = {elem.player_name for elem in rankings}
        invalid_names = response_player_names - valid_player_names
        if invalid_names:
            raise ValueError(
                f"無効なプレイヤー名が含まれています: {invalid_names}. "
                f"有効な名前: {valid_player_names}"
            )

        missing_names = valid_player_names - response_player_names
        if missing_names:
            raise ValueError(f"不足しているプレイヤー名があります: {missing_names}")

        # 基本的なPydanticバリデーションを実行
        return cls(rankings=rankings)

    def __iter__(self):
        """リストのように反復処理可能にする."""
        return iter(self.rankings)

    def __len__(self):
        """リストのようにlen()を使用可能にする."""
        return len(self.rankings)

    def __getitem__(self, index):
        """リストのようにインデックスアクセス可能にする."""
        return self.rankings[index]
