import logging
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any
import json

from src.aiwolf_log.game_log import AIWolfGameLog
from src.models.game import GameFormat, GameInfo
from src.models.evaluation.config import EvaluationConfig
from src.utils.game_log_finder import find_all_game_logs
from src.evaluator.config_loader import ConfigLoader
from src.evaluator.game_detector import GameDetector
from src.llm.formatter import GameLogFormatter
from src.llm.evaluator import Evaluator
from src.models.evaluation.llm_response import EvaluationLLMResponse
from src.models.evaluation.result import EvaluationResult


logger = logging.getLogger(__name__)


def _extract_processing_config(
    config: dict[str, Any],
) -> tuple[Path, Path, int, GameFormat]:
    """設定からprocessing関連の値を抽出."""
    try:
        processing_config = config["processing"]
        input_dir = Path(processing_config["input_dir"])
        output_dir = Path(processing_config["output_dir"])
        max_workers = processing_config.get("max_workers") or mp.cpu_count()

        # ゲーム形式を文字列からEnumに変換
        game_format_str = config.get("game", {}).get("format", "self_match")
        try:
            game_format = GameFormat(game_format_str)
        except ValueError:
            game_format = GameFormat.SELF_MATCH  # デフォルト値

        return input_dir, output_dir, max_workers, game_format
    except KeyError as e:
        raise ValueError(f"Missing required config key: {e}")


def _collect_processing_results(
    futures: list[tuple[Any, AIWolfGameLog]],
) -> tuple[int, int]:
    """処理結果を収集して成功・失敗数をカウント."""
    completed = 0
    failed = 0

    for future, game_log in futures:
        try:
            result = future.result()
            if result:
                completed += 1
                logger.info(f"Completed processing: {game_log.game_id}")
            else:
                failed += 1
                logger.error(f"Failed processing: {game_log.game_id}")
        except Exception as e:
            failed += 1
            logger.error(f"Error processing {game_log.game_id}: {e}")

    return completed, failed


def process_all_games(config: dict[str, Any]) -> None:
    """すべてのゲームログを並列処理で評価.

    Args:
        config: 設定辞書（input_dir, output_dir, max_workersを含む）
    """
    input_dir, output_dir, max_workers, game_format = _extract_processing_config(config)
    logger.info(f"Starting batch processing with {max_workers} workers")

    logger.info(f"Searching for game logs in: {input_dir}")
    game_logs = find_all_game_logs(input_dir)
    logger.info(f"Found {len(game_logs)} game logs")

    if not game_logs:
        logger.warning("No game logs found")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Processing {len(game_logs)} games with {max_workers} workers")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            (
                executor.submit(process_single_game, game_log, config, output_dir),
                game_log,
            )
            for game_log in game_logs
        ]

        completed, failed = _collect_processing_results(futures)

    logger.info(f"Batch processing completed. Success: {completed}, Failed: {failed}")


def _load_evaluation_configs(settings_path: Path) -> EvaluationConfig:
    """評価設定とゲーム情報の読み込み."""
    evaluation_config = ConfigLoader.load_from_settings(settings_path)
    logger.info(f"Loaded evaluation config with {len(evaluation_config)} criteria")
    return evaluation_config


def _detect_and_log_game_info(game_log: AIWolfGameLog, settings_path: Path) -> GameInfo:
    """ゲーム情報の検出とログ出力."""
    game_info = GameDetector.detect_game_format(game_log.log_path, settings_path)
    logger.info(
        f"Detected game format: {game_info.game_format.value}, player count: {game_info.player_count}"
    )
    return game_info


def _format_game_log(
    game_log: AIWolfGameLog, config: dict[str, Any], game_info: GameInfo
) -> list[dict[str, Any]]:
    """ゲームログのフォーマット変換."""
    formatter = GameLogFormatter(game_log, config, parser=None)
    formatted_data = formatter.convert_to_jsonl(game_info.game_format)
    logger.info(f"Formatted {len(formatted_data)} log entries")
    return formatted_data


def _execute_evaluations(
    evaluation_config: EvaluationConfig,
    game_info: GameInfo,
    formatted_data: list[dict[str, Any]],
    evaluator: Evaluator,
) -> EvaluationResult:
    """各評価基準に対する評価の実行."""
    evaluation_result = EvaluationResult()
    criteria_for_game = evaluation_config.get_criteria_for_game(game_info.player_count)

    for criteria in criteria_for_game:
        logger.info(f"Evaluating criteria: {criteria.name}")

        llm_response = evaluator.evaluation(
            criteria=criteria,
            log=formatted_data,
            output_structure=EvaluationLLMResponse,
        )

        evaluation_result.add_response(criteria.name, llm_response)
        logger.info(f"Completed evaluation for criteria: {criteria.name}")

    return evaluation_result


def _build_result_data(
    game_log: AIWolfGameLog, game_info: GameInfo, evaluation_result: EvaluationResult
) -> dict[str, Any]:
    """評価結果データの構築."""
    result_data = {
        "game_id": game_log.game_id,
        "game_info": {
            "format": game_info.game_format.value,
            "player_count": game_info.player_count,
        },
        "evaluations": {},
    }

    for criteria_name in evaluation_result.get_all_criteria_names():
        response = evaluation_result.get_by_criteria(criteria_name)
        result_data["evaluations"][criteria_name] = {
            "rankings": [
                {
                    "player_name": elem.player_name,
                    "ranking": elem.ranking,
                    "reasoning": elem.reasoning,
                }
                for elem in response.rankings
            ]
        }

    return result_data


def _save_evaluation_result(result_data: dict[str, Any], output_path: Path) -> None:
    """評価結果のファイル保存."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved evaluation results to: {output_path}")


def process_single_game(
    game_log: AIWolfGameLog, config: dict[str, Any], output_dir: Path
) -> bool:
    """単一ゲームの処理（プロセス間で実行される関数）."""
    try:
        logger.info(f"Processing game: {game_log.game_id}")

        settings_path = Path(config.get("settings_path", "config/settings.yaml"))

        # 設定とゲーム情報の読み込み
        evaluation_config = _load_evaluation_configs(settings_path)
        game_info = _detect_and_log_game_info(game_log, settings_path)

        # ゲームログのフォーマット変換
        formatted_data = _format_game_log(game_log, config, game_info)

        # 評価実行
        evaluator = Evaluator(config)
        evaluation_result = _execute_evaluations(
            evaluation_config, game_info, formatted_data, evaluator
        )

        # 結果の保存
        output_path = output_dir / f"{game_log.game_id}_result.json"
        result_data = _build_result_data(game_log, game_info, evaluation_result)
        _save_evaluation_result(result_data, output_path)

        return True

    except Exception as e:
        logger.error(f"Failed to process game {game_log.game_id}: {e}", exc_info=True)
        return False
