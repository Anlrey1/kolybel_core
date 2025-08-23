# telegram_bot.py — замените на эти части

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
        
        reply = ask_llм_with_context(f"{memory_prompt}\n\n{user_input}\n\nКак бы ты ответил?")
    
    # Сохраняем ответ в память
    memory.store(reply, {"type": "response", "source": "telegram"})
    
    await message.reply(reply)