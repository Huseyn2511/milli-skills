#!/usr/bin/env python3
"""Запуск milli_pulse.py с N8N_API_KEY, прочитанным из .env Hermes (без шелл-экспорта секрета)."""
import os, sys, re

env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
env_path = os.path.abspath(env_path)
key = ""
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = re.match(r'^N8N_API_KEY\s*=\s*(.+?)\s*$', line)
            if m:
                key = m.group(1).strip().strip('"').strip("'")
                break
if key:
    os.environ["N8N_API_KEY"] = key
else:
    print("ERROR: N8N_API_KEY не найден в", env_path); sys.exit(1)

sys.path.insert(0, os.path.dirname(__file__))
import milli_pulse
milli_pulse.main()
