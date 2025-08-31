"""JSONファイルからキャラクター情報を読み込むモジュール."""

import json
from pathlib import Path
from typing import Any, Self

from aiwolf_nlp_common.packet import Request
from src.models.game import PlayerInfo


class AIWolfJSONReader:
    """AIWolfのJSONファイルを読み込むクラス."""

    def __init__(self, file_path: Path):
        """初期化

        Args:
            file_path: JSONファイルのパス

        Raises:
            FileNotFoundError: ファイルが存在しない場合
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        self.file_path = file_path
        self._data: dict[str, Any] | None = None

    @property
    def data(self) -> dict[str, Any]:
        """データを取得（遅延読み込み）."""
        if self._data is None:
            self.read()
        return self._data

    def read(self) -> dict[str, Any]:
        """JSONファイルを読み込む

        Returns:
            読み込んだデータ

        Raises:
            json.JSONDecodeError: JSONの解析に失敗した場合
        """
        with open(self.file_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        return self._data

    @classmethod
    def from_log_path(cls, log_path: Path) -> Self:
        """ログファイルパスから対応するJSONファイルのリーダーを作成

        hoge.logに対応するhoge.jsonを読み込む

        Args:
            log_path: ログファイルのパス

        Returns:
            AIWolfJSONReaderインスタンス

        Raises:
            FileNotFoundError: 対応するJSONファイルが存在しない場合
        """
        json_path = log_path.with_suffix(".json")
        return cls(json_path)

    def get_player_infos(self) -> list[PlayerInfo]:
        """agentsデータからPlayerInfoのリストを作成

        Returns:
            PlayerInfoのリスト
        """
        agents = self.data.get("agents", [])
        return [
            PlayerInfo(
                index=agent["idx"],
                full_team_name=agent["name"],
                team=agent["team"],
            )
            for agent in agents
        ]

    def get_initialize_profiles(self) -> dict[str, str]:
        """INITIALIZE requestから各エージェントのプロフィール情報を取得.

        Returns:
            エージェント名をキー、プロフィール文字列を値とする辞書
        """
        profiles = {}
        entries = self.data.get("entries", [])

        for entry in entries:
            try:
                request_str = entry.get("request", "")
                if not request_str:
                    continue

                request_data = json.loads(request_str)

                if request_data.get("request") == Request.INITIALIZE.value:
                    info = request_data.get("info", {})
                    agent_name = info.get("agent")
                    profile = info.get("profile")

                    if agent_name and profile:
                        profiles[agent_name] = profile

            except (json.JSONDecodeError, KeyError, TypeError):
                continue

        return profiles

    def get_agents_data(self) -> list[dict[str, Any]]:
        """agentsセクションの生データを取得.

        Returns:
            agents配列のデータ
        """
        return self.data.get("agents", [])

    def get_entries_data(self) -> list[dict[str, Any]]:
        """entriesセクションの生データを取得.

        Returns:
            entries配列のデータ
        """
        return self.data.get("entries", [])
