# agent_specification.py — нейтральный формат спецификации агентов
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import yaml
from datetime import datetime
import uuid

class TriggerType(Enum):
    SCHEDULE = "schedule"
    HTTP_WEBHOOK = "http_webhook"
    RSS_FEED = "rss_feed"
    FILE_WATCH = "file_watch"
    MESSAGE_QUEUE = "message_queue"
    MANUAL = "manual"

class StepType(Enum):
    HTTP_REQUEST = "http_request"
    TRANSFORM_DATA = "transform_data"
    FILTER_DATA = "filter_data"
    DATABASE_QUERY = "database_query"
    SEND_MESSAGE = "send_message"
    GENERATE_CONTENT = "generate_content"
    PARSE_RSS = "parse_rss"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    DELAY = "delay"
    CUSTOM_CODE = "custom_code"

class RuntimeType(Enum):
    N8N = "n8n"
    LOCAL = "local"
    DOCKER = "docker"
    TEMPORAL = "temporal"
    PREFECT = "prefect"
    SERVERLESS = "serverless"
    KUBERNETES = "kubernetes"

@dataclass
class AgentTrigger:
    """Триггер агента"""
    type: TriggerType
    config: Dict[str, Any]
    enabled: bool = True
    
    # Примеры конфигураций:
    # schedule: {"cron": "0 9,15,20 * * *", "timezone": "UTC"}
    # rss_feed: {"url": "https://example.com/rss", "check_interval": "1h"}
    # http_webhook: {"path": "/webhook/agent123", "method": "POST"}

@dataclass
class AgentStep:
    """Шаг выполнения агента"""
    id: str
    name: str
    type: StepType
    config: Dict[str, Any]
    inputs: Dict[str, str] = None  # Маппинг входных данных
    outputs: Dict[str, str] = None  # Маппинг выходных данных
    error_handling: Dict[str, Any] = None
    retry_config: Dict[str, Any] = None
    condition: Optional[str] = None  # Условие выполнения
    
    def __post_init__(self):
        if self.inputs is None:
            self.inputs = {}
        if self.outputs is None:
            self.outputs = {}
        if self.error_handling is None:
            self.error_handling = {"on_error": "continue", "max_retries": 3}
        if self.retry_config is None:
            self.retry_config = {"max_attempts": 3, "backoff": "exponential"}

@dataclass
class AgentSLA:
    """SLA требования агента"""
    max_execution_time: int = 300  # секунды
    max_memory_mb: int = 512
    max_cpu_percent: int = 80
    priority: str = "normal"  # low, normal, high, critical

@dataclass
class AgentSecrets:
    """Ссылки на секреты"""
    references: Dict[str, str] = None  # {"telegram_token": "secret://telegram/bot_token"}
    
    def __post_init__(self):
        if self.references is None:
            self.references = {}

