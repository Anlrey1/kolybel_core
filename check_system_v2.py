# check_system_v2.py — проверка системы Колыбели v2
import os
import sys
import importlib
import json
from datetime import datetime
from typing import Dict, List, Tuple

class SystemChecker:
    """Проверяет готовность системы Колыбели v2"""
    
    def __init__(self):
        self.results = []
        self.errors = []
        self.warnings = []
    
    def check_python_version(self) -> bool:
        """Проверяет версию Python"""
        version = sys.version_info
        if version.major >= 3 and version.minor >= 9:
            self.results.append(f"✅ Python {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            self.errors.append(f"❌ Python {version.major}.{version.minor} (требуется 3.9+)")
            return False
    
    def check_required_files(self) -> bool:
        """Проверяет наличие основных файлов"""
        required_files = [
            # Основные модули v2
            "agent_specification.py",
            "runtime_adapters.py", 
            "runtime_orchestrator.py",
            "agents_v2.py",
            "main_v2.py",
            
            # Веб-интерфейс
            "web_interface.py",
            "start_web_interface.py",
            
            # Основные модули
            "memory_core.py",
            "core.py",
            "config.py",
            "llm.py",
            
            # Конфигурация
            "requirements.txt",
            "kolybel_manifest.txt",
            
            # Документация
            "README.md",
            "ARCHITECTURE_V2.md",
            "WEB_INTERFACE.md"
        ]
        
        missing_files = []
        for file in required_files:
            if os.path.exists(file):
                self.results.append(f"✅ {file}")
            else:
                missing_files.append(file)
                self.errors.append(f"❌ Отсутствует: {file}")
        
        return len(missing_files) == 0
    
    def check_required_directories(self) -> bool:
        """Проверяет наличие необходимых директорий"""
        required_dirs = [
            "templates",
            "static/css",
            "static/js",
            "prompt_templates",
            "logs"
        ]
        
        optional_dirs = [
            "deployed_agents",
            "agent_specifications", 
            "runtime_configs",
            "migration_logs"
        ]
        
        missing_dirs = []
        for dir_name in required_dirs:
            if os.path.exists(dir_name):
                self.results.append(f"✅ {dir_name}/")
            else:
                missing_dirs.append(dir_name)
                self.errors.append(f"❌ Отсутствует директория: {dir_name}")
        
        for dir_name in optional_dirs:
            if os.path.exists(dir_name):
                self.results.append(f"✅ {dir_name}/ (опциональная)")
            else:
                self.warnings.append(f"⚠️ Отсутствует опциональная директория: {dir_name}")
        
        return len(missing_dirs) == 0
    
    def check_dependencies(self) -> bool:
        """Проверяет установленные зависимости"""
        required_packages = [
            "flask",
            "flask_socketio",
            "requests",
            "schedule",
            "feedparser",
            "sentence_transformers",
            "chromadb",
            "pyyaml"
        ]
        
        optional_packages = [
            "docker",
            "aiogram"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                importlib.import_module(package.replace('-', '_'))
                self.results.append(f"✅ {package}")
            except ImportError:
                missing_packages.append(package)
                self.errors.append(f"❌ Не установлен пакет: {package}")
        
        for package in optional_packages:
            try:
                importlib.import_module(package.replace('-', '_'))
                self.results.append(f"✅ {package} (опциональный)")
            except ImportError:
                self.warnings.append(f"⚠️ Не установлен опциональный пакет: {package}")
        
        return len(missing_packages) == 0
    
    def check_configuration(self) -> bool:
        """Проверяет конфигурацию"""
        config_ok = True
        
        # Проверяем config.py
        try:
            import config
            self.results.append("✅ config.py загружен")
            
            # Проверяем основные настройки
            if hasattr(config, 'TELEGRAM_TOKEN'):
                if config.TELEGRAM_TOKEN and config.TELEGRAM_TOKEN != "your_token_here":
                    self.results.append("✅ TELEGRAM_TOKEN настроен")
                else:
                    self.warnings.append("⚠️ TELEGRAM_TOKEN не настроен")
            
            if hasattr(config, 'TELEGRAM_CHANNEL_ID'):
                if config.TELEGRAM_CHANNEL_ID:
                    self.results.append("✅ TELEGRAM_CHANNEL_ID настроен")
                else:
                    self.warnings.append("⚠️ TELEGRAM_CHANNEL_ID не настроен")
                    
        except Exception as e:
            self.errors.append(f"❌ Ошибка загрузки config.py: {e}")
            config_ok = False
        
        # Проверяем переменные окружения для n8n
        n8n_url = os.getenv('N8N_API_URL')
        if n8n_url:
            self.results.append(f"✅ N8N_API_URL: {n8n_url}")
        else:
            self.warnings.append("⚠️ N8N_API_URL не настроен (n8n адаптер будет недоступен)")
        
        return config_ok
    
    def check_external_services(self) -> bool:
        """Проверяет доступность внешних сервисов"""
        services_ok = True
        
        # Проверяем Docker
        try:
            import docker
            client = docker.from_env()
            client.ping()
            self.results.append("✅ Docker доступен")
        except Exception as e:
            self.warnings.append(f"⚠️ Docker недоступен: {e}")
        
        # Проверяем n8n (если настроен)
        n8n_url = os.getenv('N8N_API_URL')
        if n8n_url:
            try:
                import requests
                response = requests.get(f"{n8n_url}/workflows", timeout=5)
                if response.status_code == 200:
                    self.results.append("✅ n8n API доступен")
                else:
                    self.warnings.append(f"⚠️ n8n API недоступен (код: {response.status_code})")
            except Exception as e:
                self.warnings.append(f"⚠️ n8n API недоступен: {e}")
        
        return services_ok
    
    def check_system_modules(self) -> bool:
        """Проверяет загрузку основных модулей системы"""
        modules_ok = True
        
        core_modules = [
            "memory_core",
            "agent_specification", 
            "runtime_adapters",
            "runtime_orchestrator",
            "agents_v2"
        ]
        
        for module_name in core_modules:
            try:
                importlib.import_module(module_name)
                self.results.append(f"✅ {module_name}.py загружен")
            except Exception as e:
                self.errors.append(f"❌ Ошибка загрузки {module_name}.py: {e}")
                modules_ok = False
        
        return modules_ok
    
    def test_basic_functionality(self) -> bool:
        """Тестирует базовую функциональность"""
        try:
            # Тест создания спецификации агента
            from agent_specification import AgentSpecificationFactory
            
            spec = AgentSpecificationFactory.create_rss_monitor(
                name="Test Agent",
                owner="test_user",
                rss_url="https://example.com/rss",
                telegram_chat_id="@test"
            )
            
            errors = spec.validate()
            if not errors:
                self.results.append("✅ Создание спецификации агента работает")
            else:
                self.errors.append(f"❌ Ошибки валидации спецификации: {errors}")
                return False
            
            # Тест сериализации
            json_str = spec.to_json()
            yaml_str = spec.to_yaml()
            
            if json_str and yaml_str:
                self.results.append("✅ Сериализация JSON/YAML работает")
            else:
                self.errors.append("❌ Ошибка сериализации")
                return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"❌ Ошибка тестирования функциональности: {e}")
            return False
    
    def run_all_checks(self) -> Dict[str, bool]:
        """Запускает все проверки"""
        print("🔍 Проверка системы Колыбели v2")
        print("=" * 50)
        
        checks = {
            "Python версия": self.check_python_version(),
            "Основные файлы": self.check_required_files(),
            "Директории": self.check_required_directories(),
            "Зависимости": self.check_dependencies(),
            "Конфигурация": self.check_configuration(),
            "Внешние сервисы": self.check_external_services(),
            "Системные модули": self.check_system_modules(),
            "Базовая функциональность": self.test_basic_functionality()
        }
        
        return checks
    
    def print_results(self, checks: Dict[str, bool]):
        """Выводит результаты проверки"""
        print("\n📋 Результаты проверки:")
        print("-" * 30)
        
        # Выводим результаты по категориям
        for check_name, result in checks.items():
            status = "✅" if result else "❌"
            print(f"{status} {check_name}")
        
        # Выводим детали
        if self.results:
            print(f"\n✅ Успешные проверки ({len(self.results)}):")
            for result in self.results:
                print(f"   {result}")
        
        if self.warnings:
            print(f"\n⚠️ Предупреждения ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if self.errors:
            print(f"\n❌ Ошибки ({len(self.errors)}):")
            for error in self.errors:
                print(f"   {error}")
        
        # Общий статус
        print("\n" + "=" * 50)
        
        all_critical_ok = all(checks[key] for key in ["Python версия", "Основные файлы", "Зависимости", "Системные модули"])
        
        if all_critical_ok:
            print("🎉 Система готова к работе!")
            print("\n🚀 Следующие шаги:")
            print("   • Консольный интерфейс: python main_v2.py")
            print("   • Веб-интерфейс: python start_web_interface.py")
            
            if self.warnings:
                print(f"\n💡 Есть {len(self.warnings)} предупреждений, но система работоспособна")
        else:
            print("❌ Система не готова к работе!")
            print("\n🔧 Необходимо исправить критические ошибки:")
            
            if not checks["Python версия"]:
                print("   • Обновите Python до версии 3.9+")
            if not checks["Основные файлы"]:
                print("   • Убедитесь, что все файлы на месте")
            if not checks["Зависимости"]:
                print("   • Установите зависимости: pip install -r requirements.txt")
            if not checks["Системные модули"]:
                print("   • Проверьте целостность модулей системы")
        
        return all_critical_ok

def main():
    """Основная функция проверки"""
    checker = SystemChecker()
    checks = checker.run_all_checks()
    system_ready = checker.print_results(checks)
    
    # Сохраняем отчет
    report = {
        "timestamp": datetime.now().isoformat(),
        "system_ready": system_ready,
        "checks": checks,
        "results": checker.results,
        "warnings": checker.warnings,
        "errors": checker.errors
    }
    
    os.makedirs("logs", exist_ok=True)
    with open("logs/system_check.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Отчет сохранен: logs/system_check.json")
    
    return 0 if system_ready else 1

if __name__ == "__main__":
    exit(main())