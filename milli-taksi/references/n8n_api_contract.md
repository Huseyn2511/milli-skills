# n8n API contract + v14 fix recipe (verified 18 July 2026)

Host: `https://8544767-wx953703.twc1.net/api/v1`
Auth: header `X-N8N-API-KEY: <key>` (NOT `Authorization: Bearer`).

## Working endpoints
- `GET /workflows?limit=100` — list (all 17 were `active:false` on 17 July).
- `GET /workflows/{id}` — full JSON (nodes/connections/parameters). Read this, not screenshots.
- `GET /executions?workflowId={id}&limit=20` — recent runs.
- `GET /executions/{id}?includeData=true` — **the real error source**.
  - Top-level error: `data.resultData.error` (e.g. `Referenced node doesn't exist`).
  - Per-node error: `data.resultData.runData[<node>][0].error.message`.
- `POST /workflows/{id}/activate` — **enable a workflow** (see below).

## GOTCHAS (cost real time this session)
1. **`POST /executions` and `POST /workflows/{id}/execute` → HTTP 405** (Method Not Allowed).
   Execution via API is NOT exposed in n8n v2.28.7 on this host.
   ⇒ Cannot inject a cookie by running the "Куки · запись" node via API.
   ⇒ Cannot fire the "Разведчик" manual trigger via API.
   ⇒ To run a node: do it from the n8n UI, or use the Telegram command `куки <token>`.
2. **`active` is READ-ONLY in `PUT /workflows/{id}` body** → returns `active is read-only`.
   To activate: `POST /workflows/{id}/activate` with header
   `Content-Type: application/json` and body `{}`.
   - No Content-Type → 415. GET → 404. Rate-limit "too many requests" if you spam it (wait ~12s).
3. **`PUT /workflows/{id}` body shape** is strict:
   only `{name, nodes, connections, settings}` accepted.
   `settings` must be exactly `{"executionOrder":"v1"}` —
   extra keys (`binaryMode`, `availableInMCP`) are rejected with
   `request/body/settings must NOT have additional properties`.
4. Prefer **execute_code + Python urllib.request** over MSYS curl on this Windows host
   (curl chokes on /tmp writes and hangs on confirmation prompts).

## v14 real root causes (verified, not guessed)
Symptom: "n8n лёг / новый workflow не работает вообще / бот молчит".
1. **All 17 workflows `active=false`** → no trigger (schedule or Telegram) fires.
   Fixed by `POST …/activate`.
2. **Stale renamed-node references.** Nodes were renamed:
   `Telegram Trigger` → `Мозг · триггер TG`,
   `Тема дня` → `Kontent · тема дня`,
   but expressions `$('Telegram Trigger')` / `$('Тема дня')` stayed.
   ⇒ agent crashed with `Referenced node doesn't exist` at `Мозг · память 20`
   BEFORE producing a reply → bot silent. Fixed by rewriting all `$('…')` refs.
3. **Cookie-write IF too strict.** Condition was `startsWith "куки"` (case-sensitive),
   so the owner's `"Новый куки - <token>"` fell through to the chat agent and the
   file was never written. Fixed to `contains` (case-insensitive) + regex token extract
   `[a-z0-9]{16,64}`.
4. **Bot self-report was stale.** System prompt said "browser not connected" while
   browserless WAS working — the real failure was the stale node ref, not the hardware.
   Always verify via execution logs, not the bot's words.

## Cookie reality (UpTaxi)
- `cabinetUpTaxi` exists ONLY AFTER full login + captcha + landing in the
  `1165.upphone.ru:4422` panel. Copying it BEFORE login → dead token.
- Dead token symptom: verification node returns
  `{"alive":false,"note":"редирект на логин"}`.
- First owner token `lmnaqabr0nbirm8kb4lfi5js2j` was dead for exactly this reason.
- SSH `root@5.129.225.54` is DENIED and is a DIFFERENT machine (Ubuntu VPS,
  not the n8n container on Timeweb Amsterdam) — useless for editing n8n files.
