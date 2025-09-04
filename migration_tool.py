# migration_tool.py — инструмент для миграции автономных агентов в новую архитектуру
import json
import logging
from typing import Dict, List, Any
from datetime import datetime

from agents_v2 import AgentManager
from agent_specification import AgentSpecification

logger = logging.getLogger(__name__)

class AgentMigrationTool:
    """Инструмент для миграции агентов из старых форматов в новую архитектуру"""
    
    def __init__(self, agent_manager: AgentManager = None):
        self.agent_manager = agent_manager or AgentManager()
        self.migration_log = []
    
    def migrate_autonomous_agents_from_file(self, file_path: str) -> List[str]:
        """Мигрирует автономных агентов из файла конфигурации"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                agents_config = json.load(f)
            
            migrated_agents = []
            
            if isinstance(agents_config, list):
                # Список агентов
                for agent_config in agents_config:
                    try:
                        agent_id = self._migrate_single_autonomous_agent(agent_config)
                        migrated_agents.append(agent_id)
                    except Exception as e:
                        logger.error(f"Ошибка миграции агента {agent_config.get('name', 'Unknown')}: {e}")
            
            elif isinstance(agents_config, dict):
                # Один агент
                agent_id = self._migrate_single_autonomous_agent(agents_config)
                migrated_agents.append(agent_id)
            
            logger.info(f"Мигрировано {len(migrated_agents)} агентов из {file_path}")
            return migrated_agents
            
        except Exception as e:
            logger.error(f"Ошибка чтения файла {file_path}: {e}")
            return []
    
    def _migrate_single_autonomous_agent(self, agent_config: Dict[str, Any]) -> str:
        """Мигрирует одного автономного агента"""
        agent_id = self.agent_manager.migrate_from_autonomous_agent(agent_config)
        
        self.migration_log.append({
            "original_id": agent_config.get('id', ''),
            "original_name": agent_config.get('name', ''),
            "new_agent_id": agent_id,
            "migration_time": datetime.now().isoformat(),
            "status": "success"
        })
        
        return agent_id
    
    def migrate_n8n_workflows_from_approved_goals(self, approved_goals_dir: str = "approved_goals") -> List[str]:
        """Мигрирует n8n workflows из папки approved_goals"""
        import os
        
        migrated_agents = []
        
        if not os.path.exists(approved_goals_dir):
            logger.warning(f"Папка {approved_goals_dir} не найдена")
            return migrated_agents
        
        for filename in os.listdir(approved_goals_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(approved_goals_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Пытаемся извлечь JSON из содержимого (может быть обернут в текст)
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        json_content = content[json_start:json_end]
                        workflow_data = json.loads(json_content)
                        
                        # Конвертируем n8n workflow в спецификацию агента
                        agent_id = self._migrate_n8n_workflow(workflow_data, filename)
                        if agent_id:
                            migrated_agents.append(agent_id)
                
                except Exception as e:
                    logger.error(f"Ошибка миграции файла {filename}: {e}")
        
        logger.info(f"Мигрировано {len(migrated_agents)} n8n workflows")
        return migrated_agents
    
    def _migrate_n8n_workflow(self, workflow_data: Dict[str, Any], source_file: str) -> str:
        """Конвертирует n8n workflow в спецификацию агента"""
        import time
        from agent_specification import (
            AgentTrigger, AgentStep, AgentMetadata,
            TriggerType, StepType, RuntimeType
        )

        # Извлекаем информацию из workflow
        workflow_name = workflow_data.get('name', f'Мигрированный из {source_file}')

        # Создаем триггеры (улучшенная логика)
        triggers = []
        nodes = workflow_data.get('nodes', [])

        # Ищем триггерные ноды
        for node in nodes:
            node_type = node.get('type', '').lower()
            if 'trigger' in node_type or 'webhook' in node_type or 'cron' in node_type:
                # Обработка cron триггера
                if 'cron' in node_type:
                    cron_expr = "0 9,15,20 * * *"  # дефолтное значение
                    parameters = node.get('parameters', {})
                    if 'rule' in parameters:
                        rule = parameters['rule']
                        if 'interval' in rule:
                            intervals = rule['interval']
                            for interval in intervals:
                                if interval.get('field') == 'cronExpression':
                                    cron_expr = interval.get('value', cron_expr)

                    triggers.append(AgentTrigger(
                        type=TriggerType.SCHEDULE,
                        config={"cron": cron_expr}
                    ))
                # Обработка webhook триггера
                elif 'webhook' in node_type:
                    triggers.append(AgentTrigger(
                        type=TriggerType.HTTP_WEBHOOK,
                        config={"path": f"/webhook/{source_file.replace('.json', '')}"}
                    ))

        # Если не найдено триггеров, создаем дефолтный
        if not triggers:
            triggers.append(AgentTrigger(
                type=TriggerType.SCHEDULE,
                config={"cron": "0 9,15,20 * * *"}
            ))

        # Создаем шаги на основе nodes
        steps = []

        for i, node in enumerate(nodes):
            node_type = node.get('type', '')
            node_name = node.get('name', f'Шаг {i+1}')
            parameters = node.get('parameters', {})

            # RSS node
            if 'rss' in node_type.lower() or parameters.get('url', '').endswith('/rss'):
                steps.append(AgentStep(
                    id=f"rss_step_{i}",
                    name=node_name,
                    type=StepType.PARSE_RSS,
                    config={
                        "url": parameters.get('url', 'https://dtf.ru/rss'),
                        "max_items": 5
                    }
                ))

            # HTTP request node
            elif 'http' in node_type.lower() or 'webhook' in node_type.lower():
                method = parameters.get('method', 'GET')
                url = parameters.get('url', '')

                steps.append(AgentStep(
                    id=f"http_step_{i}",
                    name=node_name,
                    type=StepType.HTTP_REQUEST,
                    config={
                        "url": url,
                        "method": method,
                        "headers": parameters.get('headers', {}),
                        "data": parameters.get('body', {})
                    }
                ))

            # Telegram message node
            elif 'telegram' in node_type.lower() or 'message' in node_name.lower():
                chat_id = parameters.get('chatId', '-1002669388680')

                steps.append(AgentStep(
                    id=f"telegram_step_{i}",
                    name=node_name,
                    type=StepType.SEND_MESSAGE,
                    config={
                        "platform": "telegram",
                        "chat_id": chat_id
                    }
                ))

            # Code node
            elif 'code' in node_type.lower() or 'function' in node_type.lower():
                code = parameters.get('code', '')
                if code:
                    steps.append(AgentStep(
                        id=f"code_step_{i}",
                        name=node_name,
                        type=StepType.CUSTOM_CODE,
                        config={
                            "code": code
                        }
                    ))

        # Если нет шагов, создаем базовые
        if not steps:
            steps = [
                AgentStep(
                    id="default_rss",
                    name="Получить RSS",
                    type=StepType.PARSE_RSS,
                    config={"url": "https://dtf.ru/rss", "max_items": 5}
                ),
                AgentStep(
                    id="default_content",
                    name="Генерировать контент",
                    type=StepType.GENERATE_CONTENT,
                    config={"style": "информативный стиль"}
                ),
                AgentStep(
                    id="default_send",
                    name="Отправить сообщение",
                    type=StepType.SEND_MESSAGE,
                    config={"platform": "telegram", "chat_id": "-1002669388680"}
                )
            ]

        # Создаем спецификацию
        spec = AgentSpecification(
            id=f"migrated_{source_file.replace('.json', '')}_{int(time.time())}",
            name=workflow_name,
            owner="migrated_user",
            triggers=triggers,
            steps=steps,
            metadata=AgentMetadata(
                created_at=datetime.now(),
                created_by="migration_tool",
                description=f"Мигрированный n8n workflow из {source_file}",
                tags=["migrated", "n8n", "workflow"]
            ),
            runtime_preferences=[RuntimeType.LOCAL, RuntimeType.N8N]
        )

        # Развертываем агента
        agent_id = self.agent_manager.orchestrator.deploy_agent(spec)

        self.migration_log.append({
            "source_file": source_file,
            "workflow_name": workflow_name,
            "new_agent_id": agent_id,
            "migration_time": datetime.now().isoformat(),
            "status": "success"
        })

        logger.info(f"n8n workflow '{workflow_name}' мигрирован в агента {agent_id}")
        return agent_id
    
    def generate_migration_report(self) -> Dict[str, Any]:
        """Генерирует отчет о миграции"""
        successful_migrations = [log for log in self.migration_log if log.get('status') == 'success']
        
        return {
            "total_migrations": len(self.migration_log),
            "successful_migrations": len(successful_migrations),
            "failed_migrations": len(self.migration_log) - len(successful_migrations),
            "migration_details": self.migration_log,
            "report_generated_at": datetime.now().isoformat()
        }
    
    def save_migration_report(self, file_path: str = "migration_report.json"):
        """Сохраняет отчет о миграции в файл"""
        report = self.generate_migration_report()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Отчет о миграции сохранен в {file_path}")

def main():
    """Основная функция для запуска миграции"""
    logging.basicConfig(level=logging.INFO)
    
    # Создаем инструмент миграции
    migration_tool = AgentMigrationTool()
    
    print("🔄 Запуск миграции агентов в новую архитектуру...")
    
    # Мигрируем n8n workflows из approved_goals
    print("\n📁 Миграция n8n workflows из approved_goals...")
    n8n_agents = migration_tool.migrate_n8n_workflows_from_approved_goals()
    print(f"✅ Мигрировано {len(n8n_agents)} n8n workflows")
    
    # Генерируем отчет
    print("\n📊 Генерация отчета о миграции...")
    migration_tool.save_migration_report()
    
    report = migration_tool.generate_migration_report()
    print(f"\n📈 Результаты миграции:")
    print(f"   Всего попыток: {report['total_migrations']}")
    print(f"   Успешных: {report['successful_migrations']}")
    print(f"   Неудачных: {report['failed_migrations']}")
    
    # Показываем статус агентов
    print("\n🤖 Статус мигрированных агентов:")
    agent_manager = migration_tool.agent_manager
    agents = agent_manager.list_agents()
    
    for agent in agents:
        print(f"   {agent['name']} ({agent['agent_id']}) - {agent['primary_runtime']}")
    
    print("\n✅ Миграция завершена!")

if __name__ == "__main__":
    main()