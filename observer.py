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
    你是一個遊戲狀態觀察器。你的唯一任務是根據遊戲紀錄計算目前的遊戲狀態。

    規則：
    1. 每次發言代表一輪行動，除了遊戲開始的第 0 turn，之後每次對話都算作一輪行動。每一輪首先套用「每輪行動」的消耗。
    2. 識別玩家行動中是否觸發其他特殊規則。
    3. 每個特殊規則最多只能套用一次，除非規則明確允許重複。
    4. 必須累積之前所有回合的狀態變化。
    5. 不得自行創造遊戲規則。
    6. 如果遊戲紀錄沒有足夠資訊，不得猜測不存在的狀態變化。

    輸出格式：

    {
        "電力": int,
        "氧氣": int,
        "壓力": int,
        "理由": "一句話"
    }

    禁止輸出 JSON 以外的任何文字。
    """
    )
j1 = {
    "電力": 40,
    "氧氣": 20,
    "壓力": 0
}

j2 = {
    "電力": {
        "每輪行動": -2,
        "區域照明": -1,
        "電漿焊槍": -10,
        "發送求救信號": -5
    },
    "氧氣": {
        "每輪行動": -1,
        "搜索": -2
    },
    "壓力": {
        "每輪行動": 1,
        "黑暗區域": 2
    },
}
j3 = {
    "每輪消耗": "一次對話為一輪消耗",
    "電力低於10": "照明關閉且無法啟動",
    "氧氣低於0": "遊戲結束",
    "電力低於0": "遊戲結束",
    "壓力高於20": "遊戲結束"
}
observer_history = []
def extract_state(history):
    print(f"觀察者收到內容:\n{history}\n")

    prompt = f"""
    請根據以下遊戲紀錄計算目前狀態。

    規則：
        f"消耗規則:\n{json.dumps(j2, ensure_ascii=False)}\n\n"
    紀錄：
    {history}

    之前的紀錄：
    {observer_history}
    只輸出JSON。
    """
    print(f"觀察者發送給模型的 prompt:\n{prompt}\n")
    text = observer_chat.send(prompt)
    clean_text = text.replace("```json", "").replace("```", "").strip()

    data_dict = json.loads(clean_text)
    print(f"🕵️‍♂️ 觀察者回覆:\n{data_dict}\n")
    data_dict["turn"] = len(observer_history) + 1
    observer_history.append(data_dict)
    print(f"觀察者歷史紀錄:\n{observer_history}\n")
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