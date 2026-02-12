import os
import json
import random
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from fastapi import FastAPI, Request
from openai import OpenAI

# ==========
# Settings
# ==========
JST = timezone(timedelta(hours=9))
USAGE_FILE = "user_usage.json"
DAILY_LIMIT = 5

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
LINE_TOKEN = os.environ["LINE_TOKEN"]

client = OpenAI(api_key=OPENAI_API_KEY)
app = FastAPI()

# ==========
# Tarot Cards (まずは大アルカナ22枚)
# ==========
CARDS = [
    "The Fool","The Magician","The High Priestess","The Empress",
    "The Emperor","The Lovers","The Chariot","Strength",
    "The Hermit","Wheel of Fortune","Justice","The Hanged Man",
    "Death","Temperance","The Devil","The Tower",
    "The Star","The Moon","The Sun","Judgement","The World"
]

GENRES = {
    "1": "恋愛",
    "2": "仕事",
    "3": "金運",
    "4": "人間関係",
    "5": "今日の運勢",
}

# ==========
# Usage Storage (JSON)
# ==========
def _today_str() -> str:
    return datetime.now(JST).strftime("%Y-%m-%d")

def _load_usage() -> Dict[str, Any]:
    if not os.path.exists(USAGE_FILE):
        return {}
    try:
        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_usage(data: Dict[str, Any]) -> None:
    with open(USAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def get_remaining(user_id: str) -> int:
    data = _load_usage()
    today = _today_str()

    u = data.get(user_id)
    if not u or u.get("date") != today:
        return DAILY_LIMIT

    used = int(u.get("count", 0))
    return max(0, DAILY_LIMIT - used)

def consume_once(user_id: str) -> int:
    """
    1回消費する。消費後の残回数を返す。
    上限を超える場合は残回数0のまま。
    """
    data = _load_usage()
    today = _today_str()

    u = data.get(user_id)
    if not u:
        data[user_id] = {"date": today, "count": 1, "streak": 1, "last_used": today}
        _save_usage(data)
        return DAILY_LIMIT - 1

    # 日付が変わったらリセット＋連続日数更新
    if u.get("date") != today:
        last_used = u.get("last_used")
        try:
            last_dt = datetime.strptime(last_used, "%Y-%m-%d").replace(tzinfo=JST)
        except Exception:
            last_dt = None

        streak = int(u.get("streak", 0))
        if last_dt and (datetime.now(JST).date() - last_dt.date()).days == 1:
            streak += 1
        else:
            streak = 1

        u = {"date": today, "count": 0, "streak": streak, "last_used": today}

    used = int(u.get("count", 0))
    if used >= DAILY_LIMIT:
        data[user_id] = u
        _save_usage(data)
        return 0

    u["count"] = used + 1
    u["last_used"] = today
    data[user_id] = u
    _save_usage(data)
    return max(0, DAILY_LIMIT - u["count"])

def get_streak(user_id: str) -> int:
    data = _load_usage()
    u = data.get(user_id)
    if not u:
        return 0
    return int(u.get("streak", 0))

# ==========
# Core Logic
# ==========
def draw_three():
    return random.sample(CARDS, 3)

def build_menu_text(user_id: str) -> str:
    remaining = get_remaining(user_id)
    return (
        f"🔮 今日の10円占い（残り{remaining}回）\n\n"
        "1️⃣ 恋愛（相手の気持ち／進展）\n"
        "2️⃣ 仕事（転職／評価／流れ）\n"
        "3️⃣ 金運（出費／収入／チャンス）\n"
        "4️⃣ 人間関係（距離感／修復）\n"
        "5️⃣ 今日の運勢（総合）\n\n"
        "番号で選んでください（1〜5）"
    )

def genre_prompt(genre_name: str, question: str, cards3: list[str]) -> str:
    # 10円仕様：短く具体的（450〜650文字くらい）
    base = f"""
あなたはプロのタロット占い師です。
ジャンル: {genre_name}

ユーザーの入力: {question}

3枚引き:
①現状: {cards3[0]}
②注意: {cards3[1]}
③行動: {cards3[2]}

以下の形式で、日本語で短く具体的に（全体450〜650文字目安）書いてください。

出力形式:
🧭結論（1行）
（2〜4行の説明）
✅今日の一手（1つ、具体）
⚠️NG行動（1つ）
🌙ひとこと（1行、前向き）
"""
    return base.strip()

def ai_reading(genre_name: str, question: str, cards3: list[str]) -> str:
    prompt = genre_prompt(genre_name, question, cards3)

    r = client.responses.create(
        model="gpt-5-mini",
        input=prompt
    )
    return r.output_text

def reply(token: str, text: str) -> None:
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers=headers,
        json={
            "replyToken": token,
            "messages": [{"type": "text", "text": text}]
        },
        timeout=10
    )

# ==========
# Routes
# ==========
@app.get("/")
def root():
    return {"status": "tarot bot running"}

@app.post("/callback")
async def callback(req: Request):
    body = await req.json()

    for e in body.get("events", []):
        if e.get("type") != "message":
            continue

        user_id = e.get("source", {}).get("userId", "unknown")
        text = (e.get("message", {}).get("text") or "").strip()
        reply_token = e.get("replyToken")

        # ① メニューを出す（回数消費しない）
        if text in {"10円占い", "占い", "10円"}:
            reply(reply_token, build_menu_text(user_id))
            continue

        # ② ジャンル選択（ここで回数消費）
        if text in GENRES:
            remaining = get_remaining(user_id)
            if remaining <= 0:
                streak = get_streak(user_id)
                reply(reply_token, f"🔒今日は5回までです。また明日！\n（連続{streak}日）")
                continue

            # 1回消費
            remaining_after = consume_once(user_id)
            streak = get_streak(user_id)

            genre_name = GENRES[text]
            cards3 = draw_three()

            # 質問文：ジャンルだけしか来ないので、内部で補う
            question = f"{genre_name}について占ってください。"

            reading = ai_reading(genre_name, question, cards3)

            msg = (
                f"🔮3枚引き\n"
                f"①現状：{cards3[0]}\n"
                f"②注意：{cards3[1]}\n"
                f"③行動：{cards3[2]}\n\n"
                f"{reading}\n\n"
                f"（残り{remaining_after}回｜連続{streak}日）"
            )
            reply(reply_token, msg)
            continue

        # ③ それ以外はガイド（入力が迷子にならないように）
        reply(
            reply_token,
            "「10円占い」と送るとメニューが出ます。\n"
            "その後、1〜5の番号で選んでください。"
        )

    return {"ok": True}
