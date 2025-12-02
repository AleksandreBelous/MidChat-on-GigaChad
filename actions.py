# actions.py

# Для каждого состояния определяем список возможных действий (команд)
# Каждое действие - это словарь с 'command' (для бэкенда) и 'label' (для кнопки на фронтенде)
AVAILABLE_ACTIONS = {
        "INTRODUCTION"            : [
                # { "command": "PROVIDE_NAMES",
                #   "label"  : "Представить участников"
                #   }
                ],

        "GENERAL_SESSION_1_2"     : [
                # { "command": "STATE_POSITION",
                #   "label"  : "Изложить позицию"
                #   },
                { "command": "PROCEED_TO_CAUCUS",
                  "label"  : "Позиции ясны, перейти к кокусам"
                  }
                ],

        "CAUCUS_PROMPT"           : [
                # Эти действия будут генерироваться динамически в main.py
                ],

        "CAUCUS_SESSION"          : [
                { "command": "CONTINUE_CAUCUS",
                  "label"  : "Продолжить обсуждение"
                  },
                { "command": "CONCLUDE_CAUCUS",
                  "label"  : "Завершить кокус"
                  }
                ],

        "GENERAL_SESSION_2"       : [
                { "command": "DISCUSS_AGENDA",
                  "label"  : "Обсудить повестку"
                  },
                { "command": "PROCEED_TO_AGREEMENT",
                  "label"  : "Перейти к выработке соглашения"
                  }
                ],

        "AGREEMENT_DRAFTING"      : [
                { "command": "PROCEED_TO_SANCTIONS",
                  "label"  : "Перейти к обсуждению санкций"
                  }
                ],

        "SANCTIONS_AND_GUARANTEES": [
                { "command": "PROCEED_TO_CONCLUSION",
                  "label"  : "Перейти к завершению"
                  }
                ],

        "CONCLUSION"              : [
                { "command": "END_SESSION",
                  "label"  : "Завершить переговоры"
                  }
                ],
        "END"                     : [

                ]
        }


def get_actions_for_state(state_key, participants=None, completed_caucuses=None):
    """Возвращает список действий для текущего состояния."""
    if participants is None:
        participants = []

    if completed_caucuses is None:
        completed_caucuses = []

    # Особая логика для CAUCUS_PROMPT
    if state_key == 'CAUCUS_PROMPT':
        remaining = [p for p in participants if p not in completed_caucuses]
        return [{ "command": f"START_CAUCUS_{p}", "label": f"Начать кокус с {p}" } for p in remaining]

    return AVAILABLE_ACTIONS.get(state_key, [])
