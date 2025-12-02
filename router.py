# router.py
import json
from langchain_core.messages import SystemMessage, HumanMessage
from gigachat_service import giga


def get_next_action(current_state, user_message, participants, history):
    """
    Определяет следующее действие системы с помощью LLM.
    """

    # Для каждого состояния мы определяем свои возможные действия
    # router.py -> actions_schema

    actions_schema = {
            "INTRODUCTION"     : [
                    { "action"     : "GATHER_NAMES",
                      "description": "Пользователь представил двух или более участников. Пример: 'Меня зовут Александр, а это Мария'."
                      },
                    { "action"     : "WAIT",
                      "description": "Пользователь еще не представил участников или говорит на отвлеченные темы."
                      }
                    ],
            "GENERAL_SESSION_1": [
                    { "action"     : "GATHER_POSITION",
                      "description": "Один из участников высказал свою позицию. Пример: 'Я хочу получить инвестиции'."
                      },
                    { "action"     : "PROCEED_TO_CAUCUS",
                      "description": "Оба участника высказали свои позиции, это финал этапа."
                      },
                    { "action"     : "WAIT",
                      "description": "Диалог не содержит четкой позиции или является отвлеченным."
                      }
                    ],
            "CAUCUS_PROMPT"    : [
                    { "action"     : "START_CAUCUS(participant_name)",
                      "description": "Пользователь явно согласился начать кокус со своим именем."
                      },
                    { "action"     : "CLARIFY_WHICH_PARTICIPANT",
                      "description": "Пользователь согласился начать кокус, но неясно, кто именно. Пример: 'Да, я готов', 'Хорошо, давайте'."
                      },
                    { "action"     : "WAIT",
                      "description": "Пользователь не дал четкого согласия на кокус или задает отвлеченные вопросы."
                      }
                    ],
            "CAUCUS_SESSION"   : [
                    { "action"     : "CONCLUDE_CAUCUS",
                      "description": "Пользователь сказал, что он закончил, ему все понятно, или спрашивает, что дальше. Пример: 'Думаю, это все', 'Я закончил', 'Мне все понятно, что дальше?', 'Хватит'."
                      },
                    { "action"     : "CONTINUE_CAUCUS",
                      "description": "Пользователь продолжает обсуждать вопросы в рамках кокуса"
                      }
                    ]
            }

    # Выбираем схему для текущего состояния, или пустой список, если ее нет
    possible_actions = actions_schema.get(current_state, [])

    if not possible_actions:
        return { "action": "WAIT" }

    # Преобразуем историю в читаемый формат
    history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in history])

    prompt = f"""
    Ты - система маршрутизации диалога. Твоя задача - проанализировать последнее сообщение пользователя в контексте всей беседы и определить, какое действие нужно выполнить.
    Текущее состояние диалога: {current_state}
    Участники: {participants}

    История диалога:
    {history_str}

    Последнее сообщение пользователя: "{user_message}"

    Доступные действия для состояния '{current_state}':
    {json.dumps(possible_actions, indent=2, ensure_ascii=False)}

    Проанализируй ПОСЛЕДНЕЕ СООБЩЕНИЕ в контексте ИСТОРИИ и выбери ОДНО наиболее подходящее действие.
    Верни ответ в формате JSON. Например: {{"action": "ACTION_NAME"}}
    Если ни одно действие не подходит, верни {{"action": "WAIT"}}.
    """

    try:
        # Мы используем более дешевую и быструю модель для роутинга, если это возможно
        # В данном случае, оставим Pro, но в реальном проекте можно использовать Lite
        router_model = giga
        response = router_model.invoke([SystemMessage(content=prompt)])

        # Пытаемся распарсить JSON из ответа модели
        action_json = json.loads(response.content)
        return action_json

    except (json.JSONDecodeError, Exception) as e:
        print(f"--- Ошибка роутера: не удалось получить или распарсить действие. {e} ---")
        return { "action": "WAIT" }


def extract_agenda_from_caucus(caucus_history):
    """
    Использует LLM для извлечения публичной повестки из диалога кокуса.
    """
    if not caucus_history:
        return []

    history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in caucus_history])

    prompt = f"""
    Проанализируй следующий диалог из конфиденциальной сессии (кокуса).
    Твоя задача - определить, какие темы или вопросы участник готов вынести на общее обсуждение.
    
    Диалог кокуса:
    {history_str}
    
    Извлеки 1-3 самых важных пункта, которые можно обсуждать публично.
    Верни результат в виде JSON-массива строк. Например: ["Обсудить размер инвестиций", "Обсудить сроки окупаемости"].
    Если участник не сказал ничего конкретного, верни пустой массив [].
    """
    try:
        response = giga.invoke([SystemMessage(content=prompt)])
        agenda_items = json.loads(response.content)

        if isinstance(agenda_items, list):
            return agenda_items

        return []

    except (json.JSONDecodeError, Exception) as e:
        print(f"--- Ошибка извлечения повестки: {e} ---")
        return []
