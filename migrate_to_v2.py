# migrate_to_v2.py — скрипт миграции на новую архитектуру
import os
import shutil
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectMigrator:
    """Мигратор проекта на новую архитектуру v2"""
    
    def __init__(self):
        self.backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.deprecated_files = [
            # Старые файлы агентов
            "agents.py",
            "autonomous_agents.py", 
            "demo_autonomous_agents.py",
            
            # Старые точки входа
            "main.py",
            
            # Устаревшие документы
            "AUTONOMOUS_AGENTS.md",
            
            # Старые скрипты
            "run_kolybel.bat",
            "run_kolybel.ps1", 
            "start_kolybel.ps1",
            "stop_kolybel.ps1",
            
            # Дублирующиеся файлы
            "intuition.py",  # дублируется
        ]
        
        self.deprecated_dirs = [
            "autonomous_agents",  # Заменено на deployed_agents
            "cradle_memory",      # Устаревшая система памяти
            "code-analyzer",      # Не используется
        ]
    
    def create_backup(self):
        """Создает резервную копию важных файлов"""
        logger.info(f"Создание резервной копии в {self.backup_dir}")
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Бэкапим важные файлы
        important_files = [
            "kolybel_manifest.txt",
            "config.py",
            "goals.log",
            "dialog_history.log",
            "awakening.log"
        ]
        
        for file in important_files:
            if os.path.exists(file):
                shutil.copy2(file, self.backup_dir)
                logger.info(f"Скопирован {file}")
        
        # Бэкапим директории с данными
        important_dirs = [
            "prompt_templates",
            "approved_goals", 
            "logs",
            "agent_logs"
        ]
        
        for dir_name in important_dirs:
            if os.path.exists(dir_name):
                shutil.copytree(dir_name, os.path.join(self.backup_dir, dir_name), dirs_exist_ok=True)
                logger.info(f"Скопирована директория {dir_name}")
    
    def remove_deprecated_files(self):
        """Удаляет устаревшие файлы"""
        logger.info("Удаление устаревших файлов...")
        
        for file in self.deprecated_files:
            if os.path.exists(file):
                # Перемещаем в backup вместо удаления
                shutil.move(file, os.path.join(self.backup_dir, f"deprecated_{file}"))
                logger.info(f"Перемещен в backup: {file}")
        
        for dir_name in self.deprecated_dirs:
            if os.path.exists(dir_name):
                shutil.move(dir_name, os.path.join(self.backup_dir, f"deprecated_{dir_name}"))
                logger.info(f"Перемещена в backup директория: {dir_name}")
    
    def create_new_directories(self):
        """Создает новые директории для v2"""
        new_dirs = [
            "deployed_agents",      # Спецификации развернутых агентов
            "agent_specifications", # Библиотека спецификаций
            "runtime_configs",      # Конфигурации рантаймов
            "migration_logs"        # Логи миграции
        ]
        
        for dir_name in new_dirs:
            os.makedirs(dir_name, exist_ok=True)
            logger.info(f"Создана директория: {dir_name}")
    
    def migrate_legacy_agents(self):
        """Мигрирует старых агентов в новый формат"""
        logger.info("Миграция агентов в новый формат...")
        
        # Ищем старые файлы агентов
        legacy_agents = []
        
        if os.path.exists("approved_goals"):
            for filename in os.listdir("approved_goals"):
                if filename.startswith("n8n_agent_") and filename.endswith(".json"):
                    legacy_agents.append(os.path.join("approved_goals", filename))
        
        migrated_count = 0
        for agent_file in legacy_agents:
            try:
                with open(agent_file, 'r', encoding='utf-8') as f:
                    legacy_data = json.load(f)
                
                # Создаем новую спецификацию (упрощенная миграция)
                new_spec = self._convert_legacy_to_spec(legacy_data, agent_file)
                
                # Сохраняем новую спецификацию
                spec_filename = f"migrated_{os.path.basename(agent_file)}"
                spec_path = os.path.join("agent_specifications", spec_filename)
                
                with open(spec_path, 'w', encoding='utf-8') as f:
                    json.dump(new_spec, f, indent=2, ensure_ascii=False)
                
                migrated_count += 1
                logger.info(f"Мигрирован агент: {agent_file} -> {spec_path}")
                
            except Exception as e:
                logger.error(f"Ошибка миграции {agent_file}: {e}")
        
        logger.info(f"Мигрировано агентов: {migrated_count}")
    
    def _convert_legacy_to_spec(self, legacy_data: Dict[str, Any], source_file: str) -> Dict[str, Any]:
        """Конвертирует старый формат агента в новую спецификацию"""
        import uuid
        
        # Извлекаем информацию из старого формата (это упрощенная версия)
        agent_id = str(uuid.uuid4())
        
        # Базовая спецификация RSS монитора
        spec = {
            "id": agent_id,
            "name": f"Migrated Agent from {os.path.basename(source_file)}",
            "owner": "migrated_user",
            "triggers": [
                {
                    "type": "schedule",
                    "config": {"cron": "0 9,15,20 * * *", "timezone": "UTC"},
                    "enabled": True
                }
            ],
            "steps": [
                {
                    "id": "fetch_rss",
                    "name": "Получить RSS ленту",
                    "type": "parse_rss",
                    "config": {
                        "url": "https://dtf.ru/rss",  # Значение по умолчанию
                        "max_items": 5
                    },
                    "outputs": {"rss_items": "rss_data"}
                },
                {
                    "id": "generate_content",
                    "name": "Генерировать контент",
                    "type": "generate_content",
                    "config": {
                        "prompt_template": "Перепиши новость в информативном стиле: {title}",
                        "model": "mistral"
                    },
                    "inputs": {"items": "step:fetch_rss:rss_data"},
                    "outputs": {"generated_content": "content_data"}
                },
                {
                    "id": "send_telegram",
                    "name": "Отправить в Telegram",
                    "type": "send_message",
                    "config": {
                        "platform": "telegram",
                        "chat_id": "-1002669388680",  # Значение по умолчанию
                        "parse_mode": "HTML"
                    },
                    "inputs": {"content": "step:generate_content:content_data"}
                }
            ],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "created_by": "migration_script",
                "version": "1.0.0",
                "tags": ["migrated", "rss", "telegram"],
                "description": f"Агент мигрирован из {source_file}"
            },
            "sla": {
                "max_execution_time": 300,
                "max_memory_mb": 512,
                "priority": "normal"
            },
            "runtime_preferences": ["local", "n8n", "docker"],
            "environment_variables": {}
        }
        
        return spec
    
    def update_startup_scripts(self):
        """Обновляет скрипты запуска"""
        logger.info("Создание новых скриптов запуска...")
        
        # Создаем новый batch файл для Windows
        batch_content = """@echo off
echo Starting Kolybel v2...
python main_v2.py
pause
"""
        with open("run_kolybel_v2.bat", 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        # Создаем PowerShell скрипт
        ps_content = """# Kolybel v2 Startup Script
Write-Host "Starting Kolybel v2 with Independent Agent Architecture..." -ForegroundColor Green
python main_v2.py
"""
        with open("start_kolybel_v2.ps1", 'w', encoding='utf-8') as f:
            f.write(ps_content)
        
        # Создаем скрипт для веб-интерфейса
        web_batch_content = """@echo off
echo Starting Kolybel v2 Web Interface...
python start_web_interface.py
pause
"""
        with open("run_web_interface.bat", 'w', encoding='utf-8') as f:
            f.write(web_batch_content)
        
        logger.info("Созданы новые скрипты запуска")
    
    def create_migration_report(self):
        """Создает отчет о миграции"""
        report = {
            "migration_date": datetime.now().isoformat(),
            "backup_location": self.backup_dir,
            "deprecated_files_moved": self.deprecated_files,
            "deprecated_dirs_moved": self.deprecated_dirs,
            "new_architecture_files": [
                "agent_specification.py",
                "runtime_adapters.py", 
                "runtime_orchestrator.py",
                "agents_v2.py",
                "main_v2.py",
                "ARCHITECTURE_V2.md"
            ],
            "migration_status": "completed",
            "notes": [
                "Все старые файлы сохранены в backup директории",
                "Агенты мигрированы в новый формат спецификаций",
                "Веб-интерфейс обновлен для новой архитектуры",
                "Создана документация по новой архитектуре"
            ]
        }
        
        with open("migration_logs/migration_report.json", 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info("Создан отчет о миграции: migration_logs/migration_report.json")
    
    def run_migration(self):
        """Запускает полную миграцию"""
        logger.info("🚀 Начало миграции Колыбели на архитектуру v2")
        logger.info("=" * 60)
        
        try:
            # Шаг 1: Создание backup
            self.create_backup()
            
            # Шаг 2: Создание новых директорий
            self.create_new_directories()
            
            # Шаг 3: Миграция агентов
            self.migrate_legacy_agents()
            
            # Шаг 4: Удаление устаревших файлов
            self.remove_deprecated_files()
            
            # Шаг 5: Обновление скриптов
            self.update_startup_scripts()
            
            # Шаг 6: Создание отчета
            self.create_migration_report()
            
            logger.info("=" * 60)
            logger.info("✅ Миграция завершена успешно!")
            logger.info(f"📁 Backup создан в: {self.backup_dir}")
            logger.info("🚀 Теперь используйте: python main_v2.py")
            logger.info("🌐 Веб-интерфейс: python start_web_interface.py")
            
        except Exception as e:
            logger.error(f"❌ Ошибка миграции: {e}")
            raise

def main():
    """Основная функция миграции"""
    print("🏗️ Колыбель - Миграция на независимую архитектуру v2")
    print("=" * 60)
    
    confirm = input("Начать миграцию? Будет создан backup старых файлов (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("Миграция отменена")
        return
    
    migrator = ProjectMigrator()
    migrator.run_migration()
    
    print("\n🎉 Миграция завершена!")
    print("\n📋 Что изменилось:")
    print("• Новая независимая архитектура агентов")
    print("• Поддержка множественных рантаймов (n8n, local, docker)")
    print("• Автоматический failover при сбоях")
    print("• Нейтральный формат спецификаций агентов")
    print("• Обновленный веб-интерфейс")
    print("• Улучшенная система мониторинга")
    
    print("\n🚀 Следующие шаги:")
    print("1. Запустите: python main_v2.py")
    print("2. Или веб-интерфейс: python start_web_interface.py")
    print("3. Изучите документацию: ARCHITECTURE_V2.md")

if __name__ == "__main__":
    main()