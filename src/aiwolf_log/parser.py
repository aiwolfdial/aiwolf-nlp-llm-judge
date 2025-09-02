from __future__ import annotations

from typing import Any

from .csv_schema import CSVColumnIndices


class AIWolfCSVParser:
    """AIWolf CSVファイルのパースを行うクラス."""

    def get_action(self, line: list[str]) -> str:
        """どの行動を意味する行なのか取得.

        Args:
            line: CSV行のデータ（文字列のリスト）

        Returns:
            行動名（文字列）

        Raises:
            TypeError: lineがリストでないか、要素が文字列でない場合
            ValueError: lineが空の場合
        """
        return self._get_element(line, CSVColumnIndices.ACTION)

    def get_day(self, line: list[str]) -> int:
        """日数を取得.

        Args:
            line: CSV行のデータ（文字列のリスト）

        Returns:
            日数（整数）

        Raises:
            TypeError: lineがリストでないか、要素が文字列でない場合
            ValueError: lineが空の場合、または日数が整数に変換できない場合
        """
        day_str = self._get_element(line=line, index=CSVColumnIndices.DAY)
        try:
            return int(day_str)
        except ValueError as e:
            msg = f"Day must be a valid integer, got '{day_str}'"
            raise ValueError(msg) from e

    def _get_element(self, line: list[str], index: int) -> str:
        """指定されたインデックスの要素を取得.

        Args:
            line: CSV行のデータ（文字列のリスト）
            index: 取得したい要素のインデックス

        Returns:
            指定されたインデックスの要素（文字列）

        Raises:
            TypeError: lineがリストでないか、要素が文字列でない場合
            ValueError: lineが空の場合、またはindexが範囲外の場合
        """
        if not isinstance(line, list):
            msg = f"Line must be a list, got {type(line).__name__}"
            raise TypeError(msg)

        if not all(isinstance(elem, str) for elem in line):
            invalid_types = [
                type(elem).__name__ for elem in line if not isinstance(elem, str)
            ]
            msg = f"All elements in line must be strings, found: {', '.join(set(invalid_types))}"
            raise TypeError(msg)

        if len(line) == 0:
            msg = "Line cannot be empty"
            raise ValueError(msg)

        if index < 0:
            msg = f"Index must be non-negative, got {index}"
            raise ValueError(msg)

        if index >= len(line):
            msg = f"Index {index} is out of range for line with {len(line)} elements"
            raise ValueError(msg)

        return line[index]

    def parse_action_data(self, line: list[str]) -> dict[str, Any]:
        """actionに応じて適切なデータを解析してdictとして返す.

        Args:
            line: CSV行のデータ（文字列のリスト）

        Returns:
            解析されたデータのdict

        Raises:
            TypeError: lineがリストでないか、要素が文字列でない場合
            ValueError: lineが空の場合、または解析に失敗した場合
        """
        try:
            action = self.get_action(line).lower()
            base_data = {"day": self.get_day(line), "action": action}

            # action別の追加データを取得
            action_specific_data = self._get_action_specific_data(action, line)
            base_data.update(action_specific_data)

            return base_data

        except (TypeError, ValueError) as e:
            raise ValueError(f"Failed to parse action data for line: {line}") from e

    def _get_action_specific_data(self, action: str, line: list[str]) -> dict[str, str]:
        """action固有のデータを取得する.

        Args:
            action: アクション名
            line: CSV行のデータ

        Returns:
            action固有のデータdict
        """
        action_parsers = {
            "talk": self._parse_conversation_action,
            "whisper": self._parse_conversation_action,
            "status": self._parse_status_action,
            "vote": self._parse_vote_action,
            "divine": self._parse_divine_action,
            "execute": self._parse_execute_action,
            "guard": self._parse_guard_action,
            "result": self._parse_result_action,
        }

        parser_func = action_parsers.get(action)
        return parser_func(line) if parser_func else {}

    def _parse_conversation_action(self, line: list[str]) -> dict[str, str]:
        """会話系アクション（talk/whisper）のデータを解析."""
        conv = CSVColumnIndices.ConversationAction
        return {
            "talk_number": self._get_element_safe(line, conv.TALK_NUMBER),
            "talk_count": self._get_element_safe(line, conv.TALK_COUNT),
            "speaker_index": self._get_element_safe(line, conv.SPEAKER_INDEX),
            "text": self._get_element_safe(line, conv.TEXT),
        }

    def _parse_status_action(self, line: list[str]) -> dict[str, str]:
        """statusアクションのデータを解析."""
        status = CSVColumnIndices.StatusAction
        return {
            "player_index": self._get_element_safe(line, status.PLAYER_INDEX),
            "role": self._get_element_safe(line, status.ROLE),
            "alive_status": self._get_element_safe(line, status.ALIVE_STATUS),
            "team_name": self._get_element_safe(line, status.TEAM_NAME),
            "player_name": self._get_element_safe(line, status.PLAYER_NAME),
        }

    def _parse_vote_action(self, line: list[str]) -> dict[str, str]:
        """voteアクションのデータを解析."""
        vote = CSVColumnIndices.VoteAction
        return {
            "voter_index": self._get_element_safe(line, vote.VOTER_INDEX),
            "target_index": self._get_element_safe(line, vote.TARGET_INDEX),
        }

    def _parse_divine_action(self, line: list[str]) -> dict[str, str]:
        """divineアクションのデータを解析."""
        divine = CSVColumnIndices.DivineAction
        return {
            "diviner_index": self._get_element_safe(line, divine.DIVINER_INDEX),
            "target_index": self._get_element_safe(line, divine.TARGET_INDEX),
            "divine_result": self._get_element_safe(line, divine.DIVINE_RESULT),
        }

    def _parse_execute_action(self, line: list[str]) -> dict[str, str]:
        """executeアクションのデータを解析."""
        execute = CSVColumnIndices.ExecuteAction
        return {
            "executed_player_index": self._get_element_safe(
                line, execute.EXECUTED_PLAYER_INDEX
            ),
            "executed_player_role": self._get_element_safe(
                line, execute.EXECUTED_PLAYER_ROLE
            ),
        }

    def _parse_guard_action(self, line: list[str]) -> dict[str, str]:
        """guardアクションのデータを解析."""
        guard = CSVColumnIndices.GuardAction
        return {
            "guard_player_index": self._get_element_safe(
                line, guard.GUARD_PLAYER_INDEX
            ),
            "target_player_index": self._get_element_safe(
                line, guard.TARGET_PLAYER_INDEX
            ),
            "target_player_role": self._get_element_safe(
                line, guard.TARGET_PLAYER_ROLE
            ),
        }

    def _parse_result_action(self, line: list[str]) -> dict[str, str]:
        """resultアクションのデータを解析."""
        result = CSVColumnIndices.ResultAction
        return {
            "villager_survivors": self._get_element_safe(
                line, result.VILLAGER_SURVIVORS
            ),
            "werewolf_survivors": self._get_element_safe(
                line, result.WEREWOLF_SURVIVORS
            ),
            "winning_team": self._get_element_safe(line, result.WINNING_TEAM),
        }

    def _get_element_safe(self, line: list[str], index: int) -> str:
        """安全に要素を取得する（インデックス範囲外の場合は空文字を返す）.

        Args:
            line: CSV行のデータ
            index: 取得したいインデックス

        Returns:
            要素の値、または空文字
        """
        try:
            return self._get_element(line, index)
        except (ValueError, TypeError):
            return ""
