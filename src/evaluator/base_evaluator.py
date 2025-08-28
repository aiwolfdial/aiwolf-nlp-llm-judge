from abc import ABC, abstractmethod
from pathlib import Path

from models.game import GameInfo
from models.evaluation import (
    EvaluationResult,
    EvaluationConfig,
    EvaluationScore,
    ScoreType,
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
        self, game_info: GameInfo, scores: dict[str, float]
    ) -> EvaluationResult:
        """評価結果オブジェクトを作成

        Args:
            game_info: ゲーム情報
            scores: 評価スコア辞書（基準名: スコア値）

        Returns:
            EvaluationResult: 作成された評価結果
        """
        # 該当参加人数の全評価基準を取得
        all_criteria = self.config.get_criteria_for_game(game_info.participant_num)

        common_scores = {}
        specific_scores = {}

        # 共通基準と固有基準を分離
        # 全ゲーム形式に適用される基準を共通基準とする
        from models.game import ParticipantNum

        all_games = [ParticipantNum.FIVE_PLAYER, ParticipantNum.THIRTEEN_PLAYER]
        common_criteria_names = {
            c.name
            for c in self.config
            if all(game in c.applicable_games for game in all_games)
        }

        for criteria in all_criteria:
            if criteria.name not in scores:
                raise ValueError(f"Missing score for criteria: {criteria.name}")

            score_value = scores[criteria.name]

            # 型変換
            if criteria.score_type == ScoreType.INT:
                score_value = int(score_value)
            else:
                score_value = float(score_value)

            evaluation_score = EvaluationScore(
                criteria_name=criteria.name,
                value=score_value,
                min_value=criteria.min_value,
                max_value=criteria.max_value,
                score_type=criteria.score_type,
            )

            if criteria.name in common_criteria_names:
                common_scores[criteria.name] = evaluation_score
            else:
                specific_scores[criteria.name] = evaluation_score

        return EvaluationResult(
            game_info=game_info,
            common_scores=common_scores,
            specific_scores=specific_scores,
        )

    def _validate_scores(self, scores: dict[str, float], game_info: GameInfo) -> None:
        """スコアの妥当性をチェック

        Args:
            scores: 評価スコア辞書
            game_info: ゲーム情報

        Raises:
            ValueError: スコアが不正な場合
        """
        expected_criteria = self.config.get_criteria_for_game(game_info.participant_num)
        expected_names = {c.name for c in expected_criteria}

        # 不足している基準をチェック
        missing_criteria = expected_names - set(scores.keys())
        if missing_criteria:
            raise ValueError(f"Missing scores for criteria: {missing_criteria}")

        # 余分な基準をチェック
        extra_criteria = set(scores.keys()) - expected_names
        if extra_criteria:
            raise ValueError(f"Unexpected criteria in scores: {extra_criteria}")

        # スコア値の範囲チェック
        for criteria in expected_criteria:
            score_value = scores[criteria.name]
            if not (criteria.min_value <= score_value <= criteria.max_value):
                raise ValueError(
                    f"Score for '{criteria.name}' ({score_value}) is out of range "
                    f"[{criteria.min_value}, {criteria.max_value}]"
                )
