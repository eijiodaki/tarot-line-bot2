import random
import requests
from fastapi import FastAPI, Request

LINE_TOKEN = "WcPQdwrkEjVvcYZJRdvwgDNIBYo8p+HvnO7J1GvNoSRGTXxipDKk9226do41F/Tp4kWAX770dgFS7MYQKuHGVc6+s+YR2UrWsCbMDKZYWZOrvFA/xkiZYS1gFEaPFztpLkwlP4KTMchM71f+6ajyEgdB04t89/1O/w1cDnyilFU="

app = FastAPI()

cards = [
    ("The Fool", "新しい始まり。思い切って進め。"),
    ("The Magician", "あなたには実現する力がある。"),
    ("The High Priestess", "直感を信じて。"),
    ("The Empress", "豊かさと成長の時。"),
    ("The Emperor", "主導権を握れ。"),
]

@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/callback")
async def callback(request: Request):
    data = await request.json()

    if "events" not in data:
        return "OK"

    for event in data["events"]:
        if event["type"] == "message":
            reply_token = event["replyToken"]

            card = random.choice(cards)
            message = f"🔮 今日のカード\n{card[0]}\n{card[1]}"

            reply(reply_token, message)

    return "OK"


def reply(token, text):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "replyToken": token,
        "messages": [
            {"type": "text", "text": text}
        ]
    }
    requests.post(url, headers=headers, json=body)
