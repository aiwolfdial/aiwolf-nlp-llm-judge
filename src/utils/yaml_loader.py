"""YAML ファイル読み込み基本機能."""

import yaml
from pathlib import Path
from typing import Any


class YAMLLoader:
    """YAMLファイルの基本読み込み機能を提供するクラス."""

    @staticmethod
    def load_yaml(file_path: Path) -> dict[str, Any]:
        """YAMLファイルを読み込んで辞書として返す

        Args:
            file_path: YAMLファイルのパス

        Returns:
            読み込まれたYAMLデータの辞書

        Raises:
            FileNotFoundError: ファイルが見つからない場合
            ValueError: YAMLファイルの形式が不正な場合
        """
        if not file_path.exists():
            raise FileNotFoundError(f"YAML file not found: {file_path}")

        try:
            with file_path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format in {file_path}: {e}")
