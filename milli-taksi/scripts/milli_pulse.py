#!/usr/bin/env python3
"""Milli Taksi — живой пульс из n8n API (БЕЗ SSH).
Запуск: python milli_pulse.py
Читает N8N_API_KEY из окружения (.env Hermes). Тянет последний прогон
воркфлоу ОФИС v14, где есть узел 'Пульс · запись', и печатает цифры.
ВАЖНО: НЕ лезть в SSH root@5.129.225.54 — он закрыт. Пульс = только этот путь.
"""
import os, json, urllib.request

KEY = os.environ.get("N8N_API_KEY", "").strip()
BASE = "https://8544767-wx953703.twc1.net/api/v1"
WID = "YKDeJegcr2Nwbulq"

def get(path):
    req = urllib.request.Request(BASE + path, headers={"X-N8N-API-KEY": KEY, "Accept": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))

def main():
    if not KEY:
        print("ERROR: N8N_API_KEY не задан в окружении (.env)"); return
    ex = get(f"/executions?workflowId={WID}&limit=30&includeData=false")
    data = ex.get("data", ex)
    for e in data:
        try:
            full = get(f"/executions/{e['id']}?includeData=true")
        except Exception:
            continue
        rd = (full.get("data") or {}).get("resultData", {}).get("runData", {})
        if "Пульс · запись" in rd:
            try:
                out = rd["Пульс · запись"][0]["data"]["main"][0][0]["json"]
                w = out.get("wrote", out)
                if w.get("na_linii") is None and out.get("ok") is False:
                    print("⚠ COOKIE_DEAD — нужна свежая cookie UpTaxi (F12 после логина)"); return
                print(f"🔵 ПУЛЬС ({w.get('hour','?')}) exec {e['id']}")
                print(f"На линии: {w.get('na_linii')}")
                print(f"Горит: {w.get('gorit')}")
                print(f"Свободно: {w.get('available')}")
                print(f"Готов без заказа: {w.get('gotov_bez_zakaza')}  Ищем: {w.get('ishem')}")
                print(f"Доска: всего {w.get('board_total')}, горит {w.get('board_burning')}, без водителя {w.get('board_burning_free')}")
                return
            except Exception as err:
                print("parse error:", err); return
    print("Не нашёл прогон с пульсом за последние 30 исполнений.")

if __name__ == "__main__":
    main()
