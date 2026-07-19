# Диагностика n8n / Milli (как проверять, что сломалось)

## ПЕРВЫЙ ШАГ: отличить «сервер лёг» от «сломан workflow»
Когда владелец говорит «n8n лёг / не работает совсем» — НЕ верить на слово и НЕ гадать
(правило 1.4). Сначала проверить внешнюю доступность любым окружением. Реальный
случай (июль 2026): владелец сказал «лёг, не работает», но curl показал
`/` 200, `/healthz` 200, `/rest/workflows` 401 — то есть сервер ЖИВ, а сломан был
конкретный НОВЫЙ workflow. Причина оказалась НЕ в cookie.

```
# Главная n8n
curl -sS -m 20 -o /dev/null -w "HTTP %{http_code}\n" https://8544767-wx953703.twc1.net/
# Health (Traefik/n8n)
curl -sS -m 15 -o /dev/null -w "HTTP %{http_code}\n" https://8544767-wx953703.twc1.net/healthz
# REST API — 401 означает «жив, просто требует ключ», НЕ «лёг»
curl -sS -m 15 -o /dev/null -w "HTTP %{http_code}\n" "https://8544767-wx953703.twc1.net/rest/workflows"
# Сайт
curl -sS -m 20 -o /dev/null -w "HTTP %{http_code}\n" https://taxi.milli-eticaret.com/
# SSH-порт (доступен ли сервер вообще)
timeout 8 bash -c 'cat < /dev/null > /dev/tcp/5.129.225.54/22' && echo OPEN || echo CLOSED
```
⚠️ curl может вернуть exit_code 23 (ERROR on write) при перенаправлении тела в /dev/null
на MSYS — игнорировать, смотреть на напечатанный HTTP-код.

Интерпретация:
- `/` 200 + `/healthz` 200 + `/rest/workflows` 401 → n8n ЖИВ, ищем баг в workflow.
- `401` на /rest/workflows = сервис отвечает, нужен API-ключ для чтения.
- Порт 22 OPEN = сервер доступен для логов.

## ПУТИ ПОЛУЧИТЬ ДОСТУП К ДИАГНОСТИКЕ (выбор владельца)
1. API-ключ n8n (лучший): Settings → API → создать key. С ключом сам читаю JSON
   workflow, нахожу баг, исправляю через API. Чисто, без скриншотов.
2. Логин/пароль n8n ИЛИ root-SSH (5.129.225.54): залезть в контейнер n8n-n8n-1,
   `docker logs`, увидеть реальную ошибку выполнения.
3. Скриншоты workflow целиком (каждый узел, особенно подозрительные: красный
   кружок, нет credential, body пустой). По скриншоту диагноз за минуту.

## ТИПИЧНЫЕ ПРИЧИНЫ «workflow не работает вообще» (из раздела 14 грабли)
- Schedule Trigger: по умолчанию Days; для минут — Trigger Interval → Minutes.
- Publish НЕ нажат → расписание НЕ работает (кнопка Publish вместо Published).
- HTTP Request: забыт Method=POST и ?token= → «Not Found».
- При копировании узла тело осталось старым (признак: scanTimeSec 0, wrote 0).
- Body с азерб. текстом вручную в сырой JSON → кавычки/апострофы рвут тело.
  Использовать «Using Fields Below» или Expression + JSON.stringify.
- Delete узла рвёт ОБЕ связи.
- Telegram: второй Trigger перебивает первый (один вебхук на бота).
- browserless: module.exports НЕ работает (только export default), лимит 180с,
  TIME GUARD ставить 165с.
