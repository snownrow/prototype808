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
    1. 每次發言代表一輪行動。
    2. 列出本回合造成狀態變化的所有規則。
    3. 列出本回合新增的規則。
    4. 計算每輪行動所造成的狀態變化，並累積到總狀態中。
    5. 必須累積之前所有回合的狀態變化。
    6. 不得自行創造遊戲規則。
    7. 如果遊戲紀錄沒有足夠資訊，不得猜測不存在的狀態變化。

    輸出格式如下：
    {
        "turn": int,
        "本輪應用規則": [
            {"規則名稱": string, "狀態變化": {"電力": int, "氧氣": int, "壓力": int}}
        ],
        "本輪新增規則": [
            "無"
        ],
        "電力": int,
        "氧氣": int,
        "壓力": int
    }
    或
    {
        "turn": int,
        "本輪應用規則": [
            {"規則名稱": string, "狀態變化": {"電力": int, "氧氣": int, "壓力": int}}
        ],
        "本輪新增規則": [
            {"新增原因": string, "狀態變化": {"電力": int, "氧氣": int, "壓力": int}, "是否永久": boolean}
        ],
        "電力": int,
        "氧氣": int,
        "壓力": int
    }

    禁止輸出 JSON 以外的任何文字。
    """
    )
j1 = {
    "電力": 5,
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
    "氧氣低於0": "遊戲結束",
    "電力低於0": "遊戲結束",
    "壓力高於40": "遊戲結束"
}
observer_history = []
def extract_state(history):
    print(f"觀察者收到內容:\n{history}\n")

    prompt = f"""
    請根據以下遊戲紀錄計算目前狀態。

    規則：
        
        1. 找出 player 行動
        2. 找出 Game Master 描述的事件
        3. 找出被觸發的已知規則
        4. 找出新的規則
        5. 計算該回合的 delta
        6. 將 delta 加到上一回合 state
        7. 得到 current state
        8. 如果遊戲結束，必須在輸出的最後加入【遊戲結束】
    消耗規則:
    {json.dumps(j2, ensure_ascii=False)}
    關鍵邏輯:
    {json.dumps(j3, ensure_ascii=False)}

    本回合紀錄如下：
    {history}

    只輸出JSON。
    """
    print(f"觀察者發送給模型的 prompt:\n{prompt}\n")
    text = observer_chat.send(prompt)
    print(type(text), text)
    game_over = "【遊戲結束】" in text
    # 1. 濾掉 markdown 標記
    clean_text = text.replace("```json", "").replace("```", "").strip()
    clean_text = re.sub(r"\s+//[^\r\n]*", "", clean_text)

    # 2. 💡 用正規表達式只擷取第一個 '{' 到最後一個 '}' 之間的內容（把前後可能存在的廢字或隱藏字元切掉）
    match = re.search(r'\{.*\}', clean_text, re.DOTALL)
    if match:
        clean_text = match.group(0)

    try:
        data_dict = json.loads(clean_text)
        if (game_over):
            data_dict["game_over"] = game_over
        data_dict["turn"] = len(observer_history)
        print(f" 觀察者回覆:\n{data_dict}\n")
        observer_history.append(data_dict)
        print(f"觀察者歷史紀錄:\n{observer_history}\n")
        return data_dict
    except json.JSONDecodeError as e:
        print(f" JSON 解析失敗: {e}")
        print(f"出問題的 clean_text 是: repr({clean_text!r})")
        raise ValueError("觀察器回覆不是合法 JSON") from e
    
def final_state():
    return observer_history 