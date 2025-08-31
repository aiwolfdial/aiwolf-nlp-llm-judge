"""AIWolfのゲームログ（ログファイルとJSONファイル）を管理するモジュール"""

from pathlib import Path
from typing import Any, Self

from .csv_reader import AIWolfCSVReader
from .json_reader import AIWolfJSONReader


class AIWolfGameLogError(Exception):
    """AIWolfゲームログ関連のエラー"""

    pass


class AIWolfGameLog:
    """AIWolfのゲームログ（ログファイルとJSONファイルのペア）を管理するクラス"""

    def __init__(
        self,
        input_dir: Path,
        file_name: str,
    ):
        """初期化

        Args:
            input_dir: 入力ディレクトリのパス
            file_name: ファイル名（拡張子なし）
        """
        self.input_dir = input_dir
        self.log_path = input_dir / "log" / f"{file_name}.log"
        self.json_path = input_dir / "json" / f"{file_name}.json"

        # ファイルの存在確認
        self._validate_files()

        # リーダーの初期化は遅延する
        self._csv_reader: AIWolfCSVReader | None = None
        self._json_reader: AIWolfJSONReader | None = None

        # game_idは遅延初期化（JSONから取得）
        self._game_id: str | None = None

    def _validate_files(self) -> None:
        """ファイルの存在を確認

        Raises:
            FileNotFoundError: ファイルが存在しない場合
        """
        if not self.log_path.exists():
            raise FileNotFoundError(f"Log file not found: {self.log_path}")
        if not self.json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {self.json_path}")

    def get_csv_reader(self, config: dict) -> AIWolfCSVReader:
        """CSVリーダーを取得

        Args:
            config: 設定辞書

        Returns:
            AIWolfCSVReaderインスタンス
        """
        if self._csv_reader is None:
            self._csv_reader = AIWolfCSVReader(config, self.log_path)
        return self._csv_reader

    def get_json_reader(self) -> AIWolfJSONReader:
        """JSONリーダーを取得

        Returns:
            AIWolfJSONReaderインスタンス
        """
        if self._json_reader is None:
            self._json_reader = AIWolfJSONReader(self.json_path)
        return self._json_reader

    def read_json(self) -> dict[str, Any]:
        """JSONファイルを読み込む

        Returns:
            JSONデータ
        """
        reader = self.get_json_reader()
        return reader.read()

    def get_character_info(self) -> dict[str, Any]:
        """キャラクター情報を取得

        Returns:
            キャラクター情報の辞書
        """
        reader = self.get_json_reader()
        return reader.get_character_info()

    @property
    def game_id(self) -> str:
        """ゲームIDをJSONから取得"""
        if self._game_id is None:
            json_reader = self.get_json_reader()
            json_data = json_reader.read()
            # JSONからgame_idを取得（フォーマットに依存）
            self._game_id = json_data.get("game_id", self.log_path.stem)
        return self._game_id

    @classmethod
    def from_input_dir(cls, input_dir: Path, file_name: str) -> Self:
        """入力ディレクトリとファイル名からインスタンスを作成"""
        return cls(input_dir=input_dir, file_name=file_name)

    @classmethod
    def find_all_game_logs(cls, input_dir: Path) -> list[Self]:
        """指定ディレクトリ内のすべてのゲームログを検索

        Args:
            input_dir: inputディレクトリのパス

        Returns:
            AIWolfGameLogインスタンスのリスト
        """
        game_logs = []
        log_dir = input_dir / "log"

        if not log_dir.exists():
            return game_logs

        # ログファイルをベースにペアを探す
        for log_path in log_dir.glob("*.log"):
            try:
                file_name = log_path.stem
                game_log = cls.from_input_dir(input_dir, file_name)
                game_logs.append(game_log)
            except (FileNotFoundError, AIWolfGameLogError):
                # 対応するJSONファイルがない場合はスキップ
                continue

        return game_logs

    def __repr__(self) -> str:
        return f"AIWolfGameLog(game_id='{self.game_id}', log='{self.log_path}', json='{self.json_path}')"
