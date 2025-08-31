"""ゲームログファイルの検索機能を提供するモジュール."""

from pathlib import Path

from src.aiwolf_log.game_log import AIWolfGameLog, AIWolfGameLogError


def find_all_game_logs(input_dir: Path) -> list[AIWolfGameLog]:
    """指定ディレクトリ内のすべてのゲームログを検索.

    Args:
        input_dir: inputディレクトリのパス

    Returns:
        AIWolfGameLogインスタンスのリスト
    """
    game_logs = []
    log_dir = input_dir / "log"

    if not log_dir.exists():
        return game_logs

    # ログファイルをベースにペアを探す
    for log_path in log_dir.glob("*.log"):
        try:
            file_name = log_path.stem
            game_log = AIWolfGameLog.from_input_dir(input_dir, file_name)
            game_logs.append(game_log)
        except (FileNotFoundError, AIWolfGameLogError):
            # 対応するJSONファイルがない場合はスキップ
            continue

    return game_logs
