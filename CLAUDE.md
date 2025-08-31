# AIWolf NLP LLM Judge

AIWolf CSVファイルを生成AIで評価するシステム

## プロジェクト概要

このプロジェクトは、AIWolfゲームのログ（CSVファイル）を生成AI（LLM）に渡し、事前定義された評価基準に沿って評価を行うシステムです。5人戦と13人戦の両方に対応し、共通評価項目とゲーム形式固有の評価項目を独立して評価します。評価方式はランキング形式で、各プレイヤーを相対的に順位付けします。

## ファイル構成

```
aiwolf-nlp-llm-judge/
├── CLAUDE.md                       # プロジェクト仕様書
├── README.md                       # プロジェクト概要
├── main.py                         # エントリーポイント
├── pyproject.toml                  # プロジェクト設定・依存関係
├── uv.lock                         # 依存関係ロックファイル
├── config/
│   ├── evaluation_criteria.yaml    # 評価基準設定
│   ├── prompts.yaml                 # プロンプトテンプレート
│   └── settings.yaml               # メイン設定ファイル
├── data/
│   ├── input/                      # 入力データディレクトリ
│   └── output/                     # 出力データディレクトリ
└── src/
    ├── __init__.py
    ├── cli.py                      # CLIインターフェース
    ├── processor.py                # バッチ処理（クラスベース）
    ├── aiwolf_log/                 # ログファイル解析モジュール
    │   ├── __init__.py
    │   ├── parser.py              # CSVパーサー
    │   ├── csv_reader.py          # CSV読み込み
    │   ├── json_reader.py         # JSON読み込み
    │   └── game_log.py            # ログ・JSONペア管理
    ├── utils/                     # ユーティリティモジュール
    │   ├── __init__.py
    │   └── game_log_finder.py     # ゲームログ検索機能
    ├── evaluator/                 # 評価モジュール
    │   ├── __init__.py
    │   ├── config_loader.py       # 設定読み込み
    │   ├── game_detector.py       # ゲーム形式検出
    │   └── base_evaluator.py      # 評価器基底クラス
    ├── llm/                       # LLM関連モジュール
    │   ├── __init__.py
    │   ├── evaluator.py           # LLM評価器
    │   └── formatter.py           # ゲームログフォーマッター
    └── models/                    # データモデル
        ├── __init__.py
        ├── game.py                # ゲーム関連モデル
        └── evaluation/            # 評価関連モデル
            ├── __init__.py
            ├── criteria.py        # 評価基準（ランキング形式）
            ├── result.py          # 評価結果管理
            ├── config.py          # 評価設定
            └── llm_response.py    # LLMレスポンス構造
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

### 4. ゲームログ管理
- ログファイル（*.log）とJSONファイル（*.json）のペア管理
- ファイル名による自動マッチング（例: `game1.log` ↔ `game1.json`）
- 統合的なファイルアクセスインターフェース

### 5. バッチ処理
- クラスベースの並列処理システム（`GameProcessor`、`BatchProcessor`）
- 複数ゲームログの一括評価
- プロセス間並列処理とスレッド並列処理の組み合わせによる効率的な処理

## 設定ファイル

### settings.yaml
メイン設定ファイル。評価基準ファイルのパスを管理。

```yaml
path:
  env: config/.env
  evaluation_criteria: config/evaluation_criteria.yaml

llm:
  prompt_yml: config/prompts.yaml
  model: "gpt-5"

game:
  format: "main_match"  # main_match または self_match
  player_count: 5  # プレイヤー数（5, 13など）

processing:
  input_dir: "data/input"    # 入力ディレクトリ
  output_dir: "data/output"  # 出力ディレクトリ
  max_workers: 4             # プロセス並列処理数
