# web_interface.py — веб-интерфейс для управления агентами Колыбель v2
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.serving import run_simple

from agents_v2 import AgentManager
from autonomous_agents import get_agent_manager
from migration_tool import AgentMigrationTool

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'kolybel_secret_key_2024')

# Глобальный менеджер агентов
agent_manager = None

def get_manager() -> AgentManager:
    """Получает глобальный менеджер агентов"""
    global agent_manager
    if agent_manager is None:
        agent_manager = get_agent_manager()
    return agent_manager

@app.route('/')
def index():
    """Главная страница - дашборд"""
    try:
        manager = get_manager()
        
        # Получаем список агентов
        agents = manager.list_agents()
        
        # Получаем статус рантаймов
        runtime_status = manager.get_runtime_status()
        
        # Статистика
        total_agents = len(agents)
        active_agents = sum(1 for agent in agents if agent.get('execution_count', 0) > 0)
        total_executions = sum(agent.get('execution_count', 0) for agent in agents)
        success_rate = sum(agent.get('success_rate', 0) for agent in agents) / max(total_agents, 1)
        
        stats = {
            'total_agents': total_agents,
            'active_agents': active_agents,
            'total_executions': total_executions,
            'success_rate': round(success_rate * 100, 1)
        }
        
        return render_template('dashboard.html', 
                             agents=agents, 
                             runtime_status=runtime_status,
                             stats=stats)
    except Exception as e:
        logger.error(f"Ошибка загрузки дашборда: {e}")
        return render_template('error.html', error=str(e))

@app.route('/agents')
def agents_list():
    """Страница списка агентов"""
    try:
        manager = get_manager()
        agents = manager.list_agents()
        return render_template('agents.html', agents=agents)
    except Exception as e:
        logger.error(f"Ошибка загрузки списка агентов: {e}")
        return render_template('error.html', error=str(e))

@app.route('/agents/create', methods=['GET', 'POST'])
def create_agent():
    """Страница создания нового агента"""
    if request.method == 'POST':
        try:
            agent_type = request.form.get('agent_type')
            name = request.form.get('name')
            owner = request.form.get('owner', 'web_user')
            
            manager = get_manager()
            
            if agent_type == 'rss_monitor':
                agent_id = manager.create_rss_agent(
                    name=name,
                    owner=owner,
                    rss_url=request.form.get('rss_url'),
                    telegram_chat_id=request.form.get('telegram_chat_id'),
                    schedule=request.form.get('schedule', '0 9,15,20 * * *'),
                    style=request.form.get('style', 'информативный стиль'),
                    runtime_preferences=request.form.getlist('runtime_preferences')
                )
                
            elif agent_type == 'content_generator':
                topics = [topic.strip() for topic in request.form.get('topics', '').split(',') if topic.strip()]
                agent_id = manager.create_content_agent(
                    name=name,
                    owner=owner,
                    template_id=request.form.get('template_id', 'default'),
                    telegram_chat_id=request.form.get('telegram_chat_id'),
                    topics=topics,
                    schedule=request.form.get('schedule', '0 12 * * *'),
                    runtime_preferences=request.form.getlist('runtime_preferences')
                )
            else:
                raise ValueError(f"Неизвестный тип агента: {agent_type}")
            
            flash(f'Агент "{name}" успешно создан с ID: {agent_id}', 'success')
            return redirect(url_for('agent_detail', agent_id=agent_id))
            
        except Exception as e:
            logger.error(f"Ошибка создания агента: {e}")
            flash(f'Ошибка создания агента: {str(e)}', 'error')
    
    return render_template('create_agent.html')

@app.route('/agents/<agent_id>')
def agent_detail(agent_id: str):
    """Страница детальной информации об агенте"""
    try:
        manager = get_manager()
        agent_info = manager.get_agent_status(agent_id)
        
        if not agent_info:
            flash('Агент не найден', 'error')
            return redirect(url_for('agents_list'))
        
        # Получаем спецификацию агента
        agent_spec_json = manager.export_agent_to_json(agent_id)
        
        return render_template('agent_detail.html', 
                             agent=agent_info, 
                             agent_spec=agent_spec_json)
    except Exception as e:
        logger.error(f"Ошибка загрузки агента {agent_id}: {e}")
        return render_template('error.html', error=str(e))

