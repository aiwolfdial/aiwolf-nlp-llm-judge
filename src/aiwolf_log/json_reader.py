"""JSONファイルからキャラクター情報を読み込むモジュール."""

import json
from pathlib import Path
from typing import Any, Self

from aiwolf_nlp_common.packet import Request
from src.game.models import PlayerInfo


class AIWolfJSONReader:
    """AIWolfのJSONファイルを読み込むクラス."""

    def __init__(self, file_path: Path, encoding: str = "utf-8"):
        """初期化

        Args:
            file_path: JSONファイルのパス
            encoding: ファイルエンコーディング（デフォルト: utf-8）

        Raises:
            FileNotFoundError: ファイルが存在しない場合
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        self.file_path = file_path
        self.encoding = encoding
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
        with open(self.file_path, "r", encoding=self.encoding) as f:
            self._data = json.load(f)
        return self._data

    @classmethod
    def from_log_path(cls, log_path: Path, encoding: str = "utf-8") -> Self:
        """ログファイルパスから対応するJSONファイルのリーダーを作成

        hoge.logに対応するhoge.jsonを読み込む

        Args:
            log_path: ログファイルのパス
            encoding: ファイルエンコーディング（デフォルト: utf-8）

        Returns:
            AIWolfJSONReaderインスタンス

        Raises:
            FileNotFoundError: 対応するJSONファイルが存在しない場合
        """
        json_path = log_path.with_suffix(".json")
        return cls(json_path, encoding)

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

    def get_agent_to_team_mapping(self) -> dict[str, str]:
        """エージェント表示名からチーム名へのマッピングを作成

        エージェント表示名（Minako, Yumi など）から、実際のチーム名を取得する
        INITIALIZE requestの出現順序とagents配列のインデックス順序を対応付けることで、
        より確実なマッピングを実現する

        Returns:
            エージェント名をキー、チーム名を値とする辞書
        """
        import logging

        logger = logging.getLogger(__name__)

        agent_to_team = {}
        entries = self.data.get("entries", [])
        agents_data = self.data.get("agents", [])

        # agents配列をidx順にソートしてチーム情報を取得
        agents_sorted = sorted(agents_data, key=lambda x: x["idx"])
        team_list = [agent["team"] for agent in agents_sorted]

        # INITIALIZE requestからエージェント名を出現順に取得
        agent_names_in_order = []
        processed_agents = set()

        for entry in entries:
            try:
                request_str = entry.get("request", "")
                if not request_str:
                    continue

                request_data = json.loads(request_str)

                if request_data.get("request") == Request.INITIALIZE.value:
                    info = request_data.get("info", {})
                    agent_name = info.get("agent")

                    # 既に処理済みのエージェントはスキップ
                    if not agent_name or agent_name in processed_agents:
                        continue

                    processed_agents.add(agent_name)
                    agent_names_in_order.append(agent_name)

            except (json.JSONDecodeError, KeyError, TypeError):
                continue

        # INITIALIZE requestの出現順序とagents配列の順序を対応付け
        # 両方の配列の長さが一致する場合のみマッピングを作成
        if len(agent_names_in_order) == len(team_list):
            for agent_name, team in zip(agent_names_in_order, team_list):
                agent_to_team[agent_name] = team
        else:
            # 長さが一致しない場合、フォールバック：エージェント名からチーム名を推測
            logger.warning(
                f"Agent names count ({len(agent_names_in_order)}) != teams count ({len(team_list)}). "
                "Using fallback mapping."
            )
            # 利用可能なチーム情報がある限りマッピングを作成
            for i, agent_name in enumerate(agent_names_in_order):
                if i < len(team_list):
                    agent_to_team[agent_name] = team_list[i]
                else:
                    agent_to_team[agent_name] = "unknown"

        return agent_to_team

    def get_character_info(self) -> dict[str, str]:
        """キャラクター情報を取得（get_initialize_profilesのエイリアス）

        Returns:
            エージェント名をキー、プロフィール文字列を値とする辞書
        """
        return self.get_initialize_profiles()
