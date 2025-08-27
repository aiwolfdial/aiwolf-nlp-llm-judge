# AIWolf NLP LLM Judge

AIWolf CSVファイルを生成AIで評価するシステム

## プロジェクト概要

このプロジェクトは、AIWolfゲームのログ（CSVファイル）を生成AI（LLM）に渡し、事前定義された評価基準に沿って評価を行うシステムです。5人戦と13人戦の両方に対応し、共通評価項目とゲーム形式固有の評価項目を独立して評価します。

## ファイル構成

```
aiwolf-nlp-llm-judge/
├── config/
│   ├── evaluation_criteria.yaml    # 評価基準設定
│   ├── prompt.yaml                  # プロンプト設定
│   └── settings.yaml               # メイン設定ファイル
├── src/
│   ├── aiwolf_csv/                 # CSV解析モジュール
│   │   ├── parser.py              # CSVパーサー
│   │   ├── reader.py
│   │   └── writer.py
│   └── evaluator/                 # 評価モジュール
│       ├── models.py              # データクラス定義
│       ├── config_loader.py       # 設定読み込み
│       ├── game_detector.py       # ゲーム形式検出
│       └── base_evaluator.py      # 評価器基底クラス
├── main.py
└── src/main.py
```

## 主要機能

### 1. ゲーム形式の自動検出
- CSVファイルを解析してプレイヤー数を検出
- 5人戦 または 13人戦 を自動判別

### 2. 柔軟な評価基準システム
- **共通評価項目**: 全ゲーム形式で共通の評価基準
- **固有評価項目**: ゲーム形式別の特別な評価基準
- **独立評価**: 各項目は重み付けなしで独立して評価

### 3. スケール設定
- `min`/`max`による範囲設定
- `integer`/`float`による数値型指定
- 項目ごとに異なるスケール設定可能

## 設定ファイル

### settings.yaml
メイン設定ファイル。評価基準ファイルのパスを管理。

```yaml
path:
  evaluation_criteria: config/evaluation_criteria.yaml
llm:
  model: "gpt-5"
```

### evaluation_criteria.yaml
評価基準の詳細設定。

```yaml
common_criteria:
  - name: "logical_consistency"
    description: "推理の論理的一貫性"
    scale:
      min: 1
      max: 5
      type: "integer"

game_specific_criteria:
  5_player:
    - name: "quick_decision"
      description: "限られた情報での迅速な判断"
      scale:
        min: 0.0
        max: 1.0
        type: "float"
  13_player:
    - name: "coalition_management"
      description: "陣営形成・管理能力"
      scale:
        min: 1
        max: 7
        type: "integer"
```

## データ構造

### 評価結果 (EvaluationResult)
```python
@dataclass
class EvaluationResult:
    game_info: GameInfo                    # ゲーム情報
    common_scores: Dict[str, EvaluationScore]  # 共通評価スコア
    specific_scores: Dict[str, EvaluationScore] # 固有評価スコア
```

### 評価スコア (EvaluationScore)
```python
@dataclass
class EvaluationScore:
    criteria_name: str           # 評価基準名
    value: Union[int, float]     # スコア値
    min_value: Union[int, float] # 最小値
    max_value: Union[int, float] # 最大値
    score_type: Literal["integer", "float"] # 数値型
```

## 使用方法

### 1. 設定読み込み
```python
from pathlib import Path
from src.evaluator.config_loader import ConfigLoader

# settings.yamlから評価設定を読み込み
settings_path = Path("config/settings.yaml")
evaluation_config = ConfigLoader.load_from_settings(settings_path)
```

### 2. ゲーム形式検出
```python
from src.evaluator.game_detector import GameDetector

csv_path = Path("data/game_log.csv")
game_info = GameDetector.detect_game_format(csv_path)
print(f"ゲーム形式: {game_info.format.value}, プレイヤー数: {game_info.player_count}")
```

### 3. 評価実行
```python
# 評価器の実装が完了後
evaluator = SomeEvaluator(evaluation_config)
result = evaluator.evaluate(csv_path, game_info)
```

## 開発ステータス

- [x] 基本設計
- [x] データ構造設計
- [x] 設定ファイル作成
- [x] ゲーム検出機能
- [x] 設定読み込み機能
- [x] 評価器基底クラス
- [ ] LLM評価エンジン実装
- [ ] プロンプト設計
- [ ] レポート生成機能
- [ ] テスト実装

## 今後の実装予定

1. **LLM評価エンジン** - 実際にLLMを呼び出して評価を行う
2. **プロンプト管理** - 評価基準別のプロンプト設計
3. **レポート生成** - 評価結果の可視化・出力
4. **バッチ処理** - 複数ファイルの一括評価