@app.route('/agents/<agent_id>/execute', methods=['POST'])
def execute_agent(agent_id: str):
    """Выполнить агента вручную"""
    try:
        manager = get_manager()
        result = manager.execute_agent(agent_id)
        
        return jsonify({
            'success': result.status.value == 'success',
            'status': result.status.value,
            'message': result.message,
            'execution_time': result.execution_time,
            'timestamp': result.timestamp
        })
    except Exception as e:
        logger.error(f"Ошибка выполнения агента {agent_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/agents/<agent_id>/delete', methods=['POST'])
def delete_agent(agent_id: str):
    """Удалить агента"""
    try:
        manager = get_manager()
        success = manager.remove_agent(agent_id)
        
        if success:
            flash('Агент успешно удален', 'success')
        else:
            flash('Ошибка удаления агента', 'error')
        
        return redirect(url_for('agents_list'))
    except Exception as e:
        logger.error(f"Ошибка удаления агента {agent_id}: {e}")
        flash(f'Ошибка удаления агента: {str(e)}', 'error')
        return redirect(url_for('agents_list'))

@app.route('/runtimes')
def runtimes_status():
    """Страница статуса рантаймов"""
    try:
        manager = get_manager()
        runtime_status = manager.get_runtime_status()
        return render_template('runtimes.html', runtime_status=runtime_status)
    except Exception as e:
        logger.error(f"Ошибка загрузки статуса рантаймов: {e}")
        return render_template('error.html', error=str(e))

@app.route('/migration')
def migration_page():
    """Страница миграции агентов"""
    return render_template('migration.html')

@app.route('/migration/run', methods=['POST'])
def run_migration():
    """Запуск миграции агентов"""
    try:
        migration_tool = AgentMigrationTool(get_manager())
        
        # Мигрируем n8n workflows
        migrated_agents = migration_tool.migrate_n8n_workflows_from_approved_goals()
        
        # Генерируем отчет
        report = migration_tool.generate_migration_report()
        migration_tool.save_migration_report()
        
        flash(f'Миграция завершена. Мигрировано агентов: {len(migrated_agents)}', 'success')
        
        return render_template('migration_result.html', 
                             report=report, 
                             migrated_agents=migrated_agents)
    except Exception as e:
        logger.error(f"Ошибка миграции: {e}")
        flash(f'Ошибка миграции: {str(e)}', 'error')
        return redirect(url_for('migration_page'))

@app.route('/api/agents')
def api_agents():
    """API: список агентов"""
    try:
        manager = get_manager()
        agents = manager.list_agents()
        return jsonify({'success': True, 'agents': agents})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/runtimes')
def api_runtimes():
    """API: статус рантаймов"""
    try:
        manager = get_manager()
        runtime_status = manager.get_runtime_status()
        return jsonify({'success': True, 'runtimes': runtime_status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/health')
def api_health():
    """API: проверка здоровья системы"""
    try:
        manager = get_manager()
        health_results = manager.orchestrator.force_health_check()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'health_checks': health_results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def create_templates():
    """Создает HTML шаблоны для веб-интерфейса"""
    templates_dir = 'templates'
    os.makedirs(templates_dir, exist_ok=True)
    
    # Базовый шаблон
    base_template = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Колыбель v2{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .sidebar { min-height: 100vh; background: #f8f9fa; }
        .agent-card { transition: transform 0.2s; }
        .agent-card:hover { transform: translateY(-2px); }
        .status-healthy { color: #28a745; }
        .status-unhealthy { color: #dc3545; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <nav class="col-md-2 sidebar p-3">
                <h4 class="text-primary">🤖 Колыбель v2</h4>
                <ul class="nav flex-column">
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('index') }}">
                            <i class="fas fa-tachometer-alt"></i> Дашборд
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('agents_list') }}">
                            <i class="fas fa-robot"></i> Агенты
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('create_agent') }}">
                            <i class="fas fa-plus"></i> Создать агента
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('runtimes_status') }}">
                            <i class="fas fa-server"></i> Рантаймы
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('migration_page') }}">
                            <i class="fas fa-exchange-alt"></i> Миграция
                        </a>
                    </li>
                </ul>
            </nav>
            
            <main class="col-md-10 p-4">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                {% block content %}{% endblock %}
            </main>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>'''
    
    with open(f'{templates_dir}/base.html', 'w', encoding='utf-8') as f:
        f.write(base_template)
    
    # Дашборд
    dashboard_template = '''{% extends "base.html" %}

