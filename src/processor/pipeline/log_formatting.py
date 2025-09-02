"""ログフォーマット・キャラクター情報処理サービス."""

import logging
from typing import Any

from src.aiwolf_log.game_log import AIWolfGameLog
from src.game.models import GameInfo
from src.llm.formatter import GameLogFormatter
from src.processor.models.exceptions import GameLogProcessingError

logger = logging.getLogger(__name__)


class LogFormattingService:
    """ログフォーマット・キャラクター情報処理を担当するサービス

    責任:
    - ゲームログのJSONL形式変換
    - キャラクター情報の取得・整形
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """初期化

        Args:
            config: アプリケーション設定辞書
        """
        self.config = config

    def format_game_log(
        self, game_log: AIWolfGameLog, game_info: GameInfo
    ) -> list[dict[str, Any]]:
        """ゲームログをフォーマット変換

        Args:
            game_log: ゲームログ
            game_info: ゲーム情報

        Returns:
            フォーマット済みのログデータリスト

        Raises:
            GameLogProcessingError: フォーマット変換に失敗した場合
        """
        try:
            formatter = GameLogFormatter(game_log, self.config, parser=None)
            formatted_data = formatter.convert_to_jsonl(game_info.game_format)
            logger.debug(f"Formatted {len(formatted_data)} log entries")
            return formatted_data
        except Exception as e:
            raise GameLogProcessingError(f"Failed to format game log: {e}") from e

    def get_character_info(self, game_log: AIWolfGameLog) -> str:
        """キャラクター情報を取得してフォーマット

        Args:
            game_log: ゲームログ

        Returns:
            フォーマット済みのキャラクター情報文字列
        """
        try:
            json_reader = game_log.get_json_reader()
            profiles = json_reader.get_initialize_profiles()

            if not profiles:
                logger.warning(
                    f"No character profiles found for game: {game_log.game_id}"
                )
                return ""

            character_lines = [
                f"- {agent_name}: {profile}" for agent_name, profile in profiles.items()
            ]
            return "\n".join(character_lines)

        except Exception as e:
            logger.warning(
                f"Failed to get character info for game {game_log.game_id}: {e}"
            )
            return ""
