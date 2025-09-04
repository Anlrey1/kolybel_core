# runtime_orchestrator.py — оркестратор выполнения агентов
import logging
import threading
import time
import schedule
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from agent_specification import AgentSpecification, TriggerType
from runtime_adapters import (
    BaseRuntimeAdapter, 
    LocalRuntimeAdapter, 
    N8NRuntimeAdapter, 
    DockerRuntimeAdapter,
    ExecutionResult,
    ExecutionStatus
)

logger = logging.getLogger(__name__)

class ExecutionPolicy(Enum):
    PRIMARY_ONLY = "primary_only"
    FAILOVER = "failover"
    LOAD_BALANCE = "load_balance"
    REDUNDANT = "redundant"

@dataclass
class DeployedAgent:
    """Информация о развернутом агенте"""
    agent_id: str
    spec: AgentSpecification
    deployments: Dict[str, str]  # runtime_name -> deployment_id
    primary_runtime: str
    created_at: datetime
    last_execution: Optional[datetime] = None
    execution_count: int = 0
    success_count: int = 0
    error_count: int = 0

class RuntimeOrchestrator:
    """Оркестратор для управления выполнением агентов в различных рантаймах"""
    
    def __init__(self, memory, config: Dict[str, Any] = None):
        self.memory = memory
        self.config = config or {}
        
        # Политика выполнения
        policy_str = self.config.get('execution_policy', 'failover')
        self.execution_policy = ExecutionPolicy(policy_str)
        
        # Интервал проверки здоровья
        self.health_check_interval = self.config.get('health_check_interval', 60)
        
        # Инициализируем адаптеры рантаймов
        self.runtimes = {}
        self._init_runtimes()
        
        # Развернутые агенты
        self.deployed_agents: Dict[str, DeployedAgent] = {}
        
        # Планировщик
        self.scheduler_thread = None
        self.scheduler_running = False
        
        # Мониторинг здоровья
        self.health_monitor_thread = None
        self.health_monitor_running = False
        
        logger.info(f"Runtime Orchestrator initialized with policy: {self.execution_policy.value}")
    
    def _init_runtimes(self):
        """Инициализирует доступные рантаймы"""
        # Локальный рантайм (всегда доступен)
        local_config = self.config.get('local', {})
        self.runtimes['local'] = LocalRuntimeAdapter(local_config)
        
        # n8n рантайм
        n8n_config = self.config.get('n8n', {})
        if n8n_config.get('api_url'):
            self.runtimes['n8n'] = N8NRuntimeAdapter(n8n_config)
        
        # Docker рантайм
        docker_config = self.config.get('docker', {})
        if docker_config.get('enabled', True):
            self.runtimes['docker'] = DockerRuntimeAdapter(docker_config)
        
        logger.info(f"Initialized runtimes: {list(self.runtimes.keys())}")
    
    def get_available_runtimes(self) -> List[str]:
        """Возвращает список доступных рантаймов"""
        available = []
        for name, runtime in self.runtimes.items():
            if runtime.health_check():
                available.append(name)
        return available
    
    def select_runtime(self, spec: AgentSpecification) -> str:
        """Выбирает подходящий рантайм для агента"""
        available_runtimes = self.get_available_runtimes()
        
        # Проверяем предпочтения агента
        for preferred in spec.runtime_preferences:
            runtime_name = preferred.value
            if runtime_name in available_runtimes:
                logger.info(f"Selected preferred runtime {runtime_name} for agent {spec.name}")
                return runtime_name
        
        # Если предпочтительные рантаймы недоступны, выбираем первый доступный
        if available_runtimes:
            selected = available_runtimes[0]
            logger.info(f"Selected fallback runtime {selected} for agent {spec.name}")
            return selected
        
        raise Exception("No available runtimes found")
    
    def deploy_agent(self, spec: AgentSpecification) -> str:
        """Развертывает агента в выбранных рантаймах"""
        agent_id = spec.id
        
        try:
            # Выбираем основной рантайм
            primary_runtime = self.select_runtime(spec)
            
            # Развертываем в основном рантайме
            deployments = {}
            primary_deployment_id = self.runtimes[primary_runtime].deploy_agent(spec)
            deployments[primary_runtime] = primary_deployment_id
            
            # Для политики REDUNDANT развертываем в дополнительных рантаймах
            if self.execution_policy == ExecutionPolicy.REDUNDANT:
                available_runtimes = self.get_available_runtimes()
                for runtime_name in available_runtimes:
                    if runtime_name != primary_runtime:
                        try:
                            deployment_id = self.runtimes[runtime_name].deploy_agent(spec)
                            deployments[runtime_name] = deployment_id
                        except Exception as e:
                            logger.warning(f"Failed to deploy to {runtime_name}: {e}")
            
            # Сохраняем информацию о развернутом агенте
            deployed_agent = DeployedAgent(
                agent_id=agent_id,
                spec=spec,
                deployments=deployments,
                primary_runtime=primary_runtime,
                created_at=datetime.now()
            )
            
            self.deployed_agents[agent_id] = deployed_agent
            
            # Настраиваем планировщик для агента
            self._schedule_agent(deployed_agent)
            
            logger.info(f"Agent {spec.name} deployed successfully with ID {agent_id}")
            return agent_id
            
        except Exception as e:
            logger.error(f"Failed to deploy agent {spec.name}: {e}")
            raise
    
    def _schedule_agent(self, deployed_agent: DeployedAgent):
        """Настраивает планировщик для агента"""
        spec = deployed_agent.spec
        
        for trigger in spec.triggers:
            if trigger.type == TriggerType.SCHEDULE and trigger.enabled:
                cron_expr = trigger.config.get('cron', '0 9 * * *')
                
                # Простая обработка cron выражений
                # В реальной реализации нужна более сложная логика
                if cron_expr == "0 9,15,20 * * *":
                    schedule.every().day.at("09:00").do(
                        self._execute_scheduled_agent, deployed_agent.agent_id
                    )
                    schedule.every().day.at("15:00").do(
                        self._execute_scheduled_agent, deployed_agent.agent_id
                    )
                    schedule.every().day.at("20:00").do(
                        self._execute_scheduled_agent, deployed_agent.agent_id
                    )
                elif "every" in cron_expr:
                    # Обработка "every X hours" формата
                    if "hour" in cron_expr:
                        hours = int(cron_expr.split()[1])
                        schedule.every(hours).hours.do(
                            self._execute_scheduled_agent, deployed_agent.agent_id
                        )
                
                logger.info(f"Scheduled agent {spec.name} with cron: {cron_expr}")
    
    def _execute_scheduled_agent(self, agent_id: str):
        """Выполняет агента по расписанию"""
        try:
            result = self.execute_agent(agent_id)
            logger.info(f"Scheduled execution of {agent_id}: {result.status.value}")
        except Exception as e:
            logger.error(f"Scheduled execution failed for {agent_id}: {e}")
    
    def execute_agent(self, agent_id: str, trigger_data: Dict[str, Any] = None) -> ExecutionResult:
        """Выполняет агента с учетом политики выполнения"""
        if agent_id not in self.deployed_agents:
            return ExecutionResult(
                agent_id=agent_id,
                status=ExecutionStatus.FAILED,
                message="Agent not found"
            )
        
        deployed_agent = self.deployed_agents[agent_id]
        
        if self.execution_policy == ExecutionPolicy.PRIMARY_ONLY:
            return self._execute_in_runtime(deployed_agent, deployed_agent.primary_runtime, trigger_data)
        
        elif self.execution_policy == ExecutionPolicy.FAILOVER:
            return self._execute_with_failover(deployed_agent, trigger_data)
        
        elif self.execution_policy == ExecutionPolicy.LOAD_BALANCE:
            return self._execute_with_load_balance(deployed_agent, trigger_data)
        
        elif self.execution_policy == ExecutionPolicy.REDUNDANT:
            return self._execute_redundant(deployed_agent, trigger_data)
        
        else:
            return ExecutionResult(
                agent_id=agent_id,
                status=ExecutionStatus.FAILED,
                message=f"Unknown execution policy: {self.execution_policy}"
            )
    
    def _execute_in_runtime(self, deployed_agent: DeployedAgent, runtime_name: str, trigger_data: Dict[str, Any] = None) -> ExecutionResult:
        """Выполняет агента в указанном рантайме"""
        if runtime_name not in deployed_agent.deployments:
            return ExecutionResult(
                agent_id=deployed_agent.agent_id,
                status=ExecutionStatus.FAILED,
                message=f"Agent not deployed in runtime {runtime_name}"
            )
        
        deployment_id = deployed_agent.deployments[runtime_name]
        runtime = self.runtimes[runtime_name]
        
        try:
            result = runtime.execute_agent(deployment_id, trigger_data)
            
            # Обновляем статистику
            deployed_agent.execution_count += 1
            deployed_agent.last_execution = datetime.now()
            
            if result.status == ExecutionStatus.SUCCESS:
                deployed_agent.success_count += 1
            else:
                deployed_agent.error_count += 1
            
            # Сохраняем в память
            self.memory.store(
                f"[agent_execution] {deployed_agent.spec.name}: {result.status.value} in {runtime_name}",
                {
                    "type": "agent_execution",
                    "agent_id": deployed_agent.agent_id,
                    "runtime": runtime_name,
                    "status": result.status.value,
                    "execution_time": result.execution_time,
                    "timestamp": result.timestamp
                }
            )
            
            return result
            
        except Exception as e:
            deployed_agent.error_count += 1
            logger.error(f"Execution failed in {runtime_name}: {e}")
            
            return ExecutionResult(
                agent_id=deployed_agent.agent_id,
                status=ExecutionStatus.FAILED,
                message=f"Runtime execution error: {str(e)}",
                runtime_used=runtime_name
            )
    
    def _execute_with_failover(self, deployed_agent: DeployedAgent, trigger_data: Dict[str, Any] = None) -> ExecutionResult:
        """Выполняет агента с failover между рантаймами"""
        # Сначала пробуем основной рантайм
        primary_runtime = deployed_agent.primary_runtime
        
        if primary_runtime in self.runtimes and self.runtimes[primary_runtime].is_healthy:
            result = self._execute_in_runtime(deployed_agent, primary_runtime, trigger_data)
            if result.status == ExecutionStatus.SUCCESS:
                return result
            
            logger.warning(f"Primary runtime {primary_runtime} failed, trying failover")
        
        # Пробуем другие доступные рантаймы
        available_runtimes = self.get_available_runtimes()
        for runtime_name in available_runtimes:
            if runtime_name != primary_runtime and runtime_name in deployed_agent.deployments:
                logger.info(f"Trying failover to {runtime_name}")
                result = self._execute_in_runtime(deployed_agent, runtime_name, trigger_data)
                if result.status == ExecutionStatus.SUCCESS:
                    return result
        
        # Если все рантаймы недоступны, пробуем развернуть в локальном
        if 'local' not in deployed_agent.deployments:
            try:
                local_deployment_id = self.runtimes['local'].deploy_agent(deployed_agent.spec)
                deployed_agent.deployments['local'] = local_deployment_id
                return self._execute_in_runtime(deployed_agent, 'local', trigger_data)
            except Exception as e:
                logger.error(f"Emergency local deployment failed: {e}")
        
        return ExecutionResult(
            agent_id=deployed_agent.agent_id,
            status=ExecutionStatus.FAILED,
            message="All runtimes failed"
        )
    
    def _execute_with_load_balance(self, deployed_agent: DeployedAgent, trigger_data: Dict[str, Any] = None) -> ExecutionResult:
        """Выполняет агента с балансировкой нагрузки"""
        available_runtimes = []
        for runtime_name in deployed_agent.deployments:
            if runtime_name in self.runtimes and self.runtimes[runtime_name].is_healthy:
                available_runtimes.append(runtime_name)
        
        if not available_runtimes:
            return ExecutionResult(
                agent_id=deployed_agent.agent_id,
                status=ExecutionStatus.FAILED,
                message="No healthy runtimes available"
            )
        
        # Простая балансировка - выбираем рантайм по round-robin
        selected_runtime = available_runtimes[deployed_agent.execution_count % len(available_runtimes)]
        
        return self._execute_in_runtime(deployed_agent, selected_runtime, trigger_data)
    
    def _execute_redundant(self, deployed_agent: DeployedAgent, trigger_data: Dict[str, Any] = None) -> ExecutionResult:
        """Выполняет агента во всех доступных рантаймах"""
        results = []
        
        for runtime_name in deployed_agent.deployments:
            if runtime_name in self.runtimes and self.runtimes[runtime_name].is_healthy:
                result = self._execute_in_runtime(deployed_agent, runtime_name, trigger_data)
                results.append(result)
        
        # Возвращаем первый успешный результат или последний неуспешный
        for result in results:
            if result.status == ExecutionStatus.SUCCESS:
                return result
        
        return results[-1] if results else ExecutionResult(
            agent_id=deployed_agent.agent_id,
            status=ExecutionStatus.FAILED,
            message="No runtimes available"
        )
    
    def remove_agent(self, agent_id: str) -> bool:
        """Удаляет агента из всех рантаймов"""
        if agent_id not in self.deployed_agents:
            return False

        deployed_agent = self.deployed_agents[agent_id]
        success = True

        # Удаляем из всех рантаймов
        for runtime_name, deployment_id in deployed_agent.deployments.items():
            try:
                if runtime_name in self.runtimes:
                    self.runtimes[runtime_name].remove_agent(deployment_id)
            except Exception as e:
                logger.error(f"Failed to remove agent from {runtime_name}: {e}")
                success = False

        # Удаляем из планировщика
        # Реализация удаления задач из schedule для конкретного агента
        # schedule не имеет API для удаления по функции и аргументам,
        # по-этому удаляем задачи с совпадающим агент_id в аргументах
        to_remove = []
        for job in schedule.get_jobs():
            if job.job_func:
                # Проверяем если агент_id есть в аргументах вызова функции
                args = getattr(job, 'args', ())
                kwargs = getattr(job, 'kwargs', {})
                if agent_id in args or agent_id in kwargs.values():
                    to_remove.append(job)
        for job in to_remove:
            schedule.cancel_job(job)

        # Удаляем из списка развернутых агентов
        del self.deployed_agents[agent_id]

        logger.info(f"Agent {agent_id} removed from orchestrator")
        return success
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Возвращает статус агента"""
        if agent_id not in self.deployed_agents:
            return None
        
        deployed_agent = self.deployed_agents[agent_id]
        
        return {
            "agent_id": agent_id,
            "name": deployed_agent.spec.name,
            "primary_runtime": deployed_agent.primary_runtime,
            "deployments": list(deployed_agent.deployments.keys()),
            "created_at": deployed_agent.created_at.isoformat(),
            "last_execution": deployed_agent.last_execution.isoformat() if deployed_agent.last_execution else None,
            "execution_count": deployed_agent.execution_count,
            "success_count": deployed_agent.success_count,
            "error_count": deployed_agent.error_count,
            "success_rate": deployed_agent.success_count / max(deployed_agent.execution_count, 1)
        }
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """Возвращает список всех развернутых агентов"""
        return [self.get_agent_status(agent_id) for agent_id in self.deployed_agents.keys()]
    
    def get_runtime_status(self) -> Dict[str, Any]:
        """Возвращает статус всех рантаймов"""
        status = {}
        
        for name, runtime in self.runtimes.items():
            status[name] = {
                "name": name,
                "healthy": runtime.is_healthy,
                "available": runtime.is_available(),
                "capabilities": runtime.get_capabilities(),
                "last_health_check": runtime._last_health_check.isoformat()
            }
        
        return status
    
    def start_scheduler(self):
        """Запускает планировщик агентов"""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        
        def scheduler_loop():
            while self.scheduler_running:
                try:
                    schedule.run_pending()
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Scheduler error: {e}")
        
        self.scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        # Запускаем мониторинг здоровья
        self.start_health_monitor()
        
        logger.info("Scheduler started")
    
    def stop_scheduler(self):
        """Останавливает планировщик агентов"""
        self.scheduler_running = False
        self.health_monitor_running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        if self.health_monitor_thread:
            self.health_monitor_thread.join(timeout=5)
        
        logger.info("Scheduler stopped")
    
    def start_health_monitor(self):
        """Запускает мониторинг здоровья рантаймов"""
        if self.health_monitor_running:
            return
        
        self.health_monitor_running = True
        
        def health_monitor_loop():
            while self.health_monitor_running:
                try:
                    for name, runtime in self.runtimes.items():
                        runtime.health_check()
                    
                    time.sleep(self.health_check_interval)
                except Exception as e:
                    logger.error(f"Health monitor error: {e}")
        
        self.health_monitor_thread = threading.Thread(target=health_monitor_loop, daemon=True)
        self.health_monitor_thread.start()
        
        logger.info("Health monitor started")
    
    def force_health_check(self):
        """Принудительно проверяет здоровье всех рантаймов"""
        results = {}
        for name, runtime in self.runtimes.items():
            results[name] = runtime.health_check()
        return results