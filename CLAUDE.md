# AIWolf NLP LLM Judge

AIWolf CSVファイルを生成AIで評価するシステム

## プロジェクト概要

このプロジェクトは、AIWolfゲームのログ（CSVファイル）を生成AI（LLM）に渡し、事前定義された評価基準に沿って評価を行うシステムです。5人戦と13人戦の両方に対応し、共通評価項目とゲーム形式固有の評価項目を独立して評価します。評価方式はランキング形式で、各プレイヤーを相対的に順位付けします。

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
│   │   ├── reader.py              # CSV読み込み
│   │   └── writer.py              # CSV書き込み
│   ├── evaluator/                 # 評価モジュール
│   │   ├── config_loader.py       # 設定読み込み
│   │   ├── game_detector.py       # ゲーム形式検出
│   │   └── base_evaluator.py      # 評価器基底クラス
│   └── models/                    # データモデル
│       ├── game.py                # ゲーム関連モデル
│       └── evaluation/            # 評価関連モデル
│           ├── criteria.py        # 評価基準（ランキング形式）
│           ├── result.py          # 評価結果管理
│           ├── config.py          # 評価設定
│           └── llm_response.py    # LLMレスポンス構造
├── main.py
└── src/main.py
```

## 主要機能

### 1. ゲーム形式の設定読み込み
- 設定ファイルからプレイヤー数とゲーム形式を読み込み
- 5人戦、13人戦などの任意のプレイヤー数に対応可能

### 2. 柔軟な評価基準システム
- **共通評価項目**: 全ゲーム形式で共通の評価基準
- **固有評価項目**: ゲーム形式別の特別な評価基準
- **独立評価**: 各項目は重み付けなしで独立して評価

### 3. ランキング評価
- プレイヤー間の相対的な順位付け
- `ORDINAL`（順序付け）または`COMPARATIVE`（比較ベース）のランキング形式
- 各評価基準で独立したランキング

## 設定ファイル

### settings.yaml
メイン設定ファイル。評価基準ファイルのパスを管理。

```yaml
path:
  evaluation_criteria: config/evaluation_criteria.yaml
game:
  player_count: 5        # プレイヤー数（5, 13など）
  format: "main_match"   # ゲーム形式（self_match, main_match）
llm:
  model: "gpt-5"
```

### evaluation_criteria.yaml
評価基準の詳細設定。

```yaml
common_criteria:
  - name: "natural_expression"
    description: "発話表現は自然か"
    ranking_type: "ordinal"
    applicable_games: [5, 13]
    
  - name: "contextual_dialogue"
    description: "文脈を踏まえた対話は自然か"
    ranking_type: "ordinal"
    applicable_games: [5, 13]
    
  - name: "logical_consistency"
    description: "発話内容は一貫しており矛盾がないか"
    ranking_type: "ordinal"
    applicable_games: [5, 13]
    
  - name: "action_consistency"
    description: "ゲーム行動（投票、襲撃、占いなど）は対話内容を踏まえているか"
    ranking_type: "ordinal"
    applicable_games: [5, 13]
  
  - name: "character_consistency"
    description: "発話表現は豊かか。与えられたプロフィールと矛盾なく、エージェントごとに一貫して豊かなキャラクター性が出ているか"
    ranking_type: "ordinal"
    applicable_games: [5, 13]

game_specific_criteria:
  13_player:
    - name: "team_play"
      description: "チームプレイができているか"
      ranking_type: "ordinal"
      applicable_games: [13]
```

## データ構造

### ゲーム関連 (models/game.py)
```python
class GameFormat(Enum):
    SELF_MATCH = "self_match"    # 自己対戦
    MAIN_MATCH = "main_match"    # メイン対戦

@dataclass
class GameInfo:
    game_format: GameFormat  # ゲーム形式
    player_count: int        # プレイヤー数
    game_id: str = ""        # ゲームID
```

### 評価基準 (models/evaluation/criteria.py)
```python
class RankingType(Enum):
    ORDINAL = "ordinal"          # 順序付け（1位、2位...）
    COMPARATIVE = "comparative"  # 比較ベース（A > B > C）

class CriteriaCategory(Enum):
    COMMON = "common"              # 全ゲーム形式共通
    GAME_SPECIFIC = "game_specific"  # ゲーム形式固有

