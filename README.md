# AIWolf NLP LLM Judge

AIWolfゲームログを生成AI（LLM）で評価するシステム

## 概要

このプロジェクトは、AIWolfゲームのログ（CSVファイル）を生成AI（LLM）に渡し、事前定義された評価基準に沿って評価を行うシステムです。5人戦と13人戦の両方に対応し、共通評価項目とゲーム形式固有の評価項目を独立して評価します。

## 主な機能

- **マルチゲーム形式対応**: 5人戦、13人戦などに対応
- **柔軟な評価システム**: 共通評価基準とゲーム固有評価基準を組み合わせた評価
- **並列処理**: プロセス・スレッドベースの高速処理
- **チーム集計**: 複数ゲームの結果を自動集計し、チーム別の平均スコアを算出
- **構造化出力**: JSON形式での詳細な評価結果とCSV形式での集計結果

## インストール

```bash
# uvがインストールされていない場合
pip install uv

# 依存関係のインストール
uv sync
```

## 使用方法

### 基本的な実行

```bash
# 標準設定での実行
uv run python main.py -c config/settings.yaml

# デバッグモードでの実行
uv run python main.py -c config/settings.yaml --debug
```

### データの準備

以下のディレクトリ構造でファイルを配置してください：

```
data/
├── input/
│   ├── log/     # ゲームログファイル (*.log)
│   └── json/    # キャラクター情報ファイル (*.json)
└── output/      # 評価結果の出力先
```

**重要**: ログファイルとJSONファイルは同じ名前（拡張子を除く）である必要があります。

## 設定

### メイン設定ファイル（`config/settings.yaml`）

```yaml
llm:
  model: "gpt-4o"              # 使用するLLMモデル

game:
  format: "main_match"         # ゲーム形式
  player_count: 13             # プレイヤー数

processing:
  max_workers: 4               # 並列処理数
  evaluation_workers: 8        # 評価並列処理数
```

### 評価基準の定義（`config/evaluation_criteria.yaml`）

評価基準は共通基準とゲーム固有基準に分けて定義します：

```yaml
common_criteria:               # 全ゲーム共通の評価基準
  - name: "natural_expression"
    description: "発話表現は自然か"
    ranking_type: "ordinal"
    order: 1

game_specific_criteria:        # ゲーム形式固有の評価基準
  13_player:
    - name: "team_play"
      description: "チームプレイができているか"
      ranking_type: "ordinal"
      applicable_games: [13]
      order: 6
```

## 出力形式

### 個別ゲーム結果（JSON）

各ゲームの評価結果は以下の形式で出力されます：

```json
{
  "game_id": "01K3T3XN1SHBHSBHV1JWDDVS7W",
  "game_info": {
    "format": "main_match",
    "player_count": 13
  },
  "evaluations": {
    "team_play": {
      "rankings": [
        {
          "player_name": "Takumi",
          "team": "sunamelli-b",
          "ranking": 1,
          "reasoning": "優れたチームプレイを実現..."
        }
      ]
    }
  }
}
```

### チーム集計結果

#### JSON形式（`team_aggregation.json`）

```json
{
  "team_averages": {
    "kanolab": {
      "発話表現は自然か": 3.9,
      "文脈を踏まえた対話は自然か": 3.4
    }
  },
  "team_sample_counts": {
    "kanolab": {
      "発話表現は自然か": 10,
      "文脈を踏まえた対話は自然か": 10
    }
  }
}
```

#### CSV形式（`team_aggregation.csv`）

```csv
Team,発話表現は自然か,文脈を踏まえた対話は自然か
kanolab,3.900000,3.400000
GPTaku,4.200000,3.800000
```

## システム要件

- Python 3.11以上
- OpenAI APIキー（環境変数または`.env`ファイルに設定）

## 開発

### プロジェクト構造

```
src/
├── cli.py              # CLIインターフェース
├── game/               # ゲームドメイン
├── evaluation/         # 評価ドメイン
├── processor/          # バッチ処理システム
├── aiwolf_log/         # ログファイル管理
├── llm/                # LLM統合
└── utils/              # ユーティリティ
```

### テストの実行

```bash
# テストの実行
uv run pytest

# カバレッジ付きテスト
uv run pytest --cov=src
```

## ライセンス

このプロジェクトのライセンスについては、プロジェクトのルートディレクトリにあるLICENSEファイルを参照してください。

## 貢献

バグの報告や機能の提案は、GitHubのIssueで受け付けています。プルリクエストも歓迎します。

## 問い合わせ

プロジェクトに関する質問や問題がある場合は、GitHubのIssueを作成してください。