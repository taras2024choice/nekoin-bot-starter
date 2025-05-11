import json
import os
from datetime import datetime
from telegram import Bot

# Ваш токен бота (или читайте из .env)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TOKEN)

# Пути
BASE_DIR = os.path.dirname(__file__)
POLLS_FILE = os.path.join(BASE_DIR, "polls.json")
SNAPSHOT_DIR = os.path.join(BASE_DIR, "snapshots")
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

def load_polls():
    with open(POLLS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_results(polls):
    snapshot = []
    for p in polls:
        poll_id = p["poll_id"]
        try:
            poll_data = bot.get_poll(poll_id)
            results = {opt.text: opt.voter_count for opt in poll_data.options}
        except Exception as e:
            results = {"error": str(e)}
        snapshot.append({
            "poll_id": poll_id,
            "question": p["question"],
            "author": p["author"],
            "results": results,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    return snapshot

def save_snapshot(snapshot):
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    out_file = os.path.join(SNAPSHOT_DIR, f"snapshot_{ts}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    return out_file

if __name__ == "__main__":
    polls = load_polls()
    snapshot = fetch_results(polls)
    path = save_snapshot(snapshot)
    print(f"Snapshot saved to {path}")
