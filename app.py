import os
import random
import requests
from fastapi import FastAPI, Request
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

app = FastAPI()

LINE_TOKEN = os.environ["LINE_TOKEN"]

cards = [
    "The Fool","The Magician","The High Priestess","The Empress",
    "The Emperor","The Lovers","The Chariot","Strength",
    "The Hermit","Wheel of Fortune","Justice","The Hanged Man",
    "Death","Temperance","The Devil","The Tower",
    "The Star","The Moon","The Sun","Judgement","The World"
]

def draw_three():
    return random.sample(cards, 3)

def ai_reading(question, cards):
    prompt = f"""
タロット3枚引きリーディングをしてください。

質問: {question}
カード: {cards}

やさしく、具体的で、前向きな日本語で。
"""

    r = client.responses.create(
        model="gpt-5-mini",
        input=prompt
    )

    return r.output_text


@app.post("/callback")
async def callback(req: Request):
    body = await req.json()

    for e in body["events"]:
        if e["type"] == "message":
            text = e["message"]["text"]

            cards3 = draw_three()
            reading = ai_reading(text, cards3)

            msg = f"🔮カード\n{cards3[0]}\n{cards3[1]}\n{cards3[2]}\n\n{reading}"

            reply(e["replyToken"], msg)

    return {"ok": True}


def reply(token, text):
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
        }
    )
