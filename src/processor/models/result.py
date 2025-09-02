"""処理結果を管理するデータクラス."""

from dataclasses import dataclass


@dataclass
class ProcessingResult:
    """処理結果を表すデータクラス

    Attributes:
        total: 処理対象の総数
        completed: 正常完了した数
        failed: 失敗した数
        evaluation_results: 成功した評価結果のリスト
    """

    total: int = 0
    completed: int = 0
    failed: int = 0
    evaluation_results: list[dict] = None

    def __post_init__(self):
        """初期化後の処理"""
        if self.evaluation_results is None:
            self.evaluation_results = []

    @property
    def success_rate(self) -> float:
        """成功率を計算

        Returns:
            成功率（0.0-1.0）
        """
        return self.completed / self.total if self.total > 0 else 0.0
