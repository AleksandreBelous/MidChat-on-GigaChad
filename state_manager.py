# Упрощенное управление состоянием в памяти.
# В будущем можно заменить на класс с подключением к Redis или БД.

_session_state = {
        "session_id"   : "single_session",
        "current_state": "INTRODUCTION",
        "participants" : [],
        "history"      : [],
        "state_data"   : {
                "positions_gathered": 0
                }
        }


def get_state():
    """Возвращает текущее состояние сессии."""
    return _session_state


def update_state(key, value):
    """Обновляет ключ в состоянии сессии."""
    if key in _session_state:
        _session_state[key] = value


def reset_state():
    """Сбрасывает сессию к начальному состоянию."""
    global _session_state

    _session_state = {
            "session_id"   : "single_session",
            "current_state": "INTRODUCTION",
            "participants" : [],
            "history"      : [],
            "state_data"   : {
                    "positions_gathered"  : 0,
                    "caucus_target"       : None,  # С кем сейчас идет кокус
                    "caucus_completed_for": [],  # Для кого кокус уже завершен
                    "caucus_history"      : { },  # {'Имя1': [...], 'Имя2': [...]}
                    "public_agenda"       : []  # Что можно вынести на общую сессию
                    }
            }

    print("--- СЕССИЯ СБРОШЕНА ---")


def add_to_history(message):
    """Добавляет сообщение в историю."""
    _session_state["history"].append(message)
