# prompt_templates_loader.py
import os
import json
from typing import Dict, List, Union
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Template:
    id: str
    title: str
    description: str
    content: str
    tags: List[str]
    metadata: Dict[str, Union[str, List, Dict]]
    schema_version: str = "1.0"

class PromptTemplateLoader:
    def __init__(self, template_dir: str = "./prompt_templates"):
        self.template_dir = template_dir
        os.makedirs(self.template_dir, exist_ok=True)
        self.error_log = "template_errors.log"
        with open(self.error_log, "w", encoding="utf-8") as f:
            f.write(f"=== Template Error Log ({datetime.now().isoformat()}) ===\n")

    def _log_error(self, filename: str, error: str):
        with open(self.error_log, "a", encoding="utf-8") as log:
            log.write(f"[{datetime.now().isoformat()}] {filename} — {error}\n")

    def load_all_templates(self) -> List[Template]:
        templates: List[Template] = []
        for filename in os.listdir(self.template_dir):
            if filename.lower().endswith(".json"):
                try:
                    template = self._load_single_template(filename)
                    if template.schema_version not in {"1.0", "1.1"}:
                        raise ValueError(f"Unsupported schema version: {template.schema_version}")
                    templates.append(template)
                except Exception as e:
                    self._log_error(filename, str(e))
        return templates

    def _load_single_template(self, filename: str) -> Template:
        path = os.path.join(self.template_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        version = data.get("schema_version", "1.0")
        if version == "1.0":
            self._validate(data, ["template_id", "title", "default_post"])
            content = data["default_post"].get("content", "")
            tags = data["default_post"].get("tags", [])
            metadata = {
                "schedule": data["default_post"].get("schedule", {}),
                "engagement": data["default_post"].get("engagement", {}),
                "content_guidelines": data.get("content_guidelines", {}),
            }
        else:  # 1.1
            self._validate(data, ["template_id", "title", "description", "content_strategy"])
            # допускаем различную структуру 1.1 — вытаскиваем «template» если есть
            content = data.get("content_strategy", {}).get("template", "") or data.get("default_post", {}).get("content", "")
            tags = data.get("default_post", {}).get("tags", [])
            metadata = {
                "schedule": data.get("default_post", {}).get("schedule", {}),
                "engagement": data.get("default_post", {}).get("engagement", {}),
                "content_guidelines": data.get("content_guidelines", {}),
            }

        return Template(
            id=data["template_id"],
            title=data.get("title", "Без названия"),
            description=data.get("description", ""),
            content=content,
            tags=tags,
            metadata=metadata,
            schema_version=version,
        )

    @staticmethod
    def _validate(obj: Dict, required: List[str]):
        for field in required:
            if field not in obj:
                raise ValueError(f"Отсутствует обязательное поле '{field}'")

def load_prompt_templates() -> List[Template]:
    return PromptTemplateLoader().load_all_templates()
