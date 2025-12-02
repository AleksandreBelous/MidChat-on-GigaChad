from langchain_gigachat.chat_models import GigaChat
from langchain_core.messages import SystemMessage, HumanMessage
import config

# Инициализация модели один раз при импорте модуля
giga = GigaChat(credentials=config.API_KEY, verify_ssl_certs=False)


def get_assistant_response(system_prompt, history, user_message):
    """Формирует запрос и вызывает GigaChat API."""
    messages_for_api = [SystemMessage(content=system_prompt)] + history + [HumanMessage(content=user_message)]

    try:
        res = giga.invoke(messages_for_api)
        return res

    except Exception as e:
        print(f"Ошибка при вызове GigaChat API: {e}")
        # В реальном приложении здесь должно быть логирование
        raise  # Пробрасываем исключение выше, чтобы его обработал эндпоинт
