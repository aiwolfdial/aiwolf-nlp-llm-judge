from dataclasses import dataclass
from enum import Enum


class GameFormat(Enum):
    """ゲーム形式を表す列挙型"""

    FIVE_PLAYER = "5_player"
    THIRTEEN_PLAYER = "13_player"


@dataclass
class GameInfo:
    """ゲーム情報を表すデータクラス"""

    format: GameFormat
    player_count: int
    game_id: str = ""
