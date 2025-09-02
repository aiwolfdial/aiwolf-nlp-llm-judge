"""AIWolf CSV構造の定義モジュール.

このモジュールは、AIWolfゲームのCSVファイルの列構造を定義します。
アクションごとに異なる列の意味を明確に定義することで、
コード全体でのマジックナンバーの使用を避け、保守性を向上させます。
"""

from __future__ import annotations


# 共通列インデックス
DAY = 0
ACTION = 1

# アクション固有列のベースインデックス（2から開始）
ACTION_DATA_START = 2


class CSVColumnIndices:
    """AIWolf CSVファイルの列インデックス定義クラス.

    AIWolfのCSVファイルは以下の構造を持ちます：
    - 列0: Day (日数) - 全actionで共通
    - 列1: Action (アクション名) - 全actionで共通
    - 列2以降: アクション固有のデータ

    各アクションごとに列2以降の意味が変わるため、
    アクション別にネストされたクラスで定義しています。
    """

    # 共通列（全actionで共通）
    DAY = DAY
    ACTION = ACTION

    class ConversationAction:
        """会話系アクション（talk/whisper）の列定義.

        フォーマット例:
        Day, Action, TalkNumber, TalkCount, SpeakerIndex, Text
        0,   talk,   1,          5,         3,            "Hello world"
        """

        TALK_NUMBER = ACTION_DATA_START + 0  # 2: 発話番号
        TALK_COUNT = ACTION_DATA_START + 1  # 3: 発話カウント
        SPEAKER_INDEX = ACTION_DATA_START + 2  # 4: 発話者インデックス
        TEXT = ACTION_DATA_START + 3  # 5: 発話内容

    class StatusAction:
        """statusアクションの列定義.

        フォーマット例:
        Day, Action, PlayerIndex, Role,      AliveStatus, TeamName,     PlayerName
        0,   status, 1,           VILLAGER,  ALIVE,       team_alpha,   Taro
        """

        PLAYER_INDEX = ACTION_DATA_START + 0  # 2: プレイヤーインデックス
        ROLE = ACTION_DATA_START + 1  # 3: 役職
        ALIVE_STATUS = ACTION_DATA_START + 2  # 4: 生存状態
        TEAM_NAME = ACTION_DATA_START + 3  # 5: チーム名
        PLAYER_NAME = ACTION_DATA_START + 4  # 6: プレイヤー名

    class VoteAction:
        """voteアクションの列定義.

        フォーマット例:
        Day, Action, VoterIndex, TargetIndex
        1,   vote,   1,          3
        """

        VOTER_INDEX = ACTION_DATA_START + 0  # 2: 投票者インデックス
        TARGET_INDEX = ACTION_DATA_START + 1  # 3: 投票対象インデックス

    class DivineAction:
        """divineアクション（占い）の列定義.

        フォーマット例:
        Day, Action, DivinerIndex, TargetIndex, DivineResult
        1,   divine, 1,            3,           HUMAN
        """

        DIVINER_INDEX = ACTION_DATA_START + 0  # 2: 占い師インデックス
        TARGET_INDEX = ACTION_DATA_START + 1  # 3: 占い対象インデックス
        DIVINE_RESULT = ACTION_DATA_START + 2  # 4: 占い結果

    class ExecuteAction:
        """executeアクション（処刑）の列定義.

        フォーマット例:
        Day, Action,  ExecutedPlayerIndex, ExecutedPlayerRole
        1,   execute, 3,                   WEREWOLF
        """

        EXECUTED_PLAYER_INDEX = (
            ACTION_DATA_START + 0
        )  # 2: 処刑されたプレイヤーのインデックス
        EXECUTED_PLAYER_ROLE = ACTION_DATA_START + 1  # 3: 処刑されたプレイヤーの役職

    class GuardAction:
        """guardアクション（護衛）の列定義.

        フォーマット例:
        Day, Action, GuardPlayerIndex, TargetPlayerIndex, TargetPlayerRole
        1,   guard,  2,                1,                SEER
        """

        GUARD_PLAYER_INDEX = (
            ACTION_DATA_START + 0
        )  # 2: 護衛したプレイヤーのインデックス
        TARGET_PLAYER_INDEX = (
            ACTION_DATA_START + 1
        )  # 3: 護衛対象プレイヤーのインデックス
        TARGET_PLAYER_ROLE = ACTION_DATA_START + 2  # 4: 護衛対象プレイヤーの役職

    class ResultAction:
        """resultアクション（ゲーム結果）の列定義.

        フォーマット例:
        Day, Action, VillagerSurvivors, WerewolfSurvivors, WinningTeam
        3,   result, 2,                 0,                 VILLAGER
        """

        VILLAGER_SURVIVORS = ACTION_DATA_START + 0  # 2: 村人陣営の生存者数
        WEREWOLF_SURVIVORS = ACTION_DATA_START + 1  # 3: 人狼陣営の生存者数
        WINNING_TEAM = ACTION_DATA_START + 2  # 4: 勝利チーム


class ActionTypes:
    """AIWolfで使用されるアクションタイプの定数定義."""

    # 会話系
    TALK = "talk"
    WHISPER = "whisper"

    # ゲーム進行系
    STATUS = "status"
    VOTE = "vote"
    DIVINE = "divine"
    EXECUTE = "execute"
    GUARD = "guard"
    RESULT = "result"

    # 会話系アクションのリスト（複数のアクションで共通の処理を行う場合に使用）
    CONVERSATION_ACTIONS = [TALK, WHISPER]

    # 全アクションのリスト
    ALL_ACTIONS = [TALK, WHISPER, STATUS, VOTE, DIVINE, EXECUTE, GUARD, RESULT]
