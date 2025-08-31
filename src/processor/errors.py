"""処理に関する例外クラス群."""


class ProcessingError(Exception):
    """処理エラーの基底クラス"""

    pass


class GameLogProcessingError(ProcessingError):
    """ゲームログ処理に関するエラー"""

    pass


class EvaluationExecutionError(ProcessingError):
    """評価実行に関するエラー"""

    pass


class ConfigurationError(ProcessingError):
    """設定に関するエラー"""

    pass