```

### evaluation_criteria.yaml
評価基準の詳細設定。

```yaml
common_criteria:
  - name: "natural_expression"
    description: "発話表現は自然か"
    ranking_type: "comparative"
    applicable_games: [5, 13]
    
  - name: "contextual_dialogue"
    description: "文脈を踏まえた対話は自然か"
    ranking_type: "comparative"
    applicable_games: [5, 13]
    
  - name: "logical_consistency"
    description: "発話内容は一貫しており矛盾がないか"
    ranking_type: "comparative"
    applicable_games: [5, 13]
    
  - name: "action_consistency"
    description: "ゲーム行動（投票、襲撃、占いなど）は対話内容を踏まえているか"
    ranking_type: "comparative"
    applicable_games: [5, 13]
  
  - name: "character_consistency"
    description: "発話表現は豊かか。与えられたプロフィールと矛盾なく、エージェントごとに一貫して豊かなキャラクター性が出ているか"
    ranking_type: "comparative"
    applicable_games: [5, 13]

game_specific_criteria:
  13_player:
    - name: "team_play"
      description: "チームプレイができているか"
      ranking_type: "comparative"
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

### ゲームログ管理 (aiwolf_log/game_log.py)
```python
class AIWolfGameLog:
    """AIWolfのゲームログ（ログファイルとJSONファイルのペア）を管理するクラス"""
    
    def __init__(self, input_dir: Path, file_name: str):
        """初期化
        Args:
            input_dir: 入力ディレクトリのパス
            file_name: ファイル名（拡張子なし）
        """
    
    @classmethod
    def from_input_dir(cls, input_dir: Path, file_name: str) -> Self:
        """入力ディレクトリとファイル名からインスタンスを作成"""
    
    @property
    def game_id(self) -> str:
        """ゲームIDをJSONから取得"""
    
    def get_csv_reader(self, config: dict[str, Any]) -> AIWolfCSVReader:
        """CSVリーダーを取得"""
    
    def get_json_reader(self) -> AIWolfJSONReader:
        """JSONリーダーを取得"""
    
    def get_character_info(self) -> dict[str, Any]:
        """キャラクター情報を取得"""
    
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

### 2. ゲーム情報取得
```python
from src.evaluator.game_detector import GameDetector

csv_path = Path("data/game_log.csv")
settings_path = Path("config/settings.yaml")
game_info = GameDetector.detect_game_format(csv_path, settings_path)
print(f"ゲーム形式: {game_info.game_format.value}, プレイヤー数: {game_info.player_count}")
```

### 3. ゲームログの読み込み
```python
from src.aiwolf_log import AIWolfGameLog

# 単一のゲームログを読み込み
input_dir = Path("data/input")
file_name = "game1"  # 拡張子なし
game_log = AIWolfGameLog.from_input_dir(input_dir, file_name)

# キャラクター情報の取得
character_info = game_log.get_character_info()

# CSVリーダーの取得
with game_log.get_csv_reader(config) as reader:
    while line := reader.read_next_line():
        # 行の処理
        pass
```

### 4. 複数ゲームログの一括取得
```python
# すべてのゲームログを検索
from src.utils.game_log_finder import find_all_game_logs
game_logs = find_all_game_logs(Path("data/input"))
for game_log in game_logs:
    print(f"Processing game: {game_log.game_id}")
```

### 5. バッチ処理実行
```python
from src.processor import BatchProcessor

# バッチ処理の実行
processor = BatchProcessor(config)
result = processor.process_all_games()

print(f"成功率: {result.success_rate:.2%}")
print(f"処理済み: {result.completed}/{result.total}")
```

### 6. 単一ゲーム処理
```python
from src.processor import GameProcessor

