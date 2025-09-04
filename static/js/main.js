// Колыбель - Основной JavaScript файл

// Глобальные переменные
let systemStatus = {
    online: false,
    agents: 0,
    memory: 0,
    sessions: 0
};

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupGlobalEventListeners();
    startPeriodicUpdates();
});

function initializeApp() {
    console.log('🌟 Колыбель - Инициализация интерфейса');
    
    // Проверяем статус системы
    checkSystemStatus();
    
    // Инициализируем компоненты
    initializeTooltips();
    initializePopovers();
    
    // Добавляем анимации
    addPageAnimations();
    
    console.log('✅ Интерфейс инициализирован');
}

function setupGlobalEventListeners() {
    // Обработка ошибок
    window.addEventListener('error', function(e) {
        console.error('Глобальная ошибка:', e.error);
        showNotification('Произошла ошибка в интерфейсе', 'danger');
    });
    
    // Обработка потери соединения
    window.addEventListener('online', function() {
        showNotification('Соединение восстановлено', 'success');
        updateConnectionStatus(true);
    });
    
    window.addEventListener('offline', function() {
        showNotification('Соединение потеряно', 'warning');
        updateConnectionStatus(false);
    });
    
    // Горячие клавиши
    document.addEventListener('keydown', function(e) {
        // Ctrl+K - быстрый поиск/команды
        if (e.ctrlKey && e.key === 'k') {
            e.preventDefault();
            showQuickCommandModal();
        }
        
        // Escape - закрыть модальные окна
        if (e.key === 'Escape') {
            closeAllModals();
        }
    });
}

function startPeriodicUpdates() {
    // Обновляем статус каждые 30 секунд
    setInterval(checkSystemStatus, 30000);
    
    // Обновляем время каждую секунду
    setInterval(updateTime, 1000);
}

function checkSystemStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            systemStatus = {
                online: data.status === 'online',
                agents: data.agents?.total_agents || 0,
                memory: data.memory?.total_documents || 0,
                sessions: data.sessions?.active_sessions || 0
            };
            
            updateSystemStatusDisplay();
        })
        .catch(error => {
            console.error('Ошибка проверки статуса:', error);
            systemStatus.online = false;
            updateSystemStatusDisplay();
        });
}

function updateSystemStatusDisplay() {
    const statusElement = document.getElementById('system-status');
    if (statusElement) {
        if (systemStatus.online) {
            statusElement.className = 'badge bg-success';
            statusElement.innerHTML = '<i class="bi bi-circle-fill"></i> Онлайн';
        } else {
            statusElement.className = 'badge bg-danger';
            statusElement.innerHTML = '<i class="bi bi-circle-fill"></i> Офлайн';
        }
    }
    
    // Обновляем другие элементы статуса
    updateElementText('agents-count', systemStatus.agents);
    updateElementText('memory-count', systemStatus.memory);
    updateElementText('sessions-count', systemStatus.sessions);
}

function updateConnectionStatus(online) {
    const statusElements = document.querySelectorAll('[id*="status"]');
    statusElements.forEach(element => {
        if (online) {
            element.classList.remove('text-danger');
            element.classList.add('text-success');
        } else {
            element.classList.remove('text-success');
            element.classList.add('text-danger');
        }
    });
}

function updateElementText(elementId, text) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = text;
    }
}

function updateTime() {
    const timeElements = document.querySelectorAll('.current-time');
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    
    timeElements.forEach(element => {
        element.textContent = timeString;
    });
}

