import csv
from pathlib import Path


class AIWolfCSVWriter:
    def __init__(self, config: dict, file_path: Path) -> None:
        if file_path.is_file():
            msg = f"すでに存在しています: {file_path}"
            raise ValueError(msg)

        self.file_path = file_path
        self.encoding = str(config["processing"]["encoding"])
        self.flush_threshold = int(config["processing"]["buffer_threshold"])
        self._file = None
        self._writer = None
        self.buffer_size = 0

    def open(self) -> None:
        """ファイルを開いてCSVリーダーを初期化"""
        self._file = open(self.file_path, encoding=self.encoding, mode="a+")
        self._writer = csv.writer(self._file)

    def write_line(self, line: list[str]) -> None:
        """行を書き込む"""
        self._writer.writerow(line)
        line_size = len(",".join(line)) + 1
        self.buffer_size += line_size

        if self.buffer_size >= self.flush_threshold:
            self._file.flush()
            self.buffer_size = 0

    def close(self) -> None:
        """ファイルを閉じる"""
        if self._file:
            self._file.flush()
            self._file.close()
            self._file = None
            self._writer = None
            self.buffer_size = 0

    def __enter__(self) -> None:
        """with文のサポート"""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """with文のサポート"""
        self.close()
