"""処理結果を管理するデータクラス."""

from dataclasses import dataclass


@dataclass
class ProcessingResult:
    """処理結果を表すデータクラス

    Attributes:
        total: 処理対象の総数
        completed: 正常完了した数
        failed: 失敗した数
    """

    total: int = 0
    completed: int = 0
    failed: int = 0

    @property
    def success_rate(self) -> float:
        """成功率を計算

        Returns:
            成功率（0.0-1.0）
        """
        return self.completed / self.total if self.total > 0 else 0.0
