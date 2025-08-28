import csv
from pathlib import Path
from typing import Set

from models.game import ParticipantNum, GameInfo
from .config_loader import ConfigLoader


class GameDetector:
    """CSVファイルからゲーム形式を検出するクラス"""

    @staticmethod
    def detect_game_format(csv_path: Path, settings_path: Path) -> GameInfo:
        """CSVファイルからゲーム形式を検出

        Args:
            csv_path: CSVファイルのパス
            settings_path: 設定ファイルのパス

        Returns:
            GameInfo: 検出されたゲーム情報

        Raises:
            FileNotFoundError: CSVファイルが見つからない場合
            ValueError: ゲーム形式を判定できない場合
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # 設定ファイルから対戦人数とゲーム形式を読み込み
        participant_num = ConfigLoader.load_participant_num(settings_path)
        game_format = ConfigLoader.load_game_format(settings_path)

        # 設定に基づいたプレイヤー数を取得
        if participant_num == ParticipantNum.FIVE_PLAYER:
            expected_player_count = 5
        elif participant_num == ParticipantNum.THIRTEEN_PLAYER:
            expected_player_count = 13
        else:
            raise ValueError(f"Unknown participant number: {participant_num}")

        return GameInfo(
            participant_num=participant_num,
            game_format=game_format,
            player_count=expected_player_count,
            game_id=csv_path.stem,
        )

    @staticmethod
    def _extract_player_indices(csv_path: Path) -> Set[str]:
        """CSVファイルからプレイヤーインデックスを抽出

        Args:
            csv_path: CSVファイルのパス

        Returns:
            Set[str]: プレイヤーインデックスのセット
        """
        player_indices = set()

        try:
            with csv_path.open("r", encoding="utf-8") as f:
                csv_reader = csv.reader(f)

                for row in csv_reader:
                    if len(row) < 5:
                        continue

                    # 行動タイプをチェック（会話系の行動のみを対象）
                    action = row[1].lower() if len(row) > 1 else ""
                    if action in ["talk", "whisper"]:
                        # プレイヤーインデックスを抽出（4列目）
                        if len(row) > 4:
                            player_index = row[4]
                            if player_index:  # 空文字でない場合のみ追加
                                player_indices.add(player_index)

        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {e}")

        return player_indices