{% block title %}Дашборд - Колыбель v2{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>📊 Дашборд</h1>
    <button class="btn btn-outline-primary" onclick="location.reload()">
        <i class="fas fa-sync-alt"></i> Обновить
    </button>
</div>

<!-- Статистика -->
<div class="row mb-4">
    <div class="col-md-3">
        <div class="card text-center">
            <div class="card-body">
                <h5 class="card-title">{{ stats.total_agents }}</h5>
                <p class="card-text">Всего агентов</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-center">
            <div class="card-body">
                <h5 class="card-title">{{ stats.active_agents }}</h5>
                <p class="card-text">Активных агентов</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-center">
            <div class="card-body">
                <h5 class="card-title">{{ stats.total_executions }}</h5>
                <p class="card-text">Всего выполнений</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-center">
            <div class="card-body">
                <h5 class="card-title">{{ stats.success_rate }}%</h5>
                <p class="card-text">Успешность</p>
            </div>
        </div>
    </div>
</div>

<!-- Статус рантаймов -->
<div class="row mb-4">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5>🏗️ Статус рантаймов</h5>
            </div>
            <div class="card-body">
                {% for name, status in runtime_status.items() %}
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span>{{ name.title() }}</span>
                    <span class="{{ 'status-healthy' if status.healthy else 'status-unhealthy' }}">
                        <i class="fas fa-{{ 'check-circle' if status.healthy else 'times-circle' }}"></i>
                        {{ 'Здоров' if status.healthy else 'Недоступен' }}
                    </span>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5>🤖 Последние агенты</h5>
            </div>
            <div class="card-body">
                {% for agent in agents[:5] %}
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <a href="{{ url_for('agent_detail', agent_id=agent.agent_id) }}" class="text-decoration-none">
                        {{ agent.name }}
                    </a>
                    <small class="text-muted">{{ agent.primary_runtime }}</small>
                </div>
                {% endfor %}
                {% if agents|length == 0 %}
                <p class="text-muted">Агенты не найдены</p>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
    
    with open(f'{templates_dir}/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_template)
    
    # Список агентов
    agents_template = '''{% extends "base.html" %}

{% block title %}Агенты - Колыбель v2{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>🤖 Агенты</h1>
    <a href="{{ url_for('create_agent') }}" class="btn btn-primary">
        <i class="fas fa-plus"></i> Создать агента
    </a>
</div>

<div class="row">
    {% for agent in agents %}
    <div class="col-md-4 mb-3">
        <div class="card agent-card">
            <div class="card-body">
                <h5 class="card-title">{{ agent.name }}</h5>
                <p class="card-text">
                    <small class="text-muted">ID: {{ agent.agent_id }}</small><br>
                    <strong>Рантайм:</strong> {{ agent.primary_runtime }}<br>
                    <strong>Выполнений:</strong> {{ agent.execution_count }}<br>
                    <strong>Успешность:</strong> {{ "%.1f"|format(agent.success_rate * 100) }}%
                </p>
                <div class="btn-group w-100">
                    <a href="{{ url_for('agent_detail', agent_id=agent.agent_id) }}" class="btn btn-outline-primary btn-sm">
                        <i class="fas fa-eye"></i> Детали
                    </a>
                    <button class="btn btn-outline-success btn-sm" onclick="executeAgent('{{ agent.agent_id }}')">
                        <i class="fas fa-play"></i> Запустить
                    </button>
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
    
    {% if agents|length == 0 %}
    <div class="col-12">
        <div class="text-center py-5">
            <i class="fas fa-robot fa-3x text-muted mb-3"></i>
            <h4>Агенты не найдены</h4>
            <p class="text-muted">Создайте первого агента для начала работы</p>
            <a href="{{ url_for('create_agent') }}" class="btn btn-primary">
                <i class="fas fa-plus"></i> Создать агента
            </a>
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}

{% block scripts %}
<script>
function executeAgent(agentId) {
    fetch(`/agents/${agentId}/execute`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Агент выполнен успешно! Время: ${data.execution_time.toFixed(2)}с`);
        } else {
            alert(`Ошибка выполнения: ${data.error || data.message}`);
        }
    })
    .catch(error => {
        alert(`Ошибка: ${error}`);
    });
}
</script>
{% endblock %}'''
    
    with open(f'{templates_dir}/agents.html', 'w', encoding='utf-8') as f:
        f.write(agents_template)
    
    # Создание агента
    create_agent_template = '''{% extends "base.html" %}

{% block title %}Создать агента - Колыбель v2{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <h1>➕ Создать нового агента</h1>
        
        <form method="POST">
            <div class="mb-3">
                <label for="agent_type" class="form-label">Тип агента</label>
                <select class="form-select" id="agent_type" name="agent_type" required onchange="toggleFields()">
                    <option value="">Выберите тип агента</option>
                    <option value="rss_monitor">RSS Монитор</option>
                    <option value="content_generator">Генератор контента</option>
                </select>
            </div>
            
            <div class="mb-3">
                <label for="name" class="form-label">Название агента</label>
                <input type="text" class="form-control" id="name" name="name" required>
            </div>
            
            <div class="mb-3">
                <label for="owner" class="form-label">Владелец</label>
                <input type="text" class="form-control" id="owner" name="owner" value="web_user">
            </div>
            
            <div class="mb-3">
                <label for="telegram_chat_id" class="form-label">Telegram Chat ID</label>
                <input type="text" class="form-control" id="telegram_chat_id" name="telegram_chat_id" required>
            </div>
            
            <div class="mb-3">
                <label for="schedule" class="form-label">Расписание (cron)</label>
                <input type="text" class="form-control" id="schedule" name="schedule" value="0 9,15,20 * * *">
                <div class="form-text">Формат: минуты часы день месяц день_недели</div>
            </div>
            
            <!-- RSS Monitor fields -->
            <div id="rss_fields" style="display: none;">
                <div class="mb-3">
                    <label for="rss_url" class="form-label">RSS URL</label>
                    <input type="url" class="form-control" id="rss_url" name="rss_url">
                </div>
                
                <div class="mb-3">
                    <label for="style" class="form-label">Стиль контента</label>
                    <input type="text" class="form-control" id="style" name="style" value="информативный стиль">
                </div>
            </div>
            
            <!-- Content Generator fields -->
            <div id="content_fields" style="display: none;">
                <div class="mb-3">
                    <label for="template_id" class="form-label">ID шаблона</label>
                    <input type="text" class="form-control" id="template_id" name="template_id" value="default">
                </div>
                
                <div class="mb-3">
                    <label for="topics" class="form-label">Темы (через запятую)</label>
                    <input type="text" class="form-control" id="topics" name="topics" placeholder="технологии, игры, новости">
                </div>
            </div>
            
            <div class="mb-3">
                <label class="form-label">Предпочтительные рантаймы</label>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="runtime_preferences" value="local" id="runtime_local" checked>
                    <label class="form-check-label" for="runtime_local">Local</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="runtime_preferences" value="n8n" id="runtime_n8n">
                    <label class="form-check-label" for="runtime_n8n">N8N</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="runtime_preferences" value="docker" id="runtime_docker">
                    <label class="form-check-label" for="runtime_docker">Docker</label>
                </div>
            </div>
            
            <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                <a href="{{ url_for('agents_list') }}" class="btn btn-secondary">Отмена</a>
                <button type="submit" class="btn btn-primary">Создать агента</button>
            </div>
        </form>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
function toggleFields() {
    const agentType = document.getElementById('agent_type').value;
    const rssFields = document.getElementById('rss_fields');
    const contentFields = document.getElementById('content_fields');
    
    rssFields.style.display = agentType === 'rss_monitor' ? 'block' : 'none';
    contentFields.style.display = agentType === 'content_generator' ? 'block' : 'none';
    
    // Обновляем required атрибуты
    document.getElementById('rss_url').required = agentType === 'rss_monitor';
    document.getElementById('topics').required = agentType === 'content_generator';
}
</script>
{% endblock %}'''
    
    with open(f'{templates_dir}/create_agent.html', 'w', encoding='utf-8') as f:
        f.write(create_agent_template)
    
    # Простой шаблон ошибки
    error_template = '''{% extends "base.html" %}

{% block title %}Ошибка - Колыбель v2{% endblock %}

{% block content %}
<div class="text-center py-5">
    <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
    <h2>Произошла ошибка</h2>
    <p class="text-muted">{{ error }}</p>
    <a href="{{ url_for('index') }}" class="btn btn-primary">Вернуться на главную</a>
</div>
{% endblock %}'''
    
    with open(f'{templates_dir}/error.html', 'w', encoding='utf-8') as f:
        f.write(error_template)
    
    logger.info("HTML шаблоны созданы")

def main():
    """Запуск веб-интерфейса"""
    print("🚀 Запуск веб-интерфейса Колыбель v2...")
    
    # Создаем шаблоны
    create_templates()
    
    # Настройки сервера
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    print(f"🌐 Веб-интерфейс доступен по адресу: http://{host}:{port}")
    print("📋 Доступные страницы:")
    print("   • Дашборд: /")
    print("   • Агенты: /agents")
    print("   • Создать агента: /agents/create")
    print("   • Рантаймы: /runtimes")
    print("   • Миграция: /migration")
    print("   • API: /api/agents, /api/runtimes, /api/health")
    
    try:
        if debug:
            app.run(host=host, port=port, debug=True)
        else:
            run_simple(host, port, app, use_reloader=False, use_debugger=False)
    except KeyboardInterrupt:
        print("\n👋 Веб-интерфейс остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска веб-интерфейса: {e}")

if __name__ == '__main__':
    main()