@dataclass
class AgentMetadata:
    """Метаданные агента"""
    created_at: datetime
    created_by: str
    version: str = "1.0.0"
    tags: List[str] = None
    description: str = ""
    documentation_url: str = ""
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class AgentSpecification:
    """Полная спецификация агента в нейтральном формате"""
    id: str
    name: str
    owner: str
    triggers: List[AgentTrigger]
    steps: List[AgentStep]
    metadata: AgentMetadata
    sla: AgentSLA = None
    secrets: AgentSecrets = None
    runtime_preferences: List[RuntimeType] = None
    environment_variables: Dict[str, str] = None
    
    def __post_init__(self):
        if self.sla is None:
            self.sla = AgentSLA()
        if self.secrets is None:
            self.secrets = AgentSecrets()
        if self.runtime_preferences is None:
            self.runtime_preferences = [RuntimeType.LOCAL, RuntimeType.N8N]
        if self.environment_variables is None:
            self.environment_variables = {}
        if not self.id:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        def convert_value(obj):
            if isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, '__dict__'):
                return asdict(obj)
            return obj
        
        return json.loads(json.dumps(asdict(self), default=convert_value))
    
    def to_json(self, indent: int = 2) -> str:
        """Конвертация в JSON"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def to_yaml(self) -> str:
        """Конвертация в YAML"""
        return yaml.dump(self.to_dict(), default_flow_style=False, allow_unicode=True)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentSpecification':
        """Создание из словаря"""
        # Конвертируем enum строки обратно в enum
        if 'triggers' in data:
            for trigger in data['triggers']:
                if 'type' in trigger:
                    trigger['type'] = TriggerType(trigger['type'])
        
        if 'steps' in data:
            for step in data['steps']:
                if 'type' in step:
                    step['type'] = StepType(step['type'])
        
        if 'runtime_preferences' in data:
            data['runtime_preferences'] = [RuntimeType(rt) for rt in data['runtime_preferences']]
        
        if 'metadata' in data and 'created_at' in data['metadata']:
            data['metadata']['created_at'] = datetime.fromisoformat(data['metadata']['created_at'])
        
        # Создаем объекты из словарей
        if 'triggers' in data:
            data['triggers'] = [AgentTrigger(**trigger) for trigger in data['triggers']]
        
        if 'steps' in data:
            data['steps'] = [AgentStep(**step) for step in data['steps']]
        
        if 'metadata' in data:
            data['metadata'] = AgentMetadata(**data['metadata'])
        
        if 'sla' in data:
            data['sla'] = AgentSLA(**data['sla'])
        
        if 'secrets' in data:
            data['secrets'] = AgentSecrets(**data['secrets'])
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentSpecification':
        """Создание из JSON"""
        return cls.from_dict(json.loads(json_str))
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'AgentSpecification':
        """Создание из YAML"""
        return cls.from_dict(yaml.safe_load(yaml_str))
    
    def validate(self) -> List[str]:
        """Валидация спецификации"""
        errors = []

        if not self.name:
            errors.append("Имя агента не может быть пустым")

        if not self.owner:
            errors.append("Владелец агента не может быть пустым")

        if not self.triggers:
            errors.append("Агент должен иметь хотя бы один триггер")

        if not self.steps:
            errors.append("Агент должен иметь хотя бы один шаг")

        # Проверяем уникальность ID шагов
        step_ids = [step.id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            errors.append("ID шагов должны быть уникальными")

        # Проверяем ссылки между шагами
        for step in self.steps:
            if step.inputs:
                for input_key, input_ref in step.inputs.items():
                    if input_ref.startswith("step:"):
                        ref_step_id = input_ref.split(":")[1]
                        if ref_step_id not in step_ids:
                            errors.append(f"Шаг {step.id} ссылается на несуществующий шаг {ref_step_id}")

        # Добавлена валидация cron выражений
        import re
        for trigger in self.triggers:
            if trigger.type == TriggerType.SCHEDULE:
                cron_expr = trigger.config.get("cron", "")
                # Простая проверка формата cron выражения
                if cron_expr and not re.match(r'^[\d\*\-\,\/\s]+$', cron_expr):
                    errors.append(f"Неверный формат cron выражения: {cron_expr}")

        # Проверка значений SLA
        if self.sla:
            if self.sla.max_execution_time <= 0:
                errors.append("Максимальное время выполнения должно быть положительным")
            if self.sla.max_memory_mb <= 0:
                errors.append("Максимальный объем памяти должен быть положительным")
            if self.sla.max_cpu_percent <= 0 or self.sla.max_cpu_percent > 100:
                errors.append("Процент CPU должен быть в диапазоне 1-100")
            if self.sla.priority not in ["low", "normal", "high", "critical"]:
                errors.append("Приоритет должен быть одним из: low, normal, high, critical")

        return errors

# Фабрика для создания стандартных агентов
class AgentSpecificationFactory:
    """Фабрика для создания типовых спецификаций агентов"""
    
    @staticmethod
    def create_rss_monitor(
        name: str,
        owner: str,
        rss_url: str,
        telegram_chat_id: str,
        schedule: str = "0 9,15,20 * * *",
        style: str = "информативный стиль"
    ) -> AgentSpecification:
        """Создает спецификацию RSS монитора"""
        
        agent_id = str(uuid.uuid4())
        
        triggers = [
            AgentTrigger(
                type=TriggerType.SCHEDULE,
                config={"cron": schedule, "timezone": "UTC"}
            )
        ]
        
        steps = [
            AgentStep(
                id="fetch_rss",
                name="Получить RSS ленту",
                type=StepType.PARSE_RSS,
                config={
                    "url": rss_url,
                    "max_items": 5,
                    "include_content": True
                },
                outputs={"rss_items": "rss_data"}
            ),
            AgentStep(
                id="filter_new",
                name="Фильтровать новые элементы",
                type=StepType.FILTER_DATA,
                config={
                    "filter_expression": "item.published > last_check_time",
                    "memory_key": f"rss_last_check_{agent_id}"
                },
                inputs={"items": "step:fetch_rss:rss_data"},
                outputs={"filtered_items": "new_items"}
            ),
            AgentStep(
                id="generate_content",
                name="Генерировать контент",
                type=StepType.GENERATE_CONTENT,
                config={
                    "prompt_template": f"Перепиши новость в {style}. Заголовок: {{title}}, Содержание: {{content}}",
                    "model": "mistral",
                    "max_tokens": 500
                },
                inputs={"items": "step:filter_new:new_items"},
                outputs={"generated_content": "content_data"}
            ),
            AgentStep(
                id="send_telegram",
                name="Отправить в Telegram",
                type=StepType.SEND_MESSAGE,
                config={
                    "platform": "telegram",
                    "chat_id": telegram_chat_id,
                    "parse_mode": "HTML"
                },
                inputs={"content": "step:generate_content:content_data"},
                secrets=AgentSecrets(references={"telegram_token": "secret://telegram/bot_token"})
            )
        ]
        
        return AgentSpecification(
            id=agent_id,
            name=name,
            owner=owner,
            triggers=triggers,
            steps=steps,
            metadata=AgentMetadata(
                created_at=datetime.now(),
                created_by=owner,
                description=f"RSS монитор для {rss_url}",
                tags=["rss", "telegram", "content"]
            ),
            sla=AgentSLA(max_execution_time=180),
            runtime_preferences=[RuntimeType.LOCAL, RuntimeType.N8N, RuntimeType.DOCKER]
        )
    
    @staticmethod
    def create_content_generator(
        name: str,
        owner: str,
        template_id: str,
        telegram_chat_id: str,
        topics: List[str],
        schedule: str = "0 */4 * * *"
    ) -> AgentSpecification:
        """Создает спецификацию генератора контента"""
        
        agent_id = str(uuid.uuid4())
        
        triggers = [
            AgentTrigger(
                type=TriggerType.SCHEDULE,
                config={"cron": schedule, "timezone": "UTC"}
            )
        ]
        
        steps = [
            AgentStep(
                id="select_topic",
                name="Выбрать тему",
                type=StepType.CUSTOM_CODE,
                config={
                    "code": f"import random; topic = random.choice({topics})",
                    "output_variable": "selected_topic"
                },
                outputs={"topic": "current_topic"}
            ),
            AgentStep(
                id="generate_content",
                name="Генерировать контент",
                type=StepType.GENERATE_CONTENT,
                config={
                    "template_id": template_id,
                    "model": "mistral",
                    "max_tokens": 800
                },
                inputs={"topic": "step:select_topic:current_topic"},
                outputs={"generated_content": "content_data"}
            ),
            AgentStep(
                id="send_telegram",
                name="Отправить в Telegram",
                type=StepType.SEND_MESSAGE,
                config={
                    "platform": "telegram",
                    "chat_id": telegram_chat_id,
                    "parse_mode": "HTML"
                },
                inputs={"content": "step:generate_content:content_data"}
            )
        ]
        
        return AgentSpecification(
            id=agent_id,
            name=name,
            owner=owner,
            triggers=triggers,
            steps=steps,
            metadata=AgentMetadata(
                created_at=datetime.now(),
                created_by=owner,
                description=f"Генератор контента по темам: {', '.join(topics)}",
                tags=["content", "telegram", "generator"]
            ),
            runtime_preferences=[RuntimeType.LOCAL, RuntimeType.DOCKER]
        )

# Пример использования
if __name__ == "__main__":
    # Создаем RSS монитор
    rss_agent = AgentSpecificationFactory.create_rss_monitor(
        name="DTF RSS Monitor",
        owner="kolybel_user",
        rss_url="https://dtf.ru/rss",
        telegram_chat_id="-1002669388680",
        style="молодежный стиль для геймеров"
    )
    
    # Валидируем
    errors = rss_agent.validate()
    if errors:
        print("Ошибки валидации:", errors)
    else:
        print("✅ Спецификация валидна")
    
    # Сохраняем в разных форматах
    print("\n📄 JSON:")
    print(rss_agent.to_json())
    
    print("\n📄 YAML:")
    print(rss_agent.to_yaml())