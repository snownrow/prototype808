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
            input=self.history,
            temperature=0.2
        )

        text = resp.output_text

        self.history.append({
            "role": "assistant",
            "content": text
        })

        return text
observer_chat = ChatAgent(
    """
    你是一個遊戲狀態觀察器。你的任務是根據遊戲紀錄更新知識圖譜。
    規則：
    1. 保持原有的知識圖結構並進行動態增刪修改。
    2. 輸出格式須維持結構化的條列形式（如 Markdown 列表）。
    3. 精確捕捉環境變化、玩家狀態、物品互動及心理感知。
    """)
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
    "壓力高於10": "遊戲結束"
}
observer_history = []
def extract_state(history):
    print(f"觀察者收到內容:\n{history}\n")

    prompt = f"""
    請根據收到的環境進行知識圖更新。

    紀錄如下：
    {history}

    只輸出JSON。
    """
    print(f"觀察者發送給模型的 prompt:\n{prompt}\n")
    text = observer_chat.send(prompt)
    print(type(text), text)

    # 1. 濾掉 markdown 標記
    clean_text = text.replace("```json", "").replace("```", "").strip()

    # 2. 💡 用正規表達式只擷取第一個 '{' 到最後一個 '}' 之間的內容（把前後可能存在的廢字或隱藏字元切掉）
    match = re.search(r'\{.*\}', clean_text, re.DOTALL)
    if match:
        clean_text = match.group(0)

    try:
        data_dict = json.loads(clean_text)
        print(f" 觀察者回覆:\n{data_dict}\n")
        data_dict["turn"] = len(observer_history)
        observer_history.append(data_dict)
        print(f"觀察者歷史紀錄:\n{observer_history}\n")
        return data_dict
    except json.JSONDecodeError as e:
        print(f" JSON 解析失敗: {e}")
        print(f"出問題的 clean_text 是: repr({clean_text!r})")
    
