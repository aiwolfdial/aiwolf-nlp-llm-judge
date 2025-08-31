import csv
from pathlib import Path


class AIWolfCSVReader:
    def __init__(self, config: dict, file_path: Path):
        if not file_path.is_file():
            msg = f"File not found: {file_path}"
            raise ValueError(msg)

        self.file_path = file_path
        self.encoding = str(config["processing"]["encoding"])
        self._file = None
        self._reader = None

    def open(self):
        """ファイルを開いてCSVリーダーを初期化"""
        self._file = open(self.file_path, encoding=self.encoding)
        self._reader = csv.reader(self._file)

    def read_next_line(self) -> list[str] | None:
        """次の行を読み込む"""
        if self._reader is None:
            raise RuntimeError("File not opened. Call open() first.")
        try:
            line = next(self._reader)
            if not line:
                raise ValueError("Empty line found in CSV")
            return line
        except StopIteration:
            return None

    def close(self):
        """ファイルを閉じる"""
        if self._file:
            self._file.close()
            self._file = None
            self._reader = None

    def __enter__(self):
        """with文のサポート"""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """with文のサポート"""
        self.close()
