import yaml
from pathlib import Path
from typing import Dict, List

from .models import EvaluationConfig, EvaluationCriteria, GameFormat


class ConfigLoader:
    """評価設定ファイルを読み込むクラス"""
    
    @staticmethod
    def load_from_settings(settings_path: Path) -> EvaluationConfig:
        """settings.yamlから評価設定を読み込む
        
        Args:
            settings_path: settings.yamlファイルのパス
            
        Returns:
            EvaluationConfig: 読み込まれた評価設定
            
        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            ValueError: 設定ファイルの形式が不正な場合
        """
        if not settings_path.exists():
            raise FileNotFoundError(f"Settings file not found: {settings_path}")
        
        try:
            with settings_path.open('r', encoding='utf-8') as f:
                settings_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format in settings: {e}")
        
        # evaluation_criteria のパスを取得
        evaluation_criteria_path = settings_data.get("path", {}).get("evaluation_criteria")
        if not evaluation_criteria_path:
            raise ValueError("evaluation_criteria path not found in settings")
        
        # 相対パスの場合、settings.yamlからの相対パスとして解釈
        criteria_path = settings_path.parent / evaluation_criteria_path
        
        return ConfigLoader.load_evaluation_config(criteria_path)
    
    @staticmethod
    def load_evaluation_config(config_path: Path) -> EvaluationConfig:
        """評価設定ファイルを読み込んでEvaluationConfigオブジェクトを作成
        
        Args:
            config_path: 設定ファイルのパス
            
        Returns:
            EvaluationConfig: 読み込まれた評価設定
            
        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            ValueError: 設定ファイルの形式が不正な場合
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        try:
            with config_path.open('r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
        
        # 共通評価基準の読み込み
        common_criteria = ConfigLoader._load_criteria_list(
            config_data.get("common_criteria", [])
        )
        
        # ゲーム固有評価基準の読み込み
        game_specific_criteria = {}
        specific_data = config_data.get("game_specific_criteria", {})
        
        for game_format_str, criteria_list in specific_data.items():
            try:
                game_format = GameFormat(game_format_str)
                game_specific_criteria[game_format] = ConfigLoader._load_criteria_list(criteria_list)
            except ValueError:
                raise ValueError(f"Unknown game format: {game_format_str}")
        
        return EvaluationConfig(
            common_criteria=common_criteria,
            game_specific_criteria=game_specific_criteria
        )
    
    @staticmethod
    def _load_criteria_list(criteria_data: List[Dict]) -> List[EvaluationCriteria]:
        """評価基準リストを読み込む
        
        Args:
            criteria_data: YAML から読み込まれた評価基準データ
            
        Returns:
            List[EvaluationCriteria]: 評価基準のリスト
            
        Raises:
            ValueError: 設定データが不正な場合
        """
        criteria_list = []
        
        for criteria_dict in criteria_data:
            try:
                name = criteria_dict["name"]
                description = criteria_dict["description"]
                scale = criteria_dict["scale"]
                
                min_value = scale["min"]
                max_value = scale["max"]
                score_type = scale["type"]
                
                if score_type not in ["integer", "float"]:
                    raise ValueError(f"Invalid score type: {score_type}")
                
                criteria = EvaluationCriteria(
                    name=name,
                    description=description,
                    min_value=min_value,
                    max_value=max_value,
                    score_type=score_type
                )
                
                criteria_list.append(criteria)
                
            except KeyError as e:
                raise ValueError(f"Missing required field in criteria: {e}")
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid criteria data: {e}")
        
        return criteria_list