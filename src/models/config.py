"""設定管理用のデータクラス."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PathConfig:
    """パス設定."""

    env: Path
    evaluation_criteria: Path


@dataclass(frozen=True)
class LLMConfig:
    """LLM設定."""

    prompt_yml: Path
    model: str


@dataclass(frozen=True)
class GameConfig:
    """ゲーム設定."""

    format: str
    player_count: int


@dataclass(frozen=True)
class ProcessingConfig:
    """処理設定."""

    input_dir: Path
    output_dir: Path
    max_workers: int


@dataclass(frozen=True)
class AppConfig:
    """アプリケーション全体の設定."""

    path: PathConfig
    llm: LLMConfig
    game: GameConfig
    processing: ProcessingConfig

    @classmethod
    def from_dict(cls, config_dict: dict) -> "AppConfig":
        """辞書から設定を作成."""
        path_config = PathConfig(
            env=Path(config_dict["path"]["env"]),
            evaluation_criteria=Path(config_dict["path"]["evaluation_criteria"]),
        )

        llm_config = LLMConfig(
            prompt_yml=Path(config_dict["llm"]["prompt_yml"]),
            model=config_dict["llm"]["model"],
        )

        game_config = GameConfig(
            format=config_dict["game"]["format"],
            player_count=config_dict["game"]["player_count"],
        )

        processing_config = ProcessingConfig(
            input_dir=Path(config_dict["processing"]["input_dir"]),
            output_dir=Path(config_dict["processing"]["output_dir"]),
            max_workers=config_dict["processing"]["max_workers"],
        )

        return cls(
            path=path_config,
            llm=llm_config,
            game=game_config,
            processing=processing_config,
        )

    def to_dict(self) -> dict:
        """辞書形式に変換."""
        return {
            "path": {
                "env": str(self.path.env),
                "evaluation_criteria": str(self.path.evaluation_criteria),
            },
            "llm": {"prompt_yml": str(self.llm.prompt_yml), "model": self.llm.model},
            "game": {
                "format": self.game.format,
                "player_count": self.game.player_count,
            },
            "processing": {
                "input_dir": str(self.processing.input_dir),
                "output_dir": str(self.processing.output_dir),
                "max_workers": self.processing.max_workers,
            },
        }
