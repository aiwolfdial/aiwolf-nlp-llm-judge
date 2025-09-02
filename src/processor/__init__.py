"""AIWolf ゲームログのバッチ処理システム（モジュラー・モノリス構造）

このモジュールは、AIWolfのゲームログを並列処理で評価するためのシステムを提供します。
プロセス間並列処理とスレッド並列処理を組み合わせて効率的な処理を実現します。

モジュラー・モノリス構造により、責任別にサービスが分離され、保守性が向上しています。
"""

from .batch_processor import BatchProcessor
from .game_processor import GameProcessor
from .models import (
    ConfigurationError,
    EvaluationExecutionError,
    GameLogProcessingError,
    ProcessingConfig,
    ProcessingError,
    ProcessingResult,
)

__all__ = [
    "BatchProcessor",
    "GameProcessor",
    "ProcessingConfig",
    "ProcessingResult",
    "ProcessingError",
    "GameLogProcessingError",
    "EvaluationExecutionError",
    "ConfigurationError",
]
