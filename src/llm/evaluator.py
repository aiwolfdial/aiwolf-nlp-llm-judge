import os
from typing import Any
from dotenv import load_dotenv
from pathlib import Path
from jinja2 import Template
import json

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionDeveloperMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel

from src.models.evaluation import EvaluationCriteria

import yaml


class Evaluator:
    """評価クラス."""

    def __init__(self, config: dict[str, Any]):
        try:
            env_path = Path(config["path"]["env"])
            prompt_yml_path = Path(config["llm"]["prompt_yml"])
            self.model = config["llm"]["model"]
        except KeyError as e:
            raise KeyError(f"必要な設定キーが見つかりません: {e}")

        if not env_path.is_file():
            raise FileNotFoundError(f"環境変数ファイルが見つかりません: {env_path}")

        if not prompt_yml_path.is_file():
            raise FileNotFoundError(
                f"プロンプトYAMLファイルが見つかりません: {prompt_yml_path}"
            )

        try:
            with open(prompt_yml_path, "r", encoding="utf-8") as f:
                self.prompt_template = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"プロンプトYAMLファイルの解析に失敗しました: {e}")

        load_dotenv(env_path)
        api_key = os.environ.get("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEYが設定されていません")

        self.client = OpenAI(api_key=api_key)

    def evaluation(
        self,
        criteria: EvaluationCriteria,
        log: list[dict[str, Any]],
        output_structure: type[BaseModel],
    ) -> BaseModel:
        print(self._developer_message())
        print(self._user_message(criteria=criteria, log=log))
        return

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                self._developer_message(),
                self._user_message(criteria=criteria, log=log),
            ],
            response_format=output_structure,
        )

        return response.choices[0].message.parsed

    def _developer_message(self) -> ChatCompletionDeveloperMessageParam:
        template: Template = Template(self.prompt_template["developer"])

        message: ChatCompletionDeveloperMessageParam = {
            "content": template.render().strip(),
            "role": "developer",
        }
        return message

    def _user_message(
        self, criteria: EvaluationCriteria, log: list[dict[str, Any]]
    ) -> ChatCompletionUserMessageParam:
        template: Template = Template(self.prompt_template["user"])

        message: ChatCompletionUserMessageParam = {
            "content": template.render(
                criteria_description=criteria.description,
                log=json.dumps(log, ensure_ascii=False),
            ).strip(),
            "role": "user",
        }
        return message
