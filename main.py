from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_core.messages import HumanMessage, AIMessage

import config
import state_manager
import gigachat_service
import transitions
from actions import get_actions_for_state

app = Flask(__name__)
# app.config['JSON_AS_ASCII'] = False
CORS(app)


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    command = data.get('command')

    # 1. Добавляем действие пользователя в общую историю
    if command:
        history_message = f"[Выполнена команда: {command}]"
        state_manager.add_to_history(HumanMessage(content=history_message))
    elif user_message:
        state_manager.add_to_history(HumanMessage(content=user_message))

    # 2. Обрабатываем команду или сообщение, что может изменить состояние.
    # Эта функция теперь может вернуть прямой ответ (AIMessage) для уточняющих вопросов.
    direct_response = transitions.process_command(command, user_message)

    assistant_response_content = ""

    if direct_response:
        # Если transitions.py вернул готовый ответ, используем его
        assistant_response = direct_response
        state_manager.add_to_history(assistant_response)
    else:
        # Если прямого ответа нет, генерируем его с помощью LLM
        state = state_manager.get_state()
        current_state_key = state['current_state']
        state_info = config.STATES.get(current_state_key, { })

        # Формируем промпт
        system_prompt_template = state_info.get('prompt', '')
        if current_state_key == 'CAUCUS_SESSION' and state['state_data'].get('caucus_target'):
            system_prompt = system_prompt_template.replace('{participant_name}', state['state_data']['caucus_target'])
        else:
            system_prompt = system_prompt_template
        full_system_prompt = f"{config.ROLE}\n\nИнструкция для этапа '{current_state_key}': {system_prompt}"

        # Выбираем правильную историю
        active_history = state['history']
        if current_state_key == 'CAUCUS_SESSION' and state['state_data'].get('caucus_target'):
            target = state['state_data']['caucus_target']
            if target not in state['state_data']['caucus_history']:
                state['state_data']['caucus_history'][target] = []
            active_history = state['state_data']['caucus_history'][target]

        try:
            # Передаем историю БЕЗ последнего сообщения ассистента, если оно там есть
            history_for_api = [msg for msg in active_history if msg.type != 'ai']
            llm_response = gigachat_service.get_assistant_response(full_system_prompt, history_for_api, "")
            state_manager.add_to_history(llm_response)
            # Если это кокус, дублируем ответ в его личную историю
            if current_state_key == 'CAUCUS_SESSION':
                active_history.append(llm_response)
            assistant_response = llm_response
        except Exception as e:
            print(f"ОШИБКА LLM: {e}")
            return jsonify({ "error": "Внутренняя ошибка GigaChat API" }), 500

    # Получаем действия для финального состояния
    final_state = state_manager.get_state()
    actions = get_actions_for_state(
            final_state['current_state'],
            final_state['participants'],
            final_state['state_data'].get('caucus_completed_for', [])
            )

    return jsonify({
            "response": assistant_response.content,
            "state"   : final_state['current_state'],
            "actions" : actions
            }
            )


@app.route('/api/reset', methods=['POST'])
def reset():
    state_manager.reset_state()
    # Возвращаем стартовое сообщение и действия
    actions = get_actions_for_state("INTRODUCTION")
    return jsonify({
            "response": "Здравствуйте! Я - MidChat, ваш модератор. Пожалуйста, представьте участников переговоров, написав их имена в поле ниже (пример: Александр, Мария).",
            "state"   : "INTRODUCTION",
            "actions" : actions
            }
            )


if __name__ == '__main__':
    state_manager.reset_state()
    app.run(host='0.0.0.0', port=5001, debug=True)
