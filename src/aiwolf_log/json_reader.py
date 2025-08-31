"""JSONファイルからキャラクター情報を読み込むモジュール"""

import json
from pathlib import Path
from typing import Any, Self


class AIWolfJSONReader:
    """AIWolfのJSONファイルを読み込むクラス"""

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

    def get_character_info(self) -> dict[str, Any]:
        """キャラクター情報を取得

        Returns:
            キャラクター情報の辞書
        """
        if self._data is None:
            self.read()
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
