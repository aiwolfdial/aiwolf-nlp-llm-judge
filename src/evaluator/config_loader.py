import yaml
from pathlib import Path

from src.models.evaluation import (
    EvaluationConfig,
    EvaluationCriteria,
    RankingType,
    CriteriaCategory,
)
from src.models.game import GameFormat


class ConfigLoader:
    """評価設定ファイルを読み込むクラス."""

    @staticmethod
    def load_player_count(settings_path: Path) -> int:
        """settings.yamlからプレイヤー数を読み込む.

        Args:
            settings_path: settings.yamlファイルのパス

        Returns:
            int: 読み込まれたプレイヤー数

        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            ValueError: 設定ファイルの形式が不正な場合
        """
        if not settings_path.exists():
            raise FileNotFoundError(f"Settings file not found: {settings_path}")

        try:
            with settings_path.open("r", encoding="utf-8") as f:
                settings_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format in settings: {e}")

        # プレイヤー数設定を取得
        player_count = settings_data.get("game", {}).get("player_count", 5)

        if not isinstance(player_count, int) or player_count <= 0:
            raise ValueError(f"Invalid player count: {player_count}")

        return player_count

    @staticmethod
    def load_game_format(settings_path: Path) -> GameFormat:
        """settings.yamlからゲーム形式設定を読み込む.

        Args:
            settings_path: settings.yamlファイルのパス

        Returns:
            GameFormat: 読み込まれたゲーム形式

        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            ValueError: 設定ファイルの形式が不正な場合
        """
        if not settings_path.exists():
            raise FileNotFoundError(f"Settings file not found: {settings_path}")

        try:
            with settings_path.open("r", encoding="utf-8") as f:
                settings_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format in settings: {e}")

        # ゲーム形式設定を取得
        game_format_str = settings_data.get("game", {}).get("format", "main_match")

        try:
            return GameFormat(game_format_str)
        except ValueError:
            raise ValueError(f"Unknown game format: {game_format_str}")

    @staticmethod
    def load_from_settings(settings_path: Path) -> EvaluationConfig:
        """settings.yamlから評価設定を読み込む.

        Args:
            settings_path: settings.yamlファイルのパス

        Returns:
            EvaluationConfig: 読み込まれた評価設定

        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            ValueError: 設定ファイルの形式が不正な場合
        """
        if not settings_path.exists():
            raise FileNotFoundError(f"Settings file not found: {settings_path}")

        try:
            with settings_path.open("r", encoding="utf-8") as f:
                settings_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format in settings: {e}")

        # evaluation_criteria のパスを取得
        evaluation_criteria_path = settings_data.get("path", {}).get(
            "evaluation_criteria"
        )
        if not evaluation_criteria_path:
            raise ValueError("evaluation_criteria path not found in settings")

        # 相対パスの場合、プロジェクトルートからの相対パスとして解釈
        if Path(evaluation_criteria_path).is_absolute():
            criteria_path = Path(evaluation_criteria_path)
        else:
            # プロジェクトルートを取得（settings.yamlの親の親ディレクトリ）
            project_root = settings_path.parent.parent
            criteria_path = project_root / evaluation_criteria_path

        return ConfigLoader.load_evaluation_config(criteria_path)

    @staticmethod
    def load_evaluation_config(config_path: Path) -> EvaluationConfig:
        """評価設定ファイルを読み込んでEvaluationConfigオブジェクトを作成.

        Args:
            config_path: 設定ファイルのパス

        Returns:
            EvaluationConfig: 読み込まれた評価設定

        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            ValueError: 設定ファイルの形式が不正な場合
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with config_path.open("r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")

        # 全評価基準を統合したリストを作成
        all_criteria = []

        # 共通評価基準の読み込み
        common_criteria_data = config_data.get("common_criteria", [])
        for criteria_dict in common_criteria_data:
            criteria = ConfigLoader._load_criteria_dict(
                criteria_dict,
                [5, 13],  # 全プレイヤー数に適用
                CriteriaCategory.COMMON,
            )
            all_criteria.append(criteria)

        # ゲーム固有評価基準の読み込み
        specific_data = config_data.get("game_specific_criteria", {})

        for player_count_str, criteria_list in specific_data.items():
            try:
                player_count = int(player_count_str.rstrip("_player"))
                for criteria_dict in criteria_list:
                    criteria = ConfigLoader._load_criteria_dict(
                        criteria_dict, [player_count], CriteriaCategory.GAME_SPECIFIC
                    )
                    all_criteria.append(criteria)
            except ValueError:
                raise ValueError(f"Invalid player count format: {player_count_str}")

        return EvaluationConfig(all_criteria)

    @staticmethod
    def _load_criteria_dict(
        criteria_dict: dict, applicable_games: list[int], category: CriteriaCategory
    ) -> EvaluationCriteria:
        """評価基準辞書を読み込んでEvaluationCriteriaオブジェクトを作成.

        Args:
            criteria_dict: YAML から読み込まれた評価基準データ
            applicable_games: この基準が適用されるプレイヤー数のリスト
            category: 評価基準のカテゴリー

        Returns:
            EvaluationCriteria: 評価基準オブジェクト

        Raises:
            ValueError: 設定データが不正な場合
        """
        try:
            name = criteria_dict["name"]
            description = criteria_dict["description"]
            ranking_type = criteria_dict["ranking_type"]

            # 文字列をRankingType enumに変換
            if ranking_type == "ordinal":
                ranking_type_enum = RankingType.ORDINAL
            elif ranking_type == "comparative":
                ranking_type_enum = RankingType.COMPARATIVE
            else:
                raise ValueError(f"Invalid ranking type: {ranking_type}")

            return EvaluationCriteria(
                name=name,
                description=description,
                ranking_type=ranking_type_enum,
                applicable_games=applicable_games,
                category=category,
            )

        except KeyError as e:
            raise ValueError(f"Missing required field in criteria: {e}")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid criteria data: {e}")
