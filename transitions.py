# transitions.py

import re

from langchain_core.messages import AIMessage

import state_manager
from config import STATES


def _go_to_next_state(current_state_key):
    next_state = STATES[current_state_key].get('next_state')
    if next_state:
        state_manager.update_state('current_state', next_state)
        print(f"--- ПЕРЕХОД: {current_state_key} -> {next_state} ---")


def process_command(command, user_message=""):  # Добавляем user_message
    """
    Обрабатывает либо команду от кнопки, либо сообщение от пользователя.
    """
    state = state_manager.get_state()
    current_state = state['current_state']

    # --- ПРИОРИТЕТ: АНАЛИЗ ТЕКСТА ДЛЯ INTRODUCTION ---
    if current_state == 'INTRODUCTION' and user_message:
        names = re.findall(r'\b[А-Я][а-я]+', user_message)

        if len(names) >= 2:
            state_manager.update_state('participants', names[:2])
            _go_to_next_state(current_state)

            return None  # Завершаем обработку

    # --- НОВАЯ ЛОГИКА ДЛЯ РАЗДЕЛЕННЫХ СОСТОЯНИЙ ---
    elif current_state == 'GENERAL_SESSION_1_1' and user_message:
        # Каждый ответ на этом этапе увеличивает счетчик
        state['state_data']['positions_gathered'] += 1
        # Если это первый ответивший, мы просто ждем второго
        if state['state_data']['positions_gathered'] == 1:
            print("--- Получена первая позиция, ждем вторую ---")
        # Если ответил второй, переходим к этапу суммирования
        elif state['state_data']['positions_gathered'] >= 2:
            _go_to_next_state(current_state)  # Переход в GENERAL_SESSION_1_2
        return None

    # elif current_state == 'GENERAL_SESSION_1_2' and user_message:
    #     # Любой ответ на этапе суммирования (например, "да, все верно") триггерит переход дальше
    #     if any(word in user_message.lower() for word in ['да', 'верно', 'правильно', 'дальше']):
    #         _go_to_next_state(current_state)  # Переход в CAUCUS_PROMPT
    #     return None
    # --- КОНЕЦ НОВОЙ ЛОГИКИ ---

    # --- ОБРАБОТКА КОМАНД ОТ КНОПОК ---
    if not command:
        return None  # Если нет ни текста для INTRODUCTION, ни команды, выходим

    print(f"--- Получена команда '{command}' в состоянии '{current_state}' ---")

    if command == "PROCEED_TO_CAUCUS" and current_state == 'GENERAL_SESSION_1_2':
        _go_to_next_state(current_state)

    elif "START_CAUCUS_" in command and current_state == 'CAUCUS_PROMPT':
        participant_name = command.replace("START_CAUCUS_", "")

        if participant_name in state['participants']:
            state['state_data']['caucus_target'] = participant_name
            _go_to_next_state(current_state)

    elif command == "CONCLUDE_CAUCUS" and current_state == 'CAUCUS_SESSION':
        target = state['state_data'].get('caucus_target')

        if target:
            if target not in state['state_data']['caucus_completed_for']:
                state['state_data']['caucus_completed_for'].append(target)
            state['state_data']['caucus_target'] = None

            remaining = [p for p in state['participants'] if p not in state['state_data']['caucus_completed_for']]

            if not remaining:
                _go_to_next_state(current_state)  # в GENERAL_SESSION_2
                return AIMessage(content="Все кокусы завершены. Переходим к общей сессии.")
            else:
                state_manager.update_state('current_state', 'CAUCUS_PROMPT')
                print(f"--- ВОЗВРАТ к CAUCUS_PROMPT для {remaining[0]} ---")
                return AIMessage(
                    content=f"Кокус с {target} завершен. Теперь необходимо провести сессию с {remaining[0]}."
                    )

    elif command == "PROCEED_TO_AGREEMENT" and current_state == "GENERAL_SESSION_2":
        _go_to_next_state(current_state)

    elif command == "PROCEED_TO_SANCTIONS" and current_state == 'AGREEMENT_DRAFTING':
        _go_to_next_state(current_state)

    elif command == "PROCEED_TO_CONCLUSION" and current_state == 'SANCTIONS_AND_GUARANTEES':
        _go_to_next_state(current_state)

    elif command == "END_SESSION" and current_state == 'CONCLUSION':
        _go_to_next_state(current_state)

    # Другие команды можно добавить здесь
    return None