// Система уведомлений
function showNotification(message, type = 'info', duration = 5000) {
    const notificationId = 'notification-' + Date.now();
    const alertDiv = document.createElement('div');
    alertDiv.id = notificationId;
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed slide-in`;
    alertDiv.style.cssText = `
        top: 20px; 
        right: 20px; 
        z-index: 9999; 
        min-width: 300px;
        max-width: 400px;
    `;
    
    const icon = getNotificationIcon(type);
    alertDiv.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="bi ${icon} me-2"></i>
            <div class="flex-grow-1">${message}</div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Автоматически убираем уведомление
    setTimeout(() => {
        const notification = document.getElementById(notificationId);
        if (notification && notification.parentNode) {
            notification.classList.add('fade');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }
    }, duration);
    
    // Добавляем звук (опционально)
    playNotificationSound(type);
}

function getNotificationIcon(type) {
    const icons = {
        'success': 'bi-check-circle-fill',
        'danger': 'bi-exclamation-triangle-fill',
        'warning': 'bi-exclamation-circle-fill',
        'info': 'bi-info-circle-fill',
        'primary': 'bi-star-fill'
    };
    return icons[type] || 'bi-info-circle-fill';
}

function playNotificationSound(type) {
    // Простой звуковой сигнал (можно заменить на реальные звуки)
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance('');
        utterance.volume = 0.1;
        utterance.rate = 10;
        utterance.pitch = type === 'success' ? 2 : type === 'danger' ? 0.5 : 1;
        speechSynthesis.speak(utterance);
    }
}

// Модальные окна
function showQuickCommandModal() {
    const modalHtml = `
        <div class="modal fade" id="quickCommandModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-lightning"></i> Быстрые команды
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <input type="text" class="form-control mb-3" id="quickCommandInput" 
                               placeholder="Введите команду или поиск...">
                        <div id="quickCommandSuggestions">
                            <div class="list-group">
                                <a href="/chat" class="list-group-item list-group-item-action">
                                    <i class="bi bi-chat-dots"></i> Открыть чат
                                </a>
                                <a href="/agents" class="list-group-item list-group-item-action">
                                    <i class="bi bi-robot"></i> Управление агентами
                                </a>
                                <a href="/goals" class="list-group-item list-group-item-action">
                                    <i class="bi bi-target"></i> Мои цели
                                </a>
                                <a href="/analytics" class="list-group-item list-group-item-action">
                                    <i class="bi bi-graph-up"></i> Аналитика
                                </a>
                                <a href="/settings" class="list-group-item list-group-item-action">
                                    <i class="bi bi-gear"></i> Настройки
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Удаляем существующий модал, если есть
    const existingModal = document.getElementById('quickCommandModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Добавляем новый модал
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Показываем модал
    const modal = new bootstrap.Modal(document.getElementById('quickCommandModal'));
    modal.show();
    
    // Фокус на поле ввода
    setTimeout(() => {
        document.getElementById('quickCommandInput').focus();
    }, 300);
}

function closeAllModals() {
    const modals = document.querySelectorAll('.modal.show');
    modals.forEach(modal => {
        const modalInstance = bootstrap.Modal.getInstance(modal);
        if (modalInstance) {
            modalInstance.hide();
        }
    });
}

// Анимации
function addPageAnimations() {
    // Добавляем анимации появления для карточек
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('slide-in');
    });
    
    // Анимация для статистических элементов
    const statElements = document.querySelectorAll('[id$="-count"]');
    statElements.forEach(element => {
        animateNumber(element, 0, parseInt(element.textContent) || 0, 1000);
    });
}

function animateNumber(element, start, end, duration) {
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = Math.floor(start + (end - start) * progress);
        element.textContent = current;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// Утилиты
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showNotification('Скопировано в буфер обмена', 'success');
    }, function(err) {
        console.error('Ошибка копирования: ', err);
        showNotification('Ошибка копирования', 'danger');
    });
}

// API утилиты
function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    return fetch(url, { ...defaultOptions, ...options })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('API Error:', error);
            showNotification('Ошибка API запроса', 'danger');
            throw error;
        });
}

// Экспорт функций для глобального использования
window.KolybelUI = {
    showNotification,
    checkSystemStatus,
    apiRequest,
    formatNumber,
    formatDate,
    copyToClipboard,
    showQuickCommandModal
};

// Дебаг информация
console.log('🔧 Колыбель UI загружен. Доступные функции:', Object.keys(window.KolybelUI));