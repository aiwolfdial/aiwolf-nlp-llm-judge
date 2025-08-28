import yaml
from pathlib import Path

from models.evaluation import EvaluationConfig, EvaluationCriteria, ScoreType
from models.game import ParticipantNum, GameFormat


class ConfigLoader:
    """評価設定ファイルを読み込むクラス"""

    @staticmethod
    def load_participant_num(settings_path: Path) -> ParticipantNum:
        """settings.yamlから対戦人数設定を読み込む

        Args:
            settings_path: settings.yamlファイルのパス

        Returns:
            ParticipantNum: 読み込まれた対戦人数

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

        # 対戦人数設定を取得
        participant_num_str = settings_data.get("game", {}).get(
            "participant_num", "5_player"
        )

        try:
            return ParticipantNum(participant_num_str)
        except ValueError:
            raise ValueError(f"Unknown participant number: {participant_num_str}")

    @staticmethod
    def load_game_format(settings_path: Path) -> GameFormat:
        """settings.yamlからゲーム形式設定を読み込む

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
        """settings.yamlから評価設定を読み込む

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

        # 相対パスの場合、settings.yamlからの相対パスとして解釈
        criteria_path = settings_path.parent / evaluation_criteria_path

        return ConfigLoader.load_evaluation_config(criteria_path)

    @staticmethod
    def load_evaluation_config(config_path: Path) -> EvaluationConfig:
        """評価設定ファイルを読み込んでEvaluationConfigオブジェクトを作成

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
                [ParticipantNum.FIVE_PLAYER, ParticipantNum.THIRTEEN_PLAYER],
            )
            all_criteria.append(criteria)

        # ゲーム固有評価基準の読み込み
        specific_data = config_data.get("game_specific_criteria", {})

        for participant_num_str, criteria_list in specific_data.items():
            try:
                participant_num = ParticipantNum(participant_num_str)
                for criteria_dict in criteria_list:
                    criteria = ConfigLoader._load_criteria_dict(
                        criteria_dict, [participant_num]
                    )
                    all_criteria.append(criteria)
            except ValueError:
                raise ValueError(
                    f"Unknown participant number format: {participant_num_str}"
                )

        return EvaluationConfig(all_criteria)

    @staticmethod
    def _load_criteria_dict(
        criteria_dict: dict, applicable_games: list[ParticipantNum]
    ) -> EvaluationCriteria:
        """評価基準辞書を読み込んでEvaluationCriteriaオブジェクトを作成

        Args:
            criteria_dict: YAML から読み込まれた評価基準データ
            applicable_games: この基準が適用されるゲーム形式のリスト

        Returns:
            EvaluationCriteria: 評価基準オブジェクト

        Raises:
            ValueError: 設定データが不正な場合
        """
        try:
            name = criteria_dict["name"]
            description = criteria_dict["description"]
            scale = criteria_dict["scale"]

            min_value = scale["min"]
            max_value = scale["max"]
            score_type = scale["type"]

            # 文字列をScoreType enumに変換
            if score_type == "integer" or score_type == "int":
                score_type_enum = ScoreType.INT
            elif score_type == "float":
                score_type_enum = ScoreType.FLOAT
            else:
                raise ValueError(f"Invalid score type: {score_type}")

            return EvaluationCriteria(
                name=name,
                description=description,
                min_value=min_value,
                max_value=max_value,
                score_type=score_type_enum,
                applicable_games=applicable_games,
            )

        except KeyError as e:
            raise ValueError(f"Missing required field in criteria: {e}")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid criteria data: {e}")
