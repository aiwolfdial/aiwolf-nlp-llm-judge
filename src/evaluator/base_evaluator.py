from abc import ABC, abstractmethod
from pathlib import Path

from models.game import GameInfo
from models.evaluation import (
    EvaluationResult,
    EvaluationConfig,
    EvaluationRanking,
    CriteriaCategory,
)


class BaseEvaluator(ABC):
    """評価器の基底クラス"""

    def __init__(self, config: EvaluationConfig):
        """評価器を初期化

        Args:
            config: 評価設定
        """
        self.config = config

    @abstractmethod
    def evaluate(self, csv_path: Path, game_info: GameInfo) -> EvaluationResult:
        """CSVファイルを評価

        Args:
            csv_path: 評価対象のCSVファイルパス
            game_info: ゲーム情報

        Returns:
            EvaluationResult: 評価結果
        """
        pass

    def _create_evaluation_result(
        self,
        game_info: GameInfo,
        rankings: dict[str, EvaluationRanking],
        evaluation_targets: list[str],
    ) -> EvaluationResult:
        """評価結果オブジェクトを作成

        Args:
            game_info: ゲーム情報
            rankings: 評価ランキング辞書（基準名: ランキング）
            evaluation_targets: 評価対象のIDリスト

        Returns:
            EvaluationResult: 作成された評価結果
        """
        # 該当プレイヤー数の全評価基準を取得
        all_criteria = self.config.get_criteria_for_game(game_info.player_count)

        common_rankings = {}
        specific_rankings = {}

        # 共通基準と固有基準を分離
        for criteria in all_criteria:
            if criteria.name not in rankings:
                raise ValueError(f"Missing ranking for criteria: {criteria.name}")

            ranking = rankings[criteria.name]

            if criteria.category == CriteriaCategory.COMMON:
                common_rankings[criteria.name] = ranking
            else:
                specific_rankings[criteria.name] = ranking

        return EvaluationResult(
            game_info=game_info,
            common_rankings=common_rankings,
            specific_rankings=specific_rankings,
            evaluation_targets=evaluation_targets,
        )

    def _validate_rankings(
        self,
        rankings: dict[str, EvaluationRanking],
        game_info: GameInfo,
        evaluation_targets: list[str],
    ) -> None:
        """ランキングの妥当性をチェック

        Args:
            rankings: 評価ランキング辞書
            game_info: ゲーム情報
            evaluation_targets: 評価対象のIDリスト

        Raises:
            ValueError: ランキングが不正な場合
        """
        expected_criteria = self.config.get_criteria_for_game(game_info.player_count)
        expected_names = {c.name for c in expected_criteria}

        # 不足している基準をチェック
        missing_criteria = expected_names - set(rankings.keys())
        if missing_criteria:
            raise ValueError(f"Missing rankings for criteria: {missing_criteria}")

        # 余分な基準をチェック
        extra_criteria = set(rankings.keys()) - expected_names
        if extra_criteria:
            raise ValueError(f"Unexpected criteria in rankings: {extra_criteria}")

        # 各ランキングの整合性チェック
        for criteria_name, ranking in rankings.items():
            # ランキングに全ての評価対象が含まれているか
            if set(ranking.rankings) != set(evaluation_targets):
                raise ValueError(
                    f"Ranking for '{criteria_name}' does not contain all evaluation targets"
                )