# 単一ゲームの処理
game_processor = GameProcessor(config)
success = game_processor.process(game_log, output_dir)
```

## 技術仕様

- **Python バージョン**: 3.11以上
- **型ヒント**: Python 3.10+ の union 演算子 (`|`) を使用
- **データクラス**: `@dataclass` を活用した型安全な設計
- **Enum**: 定数値の管理（`GameFormat`, `RankingType`, `CriteriaCategory`）
- **Pydantic**: LLMレスポンスのバリデーション（`BaseModel`）
- **型安全性**: `Any`型を可能な限り排除し、具体的な型ヒントを使用

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
- [x] ファイル管理機能
  - [x] CSVリーダーの実装（`csv_reader.py`）
  - [x] JSONリーダーの実装（`json_reader.py`）
  - [x] ゲームログ管理（`AIWolfGameLog`）
  - [x] ログ・JSONファイルの自動マッチング
- [x] バッチ処理システム
  - [x] クラスベースの並列処理実装（`processor.py`）
    - [x] `GameProcessor`: 単一ゲーム処理
    - [x] `BatchProcessor`: バッチ処理管理
    - [x] `ProcessingConfig`, `ProcessingResult`: 型安全な設定・結果管理
  - [x] マルチスレッド評価実装（各評価基準を並列実行）
  - [x] CLIインターフェース（`cli.py`）
  - [x] プロジェクトエントリーポイント（`main.py`）
- [x] 型安全性の改善
  - [x] `processor.py`の型ヒント改善（`Any`型を具体的な型に変更）
  - [x] `game_log.py`の設定パラメータ型改善
  - [x] `llm/evaluator.py`および`llm/formatter.py`の型ヒント改善
  - [x] 既存の`EvaluationConfig`、`GameInfo`型の活用
- [x] バグ修正
  - [x] 設定ファイルパスの重複問題修正（`config/config/evaluation_criteria.yaml` → `config/evaluation_criteria.yaml`）
  - [x] CSVリーダーのコンテキストマネージャー対応修正
- [x] LLM評価エンジン実装
  - [x] ゲームログのJSONL形式変換（`llm/formatter.py`）
  - [x] LLM評価器の基本実装（`llm/evaluator.py`）
- [ ] プロンプト設計
- [ ] レポート生成機能
- [ ] テスト実装

### バッチ処理 (processor.py)
```python
@dataclass(frozen=True)
class ProcessingConfig:
    """処理設定を表すデータクラス"""
    input_dir: Path
    output_dir: Path
    max_workers: int
    game_format: GameFormat

@dataclass
class ProcessingResult:
    """処理結果を表すデータクラス"""
    total: int = 0
    completed: int = 0
    failed: int = 0
    
    @property
    def success_rate(self) -> float:
        """成功率を計算"""

class GameProcessor:
    """単一ゲームの処理を担当するクラス"""
    
    def process(self, game_log: AIWolfGameLog, output_dir: Path) -> bool:
        """ゲームログを処理して評価結果を出力"""
        
    def _execute_evaluations(
        self,
        evaluation_config: EvaluationConfig,
        game_info: GameInfo,
        formatted_data: list[dict[str, Any]]
    ) -> EvaluationResult:
        """評価を並列実行（ThreadPoolExecutor使用）"""

class BatchProcessor:
    """バッチ処理を管理するクラス"""
    
    def process_all_games(self) -> ProcessingResult:
        """すべてのゲームログを並列処理"""
        
    def _execute_parallel_processing(self, game_logs: list[AIWolfGameLog]) -> ProcessingResult:
        """並列処理を実行（ProcessPoolExecutor使用）"""
```

## データファイル配置

ゲームログファイルは以下の構造で配置します：

```
data/
├── input/
│   ├── log/                   # ゲームログファイル (*.log)
│   │   ├── game1.log
│   │   ├── game2.log
│   │   └── ...
│   └── json/                  # キャラクター情報ファイル (*.json)
│       ├── game1.json         # game1.logに対応
│       ├── game2.json         # game2.logに対応
│       └── ...
└── output/                     # 評価結果の出力先
```

**重要**: 
- ログファイル（*.log）とJSONファイル（*.json）は、拡張子前の名前が完全一致している必要があります
- `AIWolfGameLog.find_all_game_logs()` は入力ディレクトリを再帰的に検索し、ログ・JSONペアを自動検出します

## CLIインターフェース

### 基本的な使用方法
```bash
# プロジェクトの実行（設定ファイル指定）
uv run python3 main.py -c config/settings.yaml

# または直接CLIを実行
python -m src.cli

# デフォルト設定での実行
python main.py
```

### 実装状況
- **main.py**: エントリーポイント、`src.cli.main()` を呼び出し
- **src/cli.py**: コマンドライン引数の解析、設定読み込み、バッチ処理の実行
- **src/processor.py**: 実際の並列処理実装（クラスベース）

## 今後の実装予定

1. **LLM評価エンジン** - 実際にLLMを呼び出して評価を行う
2. **プロンプト管理** - 評価基準別のプロンプト設計
3. **レポート生成** - 評価結果の可視化・出力