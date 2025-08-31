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
        input_dir: Path | None = None,
        file_name: str | None = None,
        log_path: Path | None = None,
        json_path: Path | None = None,
    ):
        """初期化

        Args:
            input_dir: 入力ディレクトリのパス（推奨）
            file_name: ファイル名（拡張子なし）（input_dirと組み合わせて使用）
            log_path: ログファイルのパス（後方互換性）
            json_path: JSONファイルのパス（後方互換性）

        注意:
            推奨: input_dir + file_name の組み合わせ
            後方互換: log_pathとjson_pathの少なくとも一方
            game_idはJSONファイルから動的に取得される
        """
        # 初期化方式の判定
        if input_dir is not None and file_name is not None:
            # 推奨方式: input_dir + file_name
            self.input_dir = input_dir
            self.log_path = input_dir / "log" / f"{file_name}.log"
            self.json_path = input_dir / "json" / f"{file_name}.json"
        elif log_path is not None or json_path is not None:
            # 後方互換方式: ファイルパス指定
            if log_path is None and json_path is None:
                raise ValueError(
                    "Either (input_dir + file_name) or (log_path/json_path) must be provided"
                )

            self.input_dir = None

            # パスの推定と検証
            if log_path is not None and json_path is None:
                self.log_path = log_path
                self.json_path = self._infer_json_path_legacy(log_path)
            elif log_path is None and json_path is not None:
                self.json_path = json_path
                self.log_path = self._infer_log_path_legacy(json_path)
            else:
                # 両方指定された場合は名前の一致を確認
                if log_path.stem != json_path.stem:
                    raise AIWolfGameLogError(
                        f"File name mismatch: {log_path.name} and {json_path.name}"
                    )
                self.log_path = log_path
                self.json_path = json_path
        else:
            raise ValueError(
                "Either (input_dir + file_name) or (log_path/json_path) must be provided"
            )

        # ファイルの存在確認
        self._validate_files()

        # リーダーの初期化は遅延する
        self._csv_reader: AIWolfCSVReader | None = None
        self._json_reader: AIWolfJSONReader | None = None

        # game_idは遅延初期化（JSONから取得）
        self._game_id: str | None = None

    def _infer_json_path_legacy(self, log_path: Path) -> Path:
        """ログファイルパスからJSONファイルパスを推定（後方互換）

        Args:
            log_path: ログファイルのパス

        Returns:
            推定されたJSONファイルのパス
        """
        # data/input/log/hoge.log -> data/input/json/hoge.json
        json_dir = log_path.parent.parent / "json"
        json_filename = f"{log_path.stem}.json"
        return json_dir / json_filename

    def _infer_log_path_legacy(self, json_path: Path) -> Path:
        """JSONファイルパスからログファイルパスを推定（後方互換）

        Args:
            json_path: JSONファイルのパス

        Returns:
            推定されたログファイルのパス
        """
        # data/input/json/hoge.json -> data/input/log/hoge.log
        log_dir = json_path.parent.parent / "log"
        log_filename = f"{json_path.stem}.log"
        return log_dir / log_filename

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
        """入力ディレクトリとファイル名からインスタンスを作成（推奨）"""
        return cls(input_dir=input_dir, file_name=file_name)

    @classmethod
    def from_log_path(cls, log_path: Path) -> Self:
        """ログファイルパスからインスタンスを作成（後方互換）"""
        return cls(log_path=log_path)

    @classmethod
    def from_json_path(cls, json_path: Path) -> Self:
        """JSONファイルパスからインスタンスを作成（後方互換）"""
        return cls(json_path=json_path)

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
