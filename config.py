import os
import json
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Загрузка инструкций и состояний
try:
    with open('instuctions.json', 'r', encoding='utf-8') as f:
        instructions = json.load(f)
    ROLE = instructions['role']
    STATES = instructions['states']

except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Критическая ошибка при загрузке instuctions.json: {e}")
    exit()

# Проверка наличия ключа API
if not API_KEY:
    print("Критическая ошибка: API_KEY не найден в .env файле.")
    exit()
