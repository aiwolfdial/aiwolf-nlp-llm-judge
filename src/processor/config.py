"""プロセッサー処理設定を表すデータクラス."""

import multiprocessing as mp
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from src.models.game import GameFormat
from .errors import ConfigurationError


@dataclass(frozen=True)
class ProcessingConfig:
    """処理設定を表すデータクラス

    Attributes:
        input_dir: 入力ディレクトリのパス
        output_dir: 出力ディレクトリのパス
        max_workers: 並列処理の最大ワーカー数
        game_format: ゲーム形式
    """

    input_dir: Path
    output_dir: Path
    max_workers: int
    game_format: GameFormat

    @staticmethod
    def from_config_dict(config: Dict[str, Any]) -> "ProcessingConfig":
        """設定辞書から処理設定を作成

        Args:
            config: アプリケーション設定辞書

        Returns:
            処理設定オブジェクト

        Raises:
            ConfigurationError: 設定が不正な場合
        """
        try:
            processing_config = config["processing"]
            input_dir = Path(processing_config["input_dir"])
            output_dir = Path(processing_config["output_dir"])
            max_workers = processing_config.get("max_workers") or mp.cpu_count()

            # ゲーム形式を文字列からEnumに変換
            game_format_str = config.get("game", {}).get("format", "self_match")
            try:
                game_format = GameFormat(game_format_str)
            except ValueError as e:
                valid_formats = [fmt.value for fmt in GameFormat]
                error_msg = (
                    f"Invalid game format: '{game_format_str}'. "
                    f"Valid values are: {valid_formats}"
                )
                raise ConfigurationError(error_msg) from e

            return ProcessingConfig(
                input_dir=input_dir,
                output_dir=output_dir,
                max_workers=max_workers,
                game_format=game_format,
            )

        except KeyError as e:
            raise ConfigurationError(f"Missing required config key: {e}") from e
