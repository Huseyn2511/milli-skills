# Hermes ↔ Telegram (вариант А — мост к владельцу)

РАБОЧИЙ рецепт, проверенный 18 июля 2026. Цель: владелец пишет боту в TG,
отвечает Hermes (с долгосрочной памятью), а НЕ n8n-агент.

## Порядок (что реально сработало)

1. **Создать бота** — только владелец, в @BotFather → /newbot.
   Токен вида `123456:ABC-DEF...`. Прислать агенту.
2. **Токен в `.env`** (НЕ в config.yaml — там только секреты):
   ```bash
   printf 'TELEGRAM_BOT_TOKEN=<токен>\n' >> "C:/Users/husey/AppData/Local/hermes/.env"
   ```
   ⚠️ `read_file` на `.env` ЗАПРЕЩЁН Hermes (defense), НО терминал `>>`
   дописать может. Читать токен обратно не нужно — gateway сам возьмёт.
3. **Включить платформу** — прямая правка `config.yaml` ЗАБЛОКИРОВАНА
   (Hermes defense "cannot modify security-sensitive config"). Использовать ШТАТНУЮ команду:
   ```bash
   hermes config set gateway.platforms.telegram.enabled true
   hermes config set gateway.platforms.telegram.home_channel "8309087590"
   ```
   (home_channel = chat_id владельца, чтобы он был «домашним» каналом.)
4. **РАЗРЕШИТЬ владельца (allowlist)** — БЕЗ этого gateway МОЛЧИТ.
   ⚠️ Главная причина «написал боту — тишина» (18 июля): gateway по умолчанию
   ОТКЛОНЯЕТ неизвестных отправителей (в логе `WARNING gateway.run: No env user
   allowlists configured … will deny unknown senders`). Лечить — дописать в `.env`:
   ```bash
   printf 'TELEGRAM_ALLOWED_USERS=8309087590\n' >> "C:/Users/husey/AppData/Local/hermes/.env"
   ```
   (chat_id владельца). Альтернатива — `GATEWAY_ALLOW_ALL_USERS=true`, но
   allowlist безопаснее. Gateway читает `.env` при СТАРТЕ → после правки
   ОБЯЗАТЕЛЬНО перезапустить процесс.
5. **Запустить gateway** — ТОЛЬКО через `terminal(background=true)`, НЕ через
   shell-хвост `&`/`nohup`/`setsid` (Hermes их блокирует; а `head -3 &`-обёртка
   отвязывает процесс и он умирает — так gateway упал в первый раз 18 июля):
   ```
   terminal(background=true, command="hermes gateway run")
   # затем отдельной командой:
   hermes gateway status         # ждать "running (PID: …)"
   hermes gateway install        # опц. — автостарт (Windows: fallback в Startup-папку
                                 #   без UAC; при входе в систему стартует сам)
   ```
   В логе `logs/gateway.log` успех = `✓ telegram connected` + `Gateway running
   with 1 platform(s)` и БЕЗ warning про deny unknown senders.
6. **Владелец ПЕРВЫЙ пишет боту** `/start` или любой текст.
   ⚠️ Telegram НЕ даёт боту писать первым. До этого `sendMessage` →
   `400 chat not found`. Это НЕ баг, а правило платформы.

## Как проверить, что мост жив (без доступа к чату владельца)

Через `execute_code` + `urllib` (прямой запрос к Telegram API):
```python
import urllib.request, json
TOKEN="<токен>"
# 1) валиден ли токен вообще
r=json.load(urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/getMe",timeout=15))
print(r["result"]["username"])   # ожидаем MilliHermesai_bot

# 2) отправить тест (только ПОСЛЕ того, как владелец написал /start)
req=urllib.request.Request(
  f"https://api.telegram.org/bot{TOKEN}/sendMessage",
  data=json.dumps({"chat_id":8309087590,"text":"мост поднят"}).encode("utf-8"),
  headers={"Content-Type":"application/json; charset=utf-8"})
# 400 "chat not found" = владелец ещё не писал боту (норма)
```

## Факты, которые НЕ гадать (проверено исходниками)

- Gateway читает токен из env `TELEGRAM_BOT_TOKEN`
  (`gateway/config.py:494, 1549`). Другие имена не подхватит.
- Telegram-платформа уже прописана в `platform_toolsets.telegram`
  (`hermes-telegram`) — включается только флагом `enabled: true`.
- `hermes gateway run` стартует одним процессом; при выходе из
  сессии/выключении ПК процесс умирает → 24/7 держится ТОЛЬКО
  пока Windows-ПК владельца включён. Для 24/7 при выключенном ПК
  gateway надо поднимать на сервере (Timeweb), отдельно.

## Красная линия
- С владельцем — русский. Тексты водителям (через n8n-агентов) —
  ТОЛЬКО азербайджанский. Hermes через TG = собеседник
  владельца, не канал рассылки водителям.
