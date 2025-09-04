# runtime_adapters.py — адаптеры для различных рантаймов выполнения
import os
import json
import logging
import requests
import subprocess
import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from agent_specification import AgentSpecification, StepType, TriggerType

logger = logging.getLogger(__name__)

class ExecutionStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RUNNING = "running"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

@dataclass
class ExecutionResult:
    """Результат выполнения агента"""
    agent_id: str
    status: ExecutionStatus
    message: str = ""
    output: Dict[str, Any] = None
    execution_time: float = 0.0
    timestamp: str = ""
    runtime_used: str = ""
    
    def __post_init__(self):
        if self.output is None:
            self.output = {}
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class BaseRuntimeAdapter(ABC):
    """Базовый класс для всех адаптеров рантаймов"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = self.__class__.__name__.replace('RuntimeAdapter', '').lower()
        self.logger = logging.getLogger(f"Runtime.{self.name}")
        self._healthy = True
        self._last_health_check = datetime.now()
    
    @abstractmethod
    def is_available(self) -> bool:
        """Проверяет доступность рантайма"""
        pass
    
    @abstractmethod
    def deploy_agent(self, spec: AgentSpecification) -> str:
        """Развертывает агента в рантайме. Возвращает deployment_id"""
        pass
    
    @abstractmethod
    def execute_agent(self, deployment_id: str, trigger_data: Dict[str, Any] = None) -> ExecutionResult:
        """Выполняет агента. Возвращает результат выполнения"""
        pass
    
    @abstractmethod
    def remove_agent(self, deployment_id: str) -> bool:
        """Удаляет агента из рантайма"""
        pass
    
    def health_check(self) -> bool:
        """Проверка здоровья рантайма"""
        try:
            self._healthy = self.is_available()
            self._last_health_check = datetime.now()
            return self._healthy
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            self._healthy = False
            return False
    
    @property
    def is_healthy(self) -> bool:
        return self._healthy
    
    def get_capabilities(self) -> List[str]:
        """Возвращает список поддерживаемых возможностей"""
        return ["basic_execution"]

class LocalRuntimeAdapter(BaseRuntimeAdapter):
    """Адаптер для локального выполнения агентов"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.deployed_agents = {}
        self.max_concurrent = self.config.get('max_concurrent', 5)
        self.running_executions = {}
    
    def is_available(self) -> bool:
        """Локальный рантайм всегда доступен"""
        return True
    
    def deploy_agent(self, spec: AgentSpecification) -> str:
        """Сохраняет спецификацию агента для локального выполнения"""
        deployment_id = f"local_{spec.id}_{int(time.time())}"
        
        self.deployed_agents[deployment_id] = {
            'spec': spec,
            'deployed_at': datetime.now().isoformat(),
            'executions': 0
        }
        
        self.logger.info(f"Agent {spec.name} deployed locally with ID {deployment_id}")
        return deployment_id
    
    def execute_agent(self, deployment_id: str, trigger_data: Dict[str, Any] = None) -> ExecutionResult:
        """Выполняет агента локально"""
        if deployment_id not in self.deployed_agents:
            return ExecutionResult(
                agent_id=deployment_id,
                status=ExecutionStatus.FAILED,
                message="Agent not found in local runtime",
                runtime_used="local"
            )
        
        start_time = time.time()
        spec = self.deployed_agents[deployment_id]['spec']
        
        try:
            # Выполняем шаги агента последовательно
            context = trigger_data or {}
            
            for step in spec.steps:
                step_result = self._execute_step(step, context)
                if not step_result['success']:
                    return ExecutionResult(
                        agent_id=deployment_id,
                        status=ExecutionStatus.FAILED,
                        message=f"Step {step.name} failed: {step_result['error']}",
                        execution_time=time.time() - start_time,
                        runtime_used="local"
                    )
                
                # Обновляем контекст результатами шага
                context.update(step_result.get('output', {}))
            
            self.deployed_agents[deployment_id]['executions'] += 1
            
            return ExecutionResult(
                agent_id=deployment_id,
                status=ExecutionStatus.SUCCESS,
                message="Agent executed successfully",
                output=context,
                execution_time=time.time() - start_time,
                runtime_used="local"
            )
            
        except Exception as e:
            self.logger.error(f"Local execution failed: {e}")
            return ExecutionResult(
                agent_id=deployment_id,
                status=ExecutionStatus.FAILED,
                message=f"Execution error: {str(e)}",
                execution_time=time.time() - start_time,
                runtime_used="local"
            )
    
    def _execute_step(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет отдельный шаг агента"""
        try:
            if step.type == StepType.HTTP_REQUEST:
                return self._execute_http_request(step, context)
            elif step.type == StepType.PARSE_RSS:
                return self._execute_parse_rss(step, context)
            elif step.type == StepType.GENERATE_CONTENT:
                return self._execute_generate_content(step, context)
            elif step.type == StepType.SEND_MESSAGE:
                return self._execute_send_message(step, context)
            elif step.type == StepType.TRANSFORM_DATA:
                return self._execute_transform_data(step, context)
            else:
                return {
                    'success': False,
                    'error': f"Unsupported step type: {step.type}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Step execution error: {str(e)}"
            }
    
    def _execute_http_request(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет HTTP запрос"""
        config = step.config
        url = config.get('url', '')
        method = config.get('method', 'GET').upper()
        headers = config.get('headers', {})
        data = config.get('data', {})

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if method in ['POST', 'PUT', 'PATCH'] else None,
                timeout=config.get('timeout', 30)
            )

            # Исправлено: безопасная обработка JSON
            content_type = response.headers.get('content-type', '')
            response_data = None

            if content_type.startswith('application/json'):
                try:
                    response_data = response.json()
                except ValueError:
                    response_data = response.text
            else:
                response_data = response.text

            return {
                'success': True,
                'output': {
                    'status_code': response.status_code,
                    'response_data': response_data,
                    'headers': dict(response.headers)
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"HTTP request failed: {str(e)}"
            }
    
    def _execute_parse_rss(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """Парсит RSS ленту"""
        try:
            import feedparser
            
            url = step.config.get('url', '')
            max_items = step.config.get('max_items', 10)
            
            feed = feedparser.parse(url)
            
            items = []
            for entry in feed.entries[:max_items]:
                items.append({
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'description': entry.get('description', ''),
                    'published': entry.get('published', ''),
                    'author': entry.get('author', '')
                })
            
            return {
                'success': True,
                'output': {
                    'feed_title': feed.feed.get('title', ''),
                    'items': items,
                    'total_items': len(items)
                }
            }
        except ImportError:
            return {
                'success': False,
                'error': "feedparser library not available"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"RSS parsing failed: {str(e)}"
            }
    
    def _execute_generate_content(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """Генерирует контент через LLM"""
        try:
            # Заглушка для LLM - в реальной реализации здесь будет вызов LLM
            prompt = step.config.get('prompt', '')
            model = step.config.get('model', 'default')
            
            # Простая заглушка
            generated_content = f"Generated content for prompt: {prompt[:50]}..."
            
            return {
                'success': True,
                'output': {
                    'generated_content': generated_content,
                    'model_used': model
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Content generation failed: {str(e)}"
            }
    
    def _execute_send_message(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """Отправляет сообщение"""
        try:
            platform = step.config.get('platform', 'telegram')
            message = step.config.get('message', '')
            chat_id = step.config.get('chat_id', '')
            
            # Заглушка для отправки сообщений
            self.logger.info(f"Sending message to {platform} chat {chat_id}: {message[:100]}...")
            
            return {
                'success': True,
                'output': {
                    'message_sent': True,
                    'platform': platform,
                    'chat_id': chat_id
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Message sending failed: {str(e)}"
            }
    
    def _execute_transform_data(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """Трансформирует данные"""
        try:
            transformation = step.config.get('transformation', 'identity')
            input_data = context.get(step.config.get('input_key', 'data'), {})
            
            # Простые трансформации
            if transformation == 'to_upper':
                if isinstance(input_data, str):
                    result = input_data.upper()
                else:
                    result = str(input_data).upper()
            elif transformation == 'to_lower':
                if isinstance(input_data, str):
                    result = input_data.lower()
                else:
                    result = str(input_data).lower()
            else:
                result = input_data
            
            return {
                'success': True,
                'output': {
                    'transformed_data': result
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Data transformation failed: {str(e)}"
            }
    
    def remove_agent(self, deployment_id: str) -> bool:
        """Удаляет агента из локального рантайма"""
        if deployment_id in self.deployed_agents:
            del self.deployed_agents[deployment_id]
            self.logger.info(f"Agent {deployment_id} removed from local runtime")
            return True
        return False
    
    def get_capabilities(self) -> List[str]:
        return [
            "basic_execution",
            "http_requests",
            "rss_parsing",
            "content_generation",
            "message_sending",
            "data_transformation"
        ]

class N8NRuntimeAdapter(BaseRuntimeAdapter):
    """Адаптер для n8n рантайма"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_url = self.config.get('api_url', '')
        self.username = self.config.get('username', '')
        self.password = self.config.get('password', '')
        self.deployed_workflows = {}
    
    def is_available(self) -> bool:
        """Проверяет доступность n8n API"""
        if not self.api_url or not self.username:
            return False
        
        try:
            response = requests.get(
                f"{self.api_url}/workflows",
                auth=(self.username, self.password),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"n8n not available: {e}")
            return False
    
    def deploy_agent(self, spec: AgentSpecification) -> str:
        """Конвертирует спецификацию в n8n workflow и развертывает"""
        try:
            workflow = self._convert_spec_to_n8n_workflow(spec)
            
            response = requests.post(
                f"{self.api_url}/workflows",
                auth=(self.username, self.password),
                json=workflow,
                timeout=30
            )
            
            if response.status_code == 201:
                workflow_data = response.json()
                deployment_id = f"n8n_{workflow_data['id']}"
                
                self.deployed_workflows[deployment_id] = {
                    'workflow_id': workflow_data['id'],
                    'spec': spec,
                    'deployed_at': datetime.now().isoformat()
                }
                
                self.logger.info(f"Agent {spec.name} deployed to n8n with ID {deployment_id}")
                return deployment_id
            else:
                raise Exception(f"n8n deployment failed: {response.status_code} {response.text}")
                
        except Exception as e:
            self.logger.error(f"n8n deployment error: {e}")
            raise
    
    def _convert_spec_to_n8n_workflow(self, spec: AgentSpecification) -> Dict[str, Any]:
        """Конвертирует спецификацию агента в n8n workflow"""
        # Упрощенная конвертация - в реальной реализации будет более сложная логика
        workflow = {
            "name": spec.name,
            "active": True,
            "nodes": [],
            "connections": {}
        }
        
        # Добавляем триггер
        if spec.triggers:
            trigger = spec.triggers[0]  # Берем первый триггер
            if trigger.type == TriggerType.SCHEDULE:
                workflow["nodes"].append({
                    "parameters": {
                        "rule": {
                            "interval": [{"field": "cronExpression", "value": trigger.config.get("cron", "0 9 * * *")}]
                        }
                    },
                    "name": "Schedule Trigger",
                    "type": "n8n-nodes-base.cron",
                    "typeVersion": 1,
                    "position": [250, 300]
                })
        
        # Добавляем шаги
        for i, step in enumerate(spec.steps):
            node = self._convert_step_to_n8n_node(step, i)
            if node:
                workflow["nodes"].append(node)
        
        return workflow
    
    def _convert_step_to_n8n_node(self, step, index: int) -> Optional[Dict[str, Any]]:
        """Конвертирует шаг агента в n8n node"""
        base_position = [250 + (index + 1) * 200, 300]
        
        if step.type == StepType.HTTP_REQUEST:
            return {
                "parameters": {
                    "url": step.config.get("url", ""),
                    "options": {}
                },
                "name": step.name,
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 1,
                "position": base_position
            }
        elif step.type == StepType.PARSE_RSS:
            return {
                "parameters": {
                    "url": step.config.get("url", "")
                },
                "name": step.name,
                "type": "n8n-nodes-base.rssFeedRead",
                "typeVersion": 1,
                "position": base_position
            }
        
        return None
    
    def execute_agent(self, deployment_id: str, trigger_data: Dict[str, Any] = None) -> ExecutionResult:
        """Запускает выполнение n8n workflow"""
        if deployment_id not in self.deployed_workflows:
            return ExecutionResult(
                agent_id=deployment_id,
                status=ExecutionStatus.FAILED,
                message="Workflow not found in n8n runtime",
                runtime_used="n8n"
            )
        
        workflow_id = self.deployed_workflows[deployment_id]['workflow_id']
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.api_url}/workflows/{workflow_id}/execute",
                auth=(self.username, self.password),
                json=trigger_data or {},
                timeout=60
            )
            
            if response.status_code == 200:
                execution_data = response.json()
                return ExecutionResult(
                    agent_id=deployment_id,
                    status=ExecutionStatus.SUCCESS,
                    message="Workflow executed successfully",
                    output=execution_data,
                    execution_time=time.time() - start_time,
                    runtime_used="n8n"
                )
            else:
                return ExecutionResult(
                    agent_id=deployment_id,
                    status=ExecutionStatus.FAILED,
                    message=f"n8n execution failed: {response.status_code}",
                    execution_time=time.time() - start_time,
                    runtime_used="n8n"
                )
                
        except Exception as e:
            return ExecutionResult(
                agent_id=deployment_id,
                status=ExecutionStatus.FAILED,
                message=f"n8n execution error: {str(e)}",
                execution_time=time.time() - start_time,
                runtime_used="n8n"
            )
    
    def remove_agent(self, deployment_id: str) -> bool:
        """Удаляет workflow из n8n"""
        if deployment_id not in self.deployed_workflows:
            return False
        
        workflow_id = self.deployed_workflows[deployment_id]['workflow_id']
        
        try:
            response = requests.delete(
                f"{self.api_url}/workflows/{workflow_id}",
                auth=(self.username, self.password),
                timeout=30
            )
            
            if response.status_code == 200:
                del self.deployed_workflows[deployment_id]
                self.logger.info(f"Workflow {deployment_id} removed from n8n")
                return True
            else:
                self.logger.error(f"Failed to remove n8n workflow: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error removing n8n workflow: {e}")
            return False
    
    def get_capabilities(self) -> List[str]:
        return [
            "basic_execution",
            "http_requests",
            "rss_parsing",
            "scheduled_triggers",
            "webhook_triggers",
            "visual_workflows"
        ]

class DockerRuntimeAdapter(BaseRuntimeAdapter):
    """Адаптер для Docker рантайма"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.deployed_containers = {}
        self.base_image = self.config.get('base_image', 'python:3.9-slim')
    
    def is_available(self) -> bool:
        """Проверяет доступность Docker"""
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def deploy_agent(self, spec: AgentSpecification) -> str:
        """Создает Docker контейнер для агента"""
        try:
            container_name = f"agent_{spec.id}_{int(time.time())}"
            deployment_id = f"docker_{container_name}"

            # Создаем Dockerfile и скрипт выполнения
            self._create_agent_container(spec, container_name)

            # Собираем образ
            build_result = subprocess.run(
                ['docker', 'build', '-t', container_name, f'./docker_agents/{container_name}'],
                capture_output=True,
                text=True,
                timeout=300
            )

            # Исправлено: проверка результата сборки
            if build_result.returncode != 0:
                raise Exception(f"Docker build failed: {build_result.stderr}")

            self.deployed_containers[deployment_id] = {
                'container_name': container_name,
                'spec': spec,
                'deployed_at': datetime.now().isoformat()
            }

            self.logger.info(f"Agent {spec.name} deployed to Docker with ID {deployment_id}")
            return deployment_id

        except Exception as e:
            self.logger.error(f"Docker deployment error: {e}")
            raise
    
    def _create_agent_container(self, spec: AgentSpecification, container_name: str):
        """Создает файлы для Docker контейнера"""
        container_dir = f"./docker_agents/{container_name}"
        os.makedirs(container_dir, exist_ok=True)
        
        # Создаем Dockerfile
        dockerfile_content = f"""
FROM {self.base_image}

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY agent_script.py .
COPY agent_spec.json .

CMD ["python", "agent_script.py"]
"""
        
        with open(f"{container_dir}/Dockerfile", "w") as f:
            f.write(dockerfile_content)
        
        # Создаем requirements.txt
        requirements = ["requests", "feedparser", "schedule"]
        with open(f"{container_dir}/requirements.txt", "w") as f:
            f.write("\n".join(requirements))
        
        # Сохраняем спецификацию
        with open(f"{container_dir}/agent_spec.json", "w", encoding="utf-8") as f:
            f.write(spec.to_json())
        
        # Создаем скрипт выполнения
        script_content = """
import json
import sys
from datetime import datetime

def main():
    with open('agent_spec.json', 'r', encoding='utf-8') as f:
        spec = json.load(f)
    
    print(f"Executing agent: {spec['name']}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Здесь будет логика выполнения агента
    # Пока что просто выводим информацию
    for step in spec['steps']:
        print(f"Executing step: {step['name']} ({step['type']})")
    
    print("Agent execution completed")

if __name__ == "__main__":
    main()
"""
        
        with open(f"{container_dir}/agent_script.py", "w", encoding="utf-8") as f:
            f.write(script_content)
    
    def execute_agent(self, deployment_id: str, trigger_data: Dict[str, Any] = None) -> ExecutionResult:
        """Запускает Docker контейнер"""
        if deployment_id not in self.deployed_containers:
            return ExecutionResult(
                agent_id=deployment_id,
                status=ExecutionStatus.FAILED,
                message="Container not found in Docker runtime",
                runtime_used="docker"
            )
        
        container_name = self.deployed_containers[deployment_id]['container_name']
        start_time = time.time()
        
        try:
            # Запускаем контейнер
            run_result = subprocess.run(
                ['docker', 'run', '--rm', container_name],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if run_result.returncode == 0:
                return ExecutionResult(
                    agent_id=deployment_id,
                    status=ExecutionStatus.SUCCESS,
                    message="Container executed successfully",
                    output={"stdout": run_result.stdout, "stderr": run_result.stderr},
                    execution_time=time.time() - start_time,
                    runtime_used="docker"
                )
            else:
                return ExecutionResult(
                    agent_id=deployment_id,
                    status=ExecutionStatus.FAILED,
                    message=f"Container execution failed: {run_result.stderr}",
                    execution_time=time.time() - start_time,
                    runtime_used="docker"
                )
                
        except Exception as e:
            return ExecutionResult(
                agent_id=deployment_id,
                status=ExecutionStatus.FAILED,
                message=f"Docker execution error: {str(e)}",
                execution_time=time.time() - start_time,
                runtime_used="docker"
            )
    
    def remove_agent(self, deployment_id: str) -> bool:
        """Удаляет Docker образ и файлы агента"""
        if deployment_id not in self.deployed_containers:
            return False
        
        container_name = self.deployed_containers[deployment_id]['container_name']
        
        try:
            # Удаляем образ
            subprocess.run(
                ['docker', 'rmi', container_name],
                capture_output=True,
                timeout=60
            )
            
            # Удаляем файлы
            import shutil
            container_dir = f"./docker_agents/{container_name}"
            if os.path.exists(container_dir):
                shutil.rmtree(container_dir)
            
            del self.deployed_containers[deployment_id]
            self.logger.info(f"Docker agent {deployment_id} removed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing Docker agent: {e}")
            return False
    
    def get_capabilities(self) -> List[str]:
        return [
            "basic_execution",
            "isolation",
            "scalability",
            "resource_limits",
            "containerization"
        ]