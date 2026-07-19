#!/usr/bin/env python3
"""
Yango price monitor — Milli vs Yandex (Baku).
Drives the real Yango app on a connected phone via ADB, types Baku addresses,
reads the price from the UI, logs to CSV, and reports to Telegram.

NO fake GPS. The city is switched inside the Yango UI by typing "Baku".
Phone must be connected via USB:  adb devices  ->  RF8N324LKLB
"""
import os, re, csv, time, datetime, subprocess, sys, json

SER = os.environ.get("YANGO_SER", "RF8N324LKLB")
PKG = "com.yandex.yango"
UI = "/sdcard/yango_ui.xml"
LOCAL = os.path.join(os.path.expanduser("~"), "yango_ui.xml")
DATA_DIR = os.path.join(os.path.expanduser("~"), "milli-skills", "data")

# Routes to monitor (from -> to), typed in latin/cyrillic as the app expects
ROUTES = [
    ("Baku", "Aeroport"),          # centre -> airport
    ("Baku", "28 Mall"),            # centre -> mall
    ("Baku", "Narimanov"),          # centre -> narimanov
]

TG_CHAT = "8309087590"
TG_BOT = os.environ.get("TG_BOT_TOKEN", "")
if not TG_BOT:
    envp = os.path.join(os.path.expanduser("~"), "AppData", "Local", "hermes", ".env")
    try:
        for line in open(envp, encoding="utf-8"):
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                TG_BOT = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass

def adb(args):
    cmd = ["adb", "-s", SER] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60)

def tap(x, y):
    adb(["shell", "input", "tap", str(x), str(y)])

def text(s):
    # clear then type; Yango edittexts accept latin/cyrillic
    adb(["shell", "input", "text", s])

def dump():
    adb(["shell", "uiautomator", "dump", UI])
    adb(["shell", "cat", UI]).stdout  # ensure written
    p = subprocess.run(["adb", "-s", SER, "shell", "cat", UI], capture_output=True, text=True, timeout=30)
    open(LOCAL, "w", encoding="utf-8").write(p.stdout)

def texts():
    dump()
    out = {}
    for m in re.finditer(r'text="([^"]*)"', open(LOCAL, encoding="utf-8").read()):
        t = m.group(1).strip()
        if t:
            out.setdefault(t, 0)
            out[t] += 1
    return out

def bounds_for(label):
    xml = open(LOCAL, encoding="utf-8").read()
    # match text="label" ... bounds="[x,y][x,y]"  (label may be exact or prefix)
    pat = re.compile(r'text="%s"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"' % re.escape(label))
    m = pat.search(xml)
    if m:
        x1,y1,x2,y2 = map(int, m.groups())
        return ((x1+x2)//2, (y1+y2)//2)
    # try prefix
    pat2 = re.compile(r'text="%s[^"]*"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"' % re.escape(label))
    m = pat2.search(xml)
    if m:
        x1,y1,x2,y2 = map(int, m.groups())
        return ((x1+x2)//2, (y1+y2)//2)
    return None

def launch():
    adb(["shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1"])
    time.sleep(7)

def reset_to_entry():
    """From any state, get back to the 'Ввести адрес' entry screen."""
    t = texts()
    if "Ввести адрес" in t:
        c = bounds_for("Ввести адрес")
        if c: tap(*c); time.sleep(4); return True
    # if already in address typing screen, fine
    return "Куда едем?" in t or "Ваше местоположение" in t

def measure(from_q, to_q):
    """Return price string or None for one route."""
    # 1) ensure we are at entry
    if not reset_to_entry():
        launch(); time.sleep(3); reset_to_entry()
    # 2) type FROM (Baku)
    et = bounds_for("Ввести адрес")  # button already tapped -> edittext focused
    # tap edittext area (center of screen upper)
    adb(["shell", "input", "tap", "666", "420"])
    time.sleep(1)
    # clear existing
    adb(["shell", "input", "keyevent", "KEYCODE_MOVE_END"])
    for _ in range(20):
        adb(["shell", "input", "keyevent", "KEYCODE_DEL"])
    text(from_q)
    time.sleep(3)
    # pick first Baku suggestion
    c = bounds_for("Баку") or bounds_for("Baku")
    if c: tap(*c); time.sleep(5)
    # 3) now "Куда едем?" — type TO
    t = texts()
    if "Куда едем?" not in t and "Ваше местоположение" not in t:
        # try tapping the 'to' field
        c2 = bounds_for("Куда едем?")
        if c2: tap(*c2)
    time.sleep(1)
    adb(["shell", "input", "tap", "666", "420"])
    time.sleep(1)
    for _ in range(20):
        adb(["shell", "input", "keyevent", "KEYCODE_DEL"])
    text(to_q)
    time.sleep(3)
    # pick first suggestion containing the destination
    c3 = bounds_for(to_q[:8]) or bounds_for(to_q)
    if c3: tap(*c3); time.sleep(6)
    # 4) read price
    t = texts()
    price = None
    for k in t:
        if "₼" in k or "azn" in k.lower() or "манат" in k.lower():
            price = k; break
    if not price:
        # try "от X ₼"
        for k in t:
            if k.startswith("от") and "₼" in k:
                price = k; break
    return price

def tg_send(msg):
    if not TG_BOT:
        print("TG_BOT_TOKEN not set, skip send:", msg[:80])
        return
    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{TG_BOT}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": TG_CHAT, "text": msg}).encode()
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=20)
    except Exception as e:
        print("tg err:", e)

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    csv_path = os.path.join(DATA_DIR, "yango_prices.csv")
    if not os.path.exists(csv_path):
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["ts", "route", "price"])
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = []
    for frm, to in ROUTES:
        try:
            p = measure(frm, to)
        except Exception as e:
            p = f"ERR {e}"
        rows.append((now, f"{frm}->{to}", p or "NONE"))
        print(now, frm, "->", to, "=", p)
        time.sleep(2)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for r in rows: w.writerow(r)
    summary = "\n".join(f"• {r[1]}: {r[2]}" for r in rows)
    tg_send(f"📊 YANGO ЗАМЕР ({now}, Баку):\n{summary}")
    # back to home for next cycle
    adb(["shell", "input", "keyevent", "KEYCODE_BACK"])
    adb(["shell", "input", "keyevent", "KEYCODE_BACK"])

if __name__ == "__main__":
    main()
