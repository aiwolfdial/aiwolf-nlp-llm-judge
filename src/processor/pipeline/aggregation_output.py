"""チーム集計結果の出力を管理するサービス."""

import csv
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AggregationOutputService:
    """チーム集計結果の出力を管理するサービス

    このサービスは、チーム集計データをJSON形式およびCSV形式で
    出力する責任を持ちます。
    """

    def save_json(self, aggregation_data: dict[str, Any], output_dir: Path) -> None:
        """チーム集計結果をJSON形式で保存

        Args:
            aggregation_data: 集計データ
            output_dir: 出力ディレクトリパス
        """
        try:
            aggregation_file = output_dir / "team_aggregation.json"
            with open(aggregation_file, "w", encoding="utf-8") as f:
                json.dump(aggregation_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Team aggregation saved to: {aggregation_file}")
        except Exception as e:
            logger.error(f"Failed to save JSON file: {e}", exc_info=True)
            raise

    def save_csv(self, aggregation_data: dict[str, Any], output_dir: Path) -> None:
        """チーム集計結果をCSV形式で保存

        Args:
            aggregation_data: JSON出力と同じ構造の集計データ
            output_dir: 出力ディレクトリパス
        """
        try:
            csv_file_path = output_dir / "team_aggregation.csv"
            team_averages = aggregation_data.get("team_averages", {})
            criteria_evaluated = aggregation_data.get("summary", {}).get(
                "criteria_evaluated", []
            )

            if not team_averages or not criteria_evaluated:
                logger.warning("No team averages data found for CSV output")
                return

            with open(csv_file_path, "w", encoding="utf-8", newline="") as csvfile:
                writer = csv.writer(csvfile)

                # ヘッダー行（チーム、各評価基準の平均順位）
                header = ["Team"]
                for criteria in criteria_evaluated:
                    header.append(criteria)
                writer.writerow(header)

                # 各チームのデータを書き出し
                for team in sorted(team_averages.keys()):
                    row = [team]

                    for criteria in criteria_evaluated:
                        # 平均順位（小数点第6位まで）
                        avg = team_averages.get(team, {}).get(criteria, 0.0)
                        row.append(f"{avg:.6f}")

                    writer.writerow(row)

            logger.info(
                f"CSV data saved with {len(team_averages)} teams and {len(criteria_evaluated)} criteria to: {csv_file_path}"
            )

        except Exception as e:
            logger.error(f"Failed to save CSV file: {e}", exc_info=True)
            raise

    def save_both(self, aggregation_data: dict[str, Any], output_dir: Path) -> None:
        """チーム集計結果をJSONとCSVの両形式で保存

        Args:
            aggregation_data: 集計データ
            output_dir: 出力ディレクトリパス
        """
        # JSONファイル保存
        self.save_json(aggregation_data, output_dir)

        # CSVファイル保存
        self.save_csv(aggregation_data, output_dir)

        # 処理結果ログ出力
        teams_processed = list(aggregation_data["team_averages"].keys())
        logger.info(f"Teams processed: {teams_processed}")
