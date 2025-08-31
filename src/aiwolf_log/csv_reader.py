import csv
import types
from pathlib import Path
from typing import Any


class AIWolfCSVReader:
    """AIWolf CSVファイルを読み込むクラス."""

    def __init__(self, config: dict[str, Any], file_path: Path) -> None:
        if not file_path.is_file():
            msg = f"File not found: {file_path}"
            raise ValueError(msg)

        self.file_path = file_path
        self.encoding = str(config["processing"]["encoding"])
        self._file = None
        self._reader = None

    def open(self) -> None:
        """ファイルを開いてCSVリーダーを初期化."""
        self._file = open(self.file_path, encoding=self.encoding)
        self._reader = csv.reader(self._file)

    def read_next_line(self) -> list[str] | None:
        """次の行を読み込む."""
        if self._reader is None:
            raise RuntimeError("File not opened. Call open() first.")
        try:
            line = next(self._reader)
            if not line:
                raise ValueError("Empty line found in CSV")
            return line
        except StopIteration:
            return None

    def close(self) -> None:
        """ファイルを閉じる."""
        if self._file:
            self._file.close()
            self._file = None
            self._reader = None

    def __enter__(self) -> "AIWolfCSVReader":
        """with文のサポート."""
        self.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """with文のサポート."""
        self.close()
