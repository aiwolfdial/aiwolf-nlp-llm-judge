"""Evaluation criteria.yaml 専用ローダー."""

import re
from pathlib import Path

from src.evaluation.models import (
    EvaluationConfig,
    EvaluationCriteria,
    RankingType,
    CriteriaCategory,
)
from src.utils.yaml_loader import YAMLLoader


class CriteriaLoader:
    """evaluation_criteria.yamlファイルの読み込み専用クラス."""

    @staticmethod
    def load_evaluation_config(config_path: Path) -> EvaluationConfig:
        """評価設定ファイルを読み込んでEvaluationConfigオブジェクトを作成

        Args:
            config_path: 設定ファイルのパス

        Returns:
            読み込まれた評価設定

        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            ValueError: 設定ファイルの形式が不正な場合
        """
        config_data = YAMLLoader.load_yaml(config_path)

        # 全評価基準を統合したリストを作成
        all_criteria = []

        # 共通評価基準の読み込み
        common_criteria_data = config_data.get("common_criteria", [])
        common_criteria = CriteriaLoader._load_common_criteria(common_criteria_data)
        all_criteria.extend(common_criteria)

        # ゲーム固有評価基準の読み込み
        specific_data = config_data.get("game_specific_criteria", {})
        specific_criteria = CriteriaLoader._load_specific_criteria(specific_data)
        all_criteria.extend(specific_criteria)

        return EvaluationConfig(all_criteria)

    @staticmethod
    def _load_common_criteria(
        common_criteria_data: list[dict],
    ) -> list[EvaluationCriteria]:
        """共通評価基準を読み込み

        Args:
            common_criteria_data: YAML から読み込まれた共通基準データのリスト

        Returns:
            共通評価基準のリスト
        """
        criteria_list = []
        for criteria_dict in common_criteria_data:
            # applicable_gamesから取得、なければデフォルトの[5, 13]
            applicable_games = criteria_dict.get("applicable_games", [5, 13])
            criteria = CriteriaLoader._load_criteria_dict(
                criteria_dict,
                applicable_games,
                CriteriaCategory.COMMON,
            )
            criteria_list.append(criteria)
        return criteria_list

    @staticmethod
    def _load_specific_criteria(specific_data: dict) -> list[EvaluationCriteria]:
        """ゲーム固有評価基準を読み込み

        Args:
            specific_data: YAML から読み込まれた固有基準データの辞書

        Returns:
            ゲーム固有評価基準のリスト

        Raises:
            ValueError: プレイヤー数の形式が不正な場合
        """
        criteria_list = []

        for player_count_str, criteria_list_data in specific_data.items():
            try:
                # より柔軟なパース（例: "13_player", "13-player", "13"）
                match = re.search(r"(\d+)", player_count_str)
                if not match:
                    raise ValueError(f"No player count found in: {player_count_str}")

                player_count = int(match.group(1))
                for criteria_dict in criteria_list_data:
                    criteria = CriteriaLoader._load_criteria_dict(
                        criteria_dict, [player_count], CriteriaCategory.GAME_SPECIFIC
                    )
                    criteria_list.append(criteria)
            except (ValueError, AttributeError) as e:
                raise ValueError(
                    f"Invalid player count format '{player_count_str}': {e}"
                )

        return criteria_list

    @staticmethod
    def _load_criteria_dict(
        criteria_dict: dict, applicable_games: list[int], category: CriteriaCategory
    ) -> EvaluationCriteria:
        """評価基準辞書を読み込んでEvaluationCriteriaオブジェクトを作成

        Args:
            criteria_dict: YAML から読み込まれた評価基準データ
            applicable_games: この基準が適用されるプレイヤー数のリスト
            category: 評価基準のカテゴリー

        Returns:
            評価基準オブジェクト

        Raises:
            ValueError: 設定データが不正な場合
        """
        try:
            name = criteria_dict["name"]
            description = criteria_dict["description"]
            ranking_type = criteria_dict["ranking_type"]
            order = criteria_dict.get("order", 0)  # デフォルト値0

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
                order=order,
            )

        except KeyError as e:
            raise ValueError(f"Missing required field in criteria: {e}")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid criteria data: {e}")
