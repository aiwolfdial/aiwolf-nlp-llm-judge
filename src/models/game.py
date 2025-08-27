from dataclasses import dataclass
from enum import Enum


class ParticipantNum(Enum):
    """対戦人数を表す列挙型"""

    FIVE_PLAYER = "5_player"
    THIRTEEN_PLAYER = "13_player"


class GameFormat(Enum):
    """ゲーム形式を表す列挙型"""

    SELF_MATCH = "self_match"
    MAIN_MATCH = "main_match"


@dataclass
class GameInfo:
    """ゲーム情報を表すデータクラス"""

    participant_num: ParticipantNum
    game_format: GameFormat
    player_count: int
    game_id: str = ""
