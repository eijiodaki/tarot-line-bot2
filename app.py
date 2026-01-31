import random
import requests
from fastapi import FastAPI, Request

# ==============================
# LINE Channel Access Token を貼る
# 文字列は必ず " " で囲み、改行しない
# ==============================
LINE_TOKEN = "WcPQdwrkEjVvcYZJRdvwgDNIBYo8p+HvnO7J1GvNoSRGTXxipDKk9226do41F/Tp4kWAX770dgFS7MYQKuHGVc6+s+YR2UrWsCbMDKZYWZOrvFA/xkiZYS1gFEaPFztpLkwlP4KTMchM71f+6ajyEgdB04t89/1O/w1cDnyilFU="

app = FastAPI()

# ==============================
# タロットカードデータ
# 78枚フル＋正位置・逆位置
# 簡単な解釈付き
# ==============================
cards = [
    # メジャーアルカナ（22枚）
    ("The Fool", "新しい始まり。思い切って進め。"),
    ("The Magician", "あなたには実現する力がある。"),
    ("The High Priestess", "直感を信じて。"),
    ("The Empress", "豊かさと成長の時。"),
    ("The Emperor", "主導権を握れ。"),
    ("The Hierophant", "伝統や知恵に従え。"),
    ("The Lovers", "大切な選択や恋愛の時。"),
    ("The Chariot", "前進と勝利を示す。"),
    ("Strength", "勇気と忍耐力。"),
    ("The Hermit", "内省と静かな時間。"),
    ("Wheel of Fortune", "運命の変化。"),
    ("Justice", "公平さと正しい判断。"),
    ("The Hanged Man", "視点を変える時。"),
    ("Death", "終わりと新しい始まり。"),
    ("Temperance", "バランスと調和。"),
    ("The Devil", "執着や誘惑に注意。"),
    ("The Tower", "突然の変化。"),
    ("The Star", "希望と癒し。"),
    ("The Moon", "不確実さと直感。"),
    ("The Sun", "喜びと成功。"),
    ("Judgement", "再生と決断の時。"),
    ("The World", "完成と達成。"),
    # 小アルカナ（56枚簡易版）
    ("Ace of Cups", "新しい感情や愛の始まり。"),
    ("Two of Cups", "関係の調和やパートナーシップ。"),
    ("Three of Cups", "友情や祝福。"),
    ("Four of Cups", "停滞感や見直し。"),
    ("Five of Cups", "失望、過去への執着。"),
    ("Six of Cups", "懐かしい思い出。"),
    ("Seven of Cups", "選択の迷い。"),
    ("Eight of Cups", "離れる決断。"),
    ("Nine of Cups", "願望成就。"),
    ("Ten of Cups", "幸福な家庭。"),
    ("Page of Cups", "感情の芽生え。"),
    ("Knight of Cups", "ロマンチックな行動。"),
    ("Queen of Cups", "感情を大切にする。"),
    ("King of Cups", "優しさと寛容。"),
    ("Ace of Wands", "新しい挑戦や創造力。"),
    ("Two of Wands", "計画と意思決定。"),
    ("Three of Wands", "展望と成長。"),
    ("Four of Wands", "お祝いと安定。"),
    ("Five of Wands", "競争や葛藤。"),
    ("Six of Wands", "勝利と評価。"),
    ("Seven of Wands", "防衛と挑戦。"),
    ("Eight of Wands", "進展や速い変化。"),
    ("Nine of Wands", "忍耐と警戒。"),
    ("Ten of Wands", "責任の重さ。"),
    ("Page of Wands", "新しい冒険。"),
    ("Knight of Wands", "行動力と情熱。"),
    ("Queen of Wands", "自信とリーダーシップ。"),
    ("King of Wands", "決断力と指導力。"),
    ("Ace of Swords", "新しい知識や発想。"),
    ("Two of Swords", "決断の迷い。"),
    ("Three of Swords", "悲しみや別れ。"),
    ("Four of Swords", "休息と回復。"),
    ("Five of Swords", "争いと葛藤。"),
    ("Six of Swords", "移動と解決。"),
    ("Seven of Swords", "策略や秘密。"),
    ("Eight of Swords", "制約や不安。"),
    ("Nine of Swords", "心配や不安。"),
    ("Ten of Swords", "終わりや絶望。"),
    ("Page of Swords", "好奇心と観察。"),
    ("Knight of Swords", "行動と決断。"),
    ("Queen of Swords", "知性と判断。"),
    ("King of Swords", "論理と指導力。"),
    ("Ace of Pentacles", "新しいチャンスや財運。"),
    ("Two of Pentacles", "バランスと調整。"),
    ("Three of Pentacles", "協力と評価。"),
    ("Four of Pentacles", "保守的・蓄財。"),
    ("Five of Pentacles", "不安や損失。"),
    ("Six of Pentacles", "援助や分配。"),
    ("Seven of Pentacles", "努力の結果を待つ。"),
    ("Eight of Pentacles", "学びと成長。"),
    ("Nine of Pentacles", "成功と独立。"),
    ("Ten of Pentacles", "安定と繁栄。"),
    ("Page of Pentacles", "学びの芽生え。"),
    ("Knight of Pentacles", "努力と継続。"),
    ("Queen of Pentacles", "家庭と安定。"),
    ("King of Pentacles", "財運と成功。"),
]

# ==================================
# ブラウザで確認用
# ==================================
@app.get("/")
def root():
    return {"status": "ok"}

# ==================================
# LINE Webhook用
# ==================================
@app.post("/callback")
async def callback(request: Request):
    try:
        data = await request.json()
    except:
        return "ok"

    if "events" not in data:
        return "ok"

    for event in data["events"]:
        if event["type"] == "message":
            reply_token = event["replyToken"]

            # カードをランダムで選ぶ
            card = random.choice(cards)

            # 正位置か逆位置をランダムで判定
            position = random.choice(["正位置", "逆位置"])
            message = f"🔮 今日のカード\n{card[0]} ({position})\n{card[1]}"

            reply(reply_token, message)

    return "ok"

# ==================================
# LINEに返信する関数
# ==================================
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