@dataclass
class EvaluationCriteria:
    name: str                      # 評価基準名
    description: str               # 評価基準の説明
    ranking_type: RankingType      # ランキングの型
    applicable_games: list[int]    # 適用されるプレイヤー数のリスト
    category: CriteriaCategory     # 評価基準のカテゴリー
```

### LLMレスポンス (models/evaluation/llm_response.py)
```python
class EvaluationElement(BaseModel):
    player_name: str = Field(description="評価対象者の名前")
    reasoning: str = Field(description="各評価対象に対する順位付けの理由")
    ranking: int = Field(description="評価対象者の順位(他のプレイヤーとの重複はなし)")

class EvaluationLLMResponse(BaseModel):
    rankings: list[EvaluationElement] = Field(description="各プレイヤーに対する評価")
```

### 評価結果 (models/evaluation/result.py)
```python
class EvaluationResult(list[EvaluationLLMResponse]):
    """評価結果全体を表すクラス（EvaluationLLMResponseのリストを継承）"""
    
    def __init__(self):
        super().__init__()
        self._criteria_index: dict[str, int] = {}  # criteria_name -> index
    
    def add_response(self, criteria_name: str, response: EvaluationLLMResponse) -> None:
        """評価レスポンスを追加"""
        
    def get_by_criteria(self, criteria_name: str) -> EvaluationLLMResponse:
        """評価基準名でレスポンスを取得"""
        
    def get_all_criteria_names(self) -> list[str]:
        """すべての評価基準名を取得"""
        
    def has_criteria(self, criteria_name: str) -> bool:
        """指定した評価基準が存在するか確認"""
```

### 評価設定 (models/evaluation/config.py)
```python
class EvaluationConfig(list[EvaluationCriteria]):
    """評価設定を表すクラス（EvaluationCriteriaのリストを継承）"""

    def get_criteria_for_game(self, player_count: int) -> list[EvaluationCriteria]:
        """指定されたプレイヤー数の評価基準を取得"""
        
    def get_criteria_by_name(self, criteria_name: str, player_count: int) -> EvaluationCriteria:
        """基準名で評価基準を取得"""
```

## 使用方法

### 1. 設定読み込み
```python
from pathlib import Path
from evaluator.config_loader import ConfigLoader

# settings.yamlから評価設定を読み込み
settings_path = Path("config/settings.yaml")
evaluation_config = ConfigLoader.load_from_settings(settings_path)
```

### 2. ゲーム情報取得
```python
from evaluator.game_detector import GameDetector

csv_path = Path("data/game_log.csv")
settings_path = Path("config/settings.yaml")
game_info = GameDetector.detect_game_format(csv_path, settings_path)
print(f"ゲーム形式: {game_info.game_format.value}, プレイヤー数: {game_info.player_count}")
```

### 3. 評価実行
```python
# 評価器の実装が完了後
evaluator = SomeEvaluator(evaluation_config)
result = evaluator.evaluate(csv_path, game_info)
```

## 技術仕様

- **Python バージョン**: 3.11以上
- **型ヒント**: Python 3.10+ の union 演算子 (`|`) を使用
- **データクラス**: `@dataclass` を活用した型安全な設計
- **Enum**: 定数値の管理（`GameFormat`, `RankingType`, `CriteriaCategory`）
- **Pydantic**: LLMレスポンスのバリデーション（`BaseModel`）

## 開発ステータス

- [x] 基本設計
- [x] データ構造設計
  - [x] モデルの階層化（`models/`, `models/evaluation/`）
  - [x] Enumによる型安全性の向上
- [x] 設定ファイル作成
- [x] ゲーム情報取得機能
- [x] 設定読み込み機能
- [x] 評価器基底クラス
- [x] データ構造リファクタリング
  - [x] ParticipantNum Enumの削除
  - [x] player_countによる統一
  - [x] スコア評価からランキング評価への変更
  - [x] EvaluationRankingの削除とEvaluationResultへの統合
  - [x] EvaluationRecordsの削除とEvaluationResultへの機能統合
- [ ] LLM評価エンジン実装
- [ ] プロンプト設計
- [ ] レポート生成機能
- [ ] テスト実装

## 今後の実装予定

1. **LLM評価エンジン** - 実際にLLMを呼び出して評価を行う
2. **プロンプト管理** - 評価基準別のプロンプト設計
3. **レポート生成** - 評価結果の可視化・出力
4. **バッチ処理** - 複数ファイルの一括評価