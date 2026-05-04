import pandas as pd
import redis
import json

print("1. Подключаемся к Redis (Feature Store)...")
cache = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

print("2. Читаем исторические данные...")
df = pd.read_csv('data/raw/creditcard.csv')

normal_profile = df[df['Class'] == 0].drop(columns=['Class', 'Amount', 'Time']).iloc[0].to_dict()
fraud_profile = df[df['Class'] == 1].drop(columns=['Class', 'Amount', 'Time']).iloc[0].to_dict()

print("3. Загружаем профили в оперативную память...")
# Внимательно: здесь мы кладем ОБА профиля
cache.set('profile:card_normal_001', json.dumps(normal_profile))
cache.set('profile:card_hacked_002', json.dumps(fraud_profile))

print("\n--- ДИАГНОСТИКА БАЗЫ ДАННЫХ ---")
# Заставляем скрипт проверить самого себя
if cache.exists('profile:card_normal_001'):
    print("✅ Нормальный клиент: НАЙДЕН В БАЗЕ")
else:
    print("❌ Нормальный клиент: НЕ НАЙДЕН")

if cache.exists('profile:card_hacked_002'):
    print("✅ Хакер: НАЙДЕН В БАЗЕ")
else:
    print("❌ Хакер: НЕ НАЙДЕН")