# telegram_bot.py — Telegram бот для Колыбель v2
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message

# Заглушки для отсутствующих модулей
try:
    from memory_core import MemoryCore
    memory = MemoryCore()
except ImportError:
    class MemoryCore:
        def store(self, document, metadata=None):
            print(f"[MEMORY] {document}")
        
        def get_similar(self, query, filter_type=None, n_results=5):
            return []
    memory = MemoryCore()

try:
    from template_engine import TemplateManager
    template_manager = TemplateManager()
except ImportError:
    class TemplateManager:
        def find_best_template(self, query):
            return None
    template_manager = TemplateManager()

try:
    from llm import ask_llm_with_context
except ImportError:
    def ask_llm_with_context(prompt, model="mistral"):
        return f"[LLM STUB] Response for: {prompt[:50]}..."

try:
    from template_engine import generate_from_template
except ImportError:
    def generate_from_template(template_id, context, use_training=False):
        return f"[TEMPLATE STUB] Generated content from {template_id}"

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Создаем роутер для обработки сообщений
dp = Router()

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_user_message(message: Message):
    user_input = message.text.strip()
    logger.info(f"📩 Получено сообщение от {message.from_user.id}: '{user_input}'")

    # Сохраняем запрос в память
    memory.store(document=user_input, metadata={"type": "user_query", "timestamp": datetime.now().isoformat()})
    
    # Подбор шаблона
    template = template_manager.find_best_template(user_input)
    
    if template:
        logger.info(f"📄 Найден шаблон: {template.title}")
        reply = generate_from_template(
            template.id,
            context={"query": user_input},
            use_training=True
        )
    else:
        # Фолбэк на прямую генерацию
        relevant_memories = memory.get_similar("successful response", filter_type="response", n_results=10)
        memory_prompt = "\n".join([f"[память] {m['content']}" for m in relevant_memories])
        
        # Исправлено: правильное имя функции
        reply = ask_llm_with_context(f"{memory_prompt}\n\n{user_input}\n\nКак бы ты ответил?")
    
    # Сохраняем ответ в память
    memory.store(reply, {"type": "response", "source": "telegram"})
    
    await message.reply(reply)