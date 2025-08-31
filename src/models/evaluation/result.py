from .llm_response import EvaluationLLMResponse


class EvaluationResult(list[EvaluationLLMResponse]):
    """評価結果全体を表すクラス（EvaluationLLMResponseのリストを継承）"""

    def __init__(self):
        super().__init__()
        self._criteria_index: dict[str, int] = {}  # criteria_name -> index

    def add_response(self, criteria_name: str, response: EvaluationLLMResponse) -> None:
        """評価レスポンスを追加"""
        if criteria_name in self._criteria_index:
            # 既存の基準を更新
            index = self._criteria_index[criteria_name]
            self[index] = response
        else:
            # 新しい基準を追加
            self.append(response)
            self._criteria_index[criteria_name] = len(self) - 1

    def get_by_criteria(self, criteria_name: str) -> EvaluationLLMResponse:
        """評価基準名でレスポンスを取得"""
        if criteria_name not in self._criteria_index:
            raise KeyError(f"Criteria '{criteria_name}' not found")
        index = self._criteria_index[criteria_name]
        return self[index]

    def get_all_criteria_names(self) -> list[str]:
        """すべての評価基準名を取得"""
        return list(self._criteria_index.keys())

    def has_criteria(self, criteria_name: str) -> bool:
        """指定した評価基準が存在するか確認"""
        return criteria_name in self._criteria_index
