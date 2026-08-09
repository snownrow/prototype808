import json
import time
from datetime import datetime
from openai import OpenAI

import re
import os
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

MODEL = "gpt-4o-mini"
class ChatAgent:
    def __init__(self, system_prompt):
        self.history = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

    def send(self, message):
        self.history.append({
            "role": "user",
            "content": message
        })

        resp = client.responses.create(
            model=MODEL,
            input=self.history
        )

        text = resp.output_text

        self.history.append({
            "role": "assistant",
            "content": text
        })

        return text
observer_chat = ChatAgent(
        """
        你是一個遊戲觀察器。

        任務：
        玩家發言一次代表一輪行動，每輪行動的消耗必須根據規則計算。你必須嚴格根據消耗規則計算電力、氧氣和壓力，。

        輸出格式必須為：

        {
        "電力": int,
        "氧氣": int,
        "壓力": int,
        "理由": "一句話"
        }

        禁止輸出其他文字。
        """
    )
j1 = {
    "電力": 40,
    "氧氣": 20,
    "壓力": 0
}

j2 = {
    "電力": {
        "每輪行動": 2,
        "區域照明": 1,
        "電漿焊槍": 10,
        "發送求救信號": 5
    },
    "氧氣": {
        "每輪行動": 1,
        "搜索": 2
    },
    "壓力": {
        "每輪行動": 1,
        "黑暗區域": 2
    },
}
j3 = {
    "每輪消耗": "一次玩家行動為一輪",
    "電力低於10": "照明關閉且無法啟動",
    "氧氣低於0": "遊戲結束",
    "電力低於0": "遊戲結束",
    "壓力高於20": "遊戲結束"
}
def extract_state(history):
    print(f"觀察者訊息:\n{history}\n")
    observer_chat.history = observer_chat.history[:1]

    prompt = f"""
    根據以下遊戲紀錄推測目前狀態。

    規則：
        f"初始狀態:\n{json.dumps(j1)}"
        f"消耗規則:\n{json.dumps(j2)}"
        f"關鍵邏輯:\n{json.dumps(j3)}"

    紀錄：
    {history}

    只輸出JSON。
    """

    text = observer_chat.send(prompt)
    print(f"🕵️‍♂️ 觀察者回覆:\n{text}\n")
    try:

        m = re.search(
            r"\{[\s\S]*?\}",
            text
        )

        if not m:
            return {
                "error": "parse_fail",
                "raw": text
            }

        return json.loads(
            m.group()
        )

    except Exception as e:

        return {
            "error": str(e),
            "raw": text
        }