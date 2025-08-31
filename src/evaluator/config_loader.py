"""評価設定ファイル読み込みクラス

注意: このモジュールは後方互換性のために存在します。
新しいコードでは src.evaluator.loaders モジュール内の各クラスを直接使用してください。
"""

from pathlib import Path

from src.models.evaluation import EvaluationConfig
from src.models.game import GameFormat
from .loaders.criteria_loader import CriteriaLoader
from .loaders.settings_loader import SettingsLoader


class ConfigLoader:
    """評価設定ファイルを読み込むクラス（後方互換性用）."""

    @staticmethod
    def load_player_count(settings_path: Path) -> int:
        """settings.yamlからプレイヤー数を読み込む（後方互換性用）"""
        return SettingsLoader.load_player_count(settings_path)

    @staticmethod
    def load_game_format(settings_path: Path) -> GameFormat:
        """settings.yamlからゲーム形式設定を読み込む（後方互換性用）"""
        return SettingsLoader.load_game_format(settings_path)

    @staticmethod
    def load_from_settings(settings_path: Path) -> EvaluationConfig:
        """settings.yamlから評価設定を読み込む（後方互換性用）"""
        criteria_path = SettingsLoader.get_evaluation_criteria_path(settings_path)
        return CriteriaLoader.load_evaluation_config(criteria_path)

    @staticmethod
    def load_evaluation_config(config_path: Path) -> EvaluationConfig:
        """評価設定ファイルを読み込む（後方互換性用）"""
        return CriteriaLoader.load_evaluation_config(config_path)
