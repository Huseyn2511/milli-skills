Milli Taksi (Баку/Сумгаит). Владелец Гусейн (десктоп-Hermes осн., ТГ запасной). Агентов по одному. Цена до заказа окончательна, тон Siz, водителям только азерб. Тариф Milli на 10% дешевле Яндекса. Красные линии: 2.50 только Баку, iPhone только водителям, бел/бордо только Taksi.
§
OpenRouter deepseek/deepseek-v4-flash
§
Память: ПК push → github Huseyn2511/milli-skills memory-sync/ (ghp_DH5h...). Сервер pull каждые 5мин cron; рестарт gateway при изменении.
§
Daily Orders файл: /home/node/.n8n/milli/daily_orders.json на сервере Timeweb. Читать: docker exec n8n-n8n-1 cat /home/node/.n8n/milli/daily_orders.json. Формат: {дата: {total, statuses, lastUpdate}}. Из любого канала читаю через paramiko.
§
Сервер модель: deepseek/deepseek-v4-flash через OpenRouter (обновлено 21.07). TG-бот @MilliHermesai_bot. Для проверки n8n нужно добавить N8N_API_KEY в .env на сервере — ключ leyla. Контекст с TG: синхронизация памяти разорвана, нужен push в GitHub.