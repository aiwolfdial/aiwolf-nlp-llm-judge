import csv
from pathlib import Path
from typing import Set

from .models import GameFormat, GameInfo


class GameDetector:
    """CSVファイルからゲーム形式を検出するクラス"""
    
    @staticmethod
    def detect_game_format(csv_path: Path) -> GameInfo:
        """CSVファイルからゲーム形式を検出
        
        Args:
            csv_path: CSVファイルのパス
            
        Returns:
            GameInfo: 検出されたゲーム情報
            
        Raises:
            FileNotFoundError: CSVファイルが見つからない場合
            ValueError: ゲーム形式を判定できない場合
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        player_indices = GameDetector._extract_player_indices(csv_path)
        player_count = len(player_indices)
        
        # プレイヤー数に基づいてゲーム形式を判定
        if player_count == 5:
            game_format = GameFormat.FIVE_PLAYER
        elif player_count == 13:
            game_format = GameFormat.THIRTEEN_PLAYER
        else:
            raise ValueError(f"Unsupported player count: {player_count}")
        
        return GameInfo(
            format=game_format,
            player_count=player_count,
            game_id=csv_path.stem
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
            with csv_path.open('r', encoding='utf-8') as f:
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