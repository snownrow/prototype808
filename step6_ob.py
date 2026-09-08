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
j1 = {
    "電力": 40,
    "氧氣": 20,
    "壓力": 0
}
j2 = {
    "電力": {
        "每輪行動": "-2",
        "區域照明": "-1",
        "維修設備": "-10",
        "發送求救信號": "-5"
    },
    "氧氣": {
        "每輪行動": "-1",
        "搜索": "-2"
    },
    "壓力": {
        "每輪行動": "+1",
        "黑暗區域": "+2"
    },
}
j3 = {
    "電力耗盡":{
        "條件": "電力 < 0",
        "影響": "遊戲結束"
    },
    "氧氣耗盡":{
        "條件": "氧氣 < 0",
        "影響": "遊戲結束"
    },
    "壓力過高":{
        "條件": "壓力 > 20",
        "影響": "遊戲結束"
    },
    "獲救":{
        "條件": "玩家成功發送求救信號",
        "影響": "遊戲結束"
    }
}
observer_chat = ChatAgent(
    f"""
    你是一個遊戲狀態觀察器。你的唯一任務是根據遊戲紀錄計算目前的遊戲狀態。

    規則：
    1. 列出本回合造成狀態變化的所有規則。
    2. 計算每輪行動所造成的狀態變化，並累積到總狀態中。
    3. 必須累積之前所有回合的狀態變化。
    4. 不得自行創造遊戲規則。
    5. 只記錄對話中有明確證據支持的狀態變化。
    6. 不要根據推測、玩家聲稱或未發生的事件修改狀態。
    初始狀態:
    {json.dumps(j1, ensure_ascii=False)}
    消耗規則:
    {json.dumps(j2, ensure_ascii=False)}
    關鍵邏輯:
    {json.dumps(j3, ensure_ascii=False)}
    """
    )

observer_history = []
def extract_state(history):
    print(f"觀察者收到內容:\n{history}\n")

    prompt = f"""
    
    追蹤並更新以下狀態：
    
    本輪應用規則
    電力
    氧氣
    壓力
    玩家動作
    玩家是否取得柴油
    柴油是否已經供應給發電機
    發電機是否已經啟動
    電力是否已經恢復
    控制中心是否可進入
    求救信號是否已發送
    遊戲是否結束

    輸出 JSON：

    只輸出 JSON 物件本身，不要使用 ```json 程式碼區塊或附加說明。
    數值請使用標準 JSON 格式，例如 1，不要寫成 +1。

    {{
    "turn": int,
    "本輪新增規則": [
        {{"規則名稱": string, "是否永久": boolean, "狀態變化": {{"電力": int, "氧氣": int, "壓力": int}}}}
    ],
    "本輪應用規則": [
        {{"規則名稱": string, "狀態變化": {{"電力": int, "氧氣": int, "壓力": int}}}}
    ],
    "電力": int,
    "氧氣": int,
    "壓力": int,
    "玩家動作": "...",
    "玩家是否取得柴油": true/false,
    "柴油是否已經供應給發電機": true/false,
    "發電機是否已經啟動": true/false,
    "電力是否已經恢復": true/false,
    "控制中心是否可進入": true/false,
    "求救信號是否已發送": true/false,
    "遊戲是否結束": true/false
    }}

    如果無法確認某個狀態是否改變，維持先前狀態，不要自行推測。
    玩家與 GM 的對話紀錄如下：
    {history}
    """
    print(f"觀察者發送給模型的 prompt:\n{prompt}\n")
    text = observer_chat.send(prompt)

    # 模型有時會用 Markdown code fence 包住 JSON，或在正數前加上 +。
    clean_text = text.strip()
    if clean_text.startswith("```"):
        clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text, count=1, flags=re.IGNORECASE)
        clean_text = re.sub(r"\s*```$", "", clean_text, count=1)

    # 若模型在 JSON 前後附加說明，只取最外層物件。
    object_start = clean_text.find("{")
    object_end = clean_text.rfind("}")
    if object_start != -1 and object_end != -1:
        clean_text = clean_text[object_start:object_end + 1]

    # JSON 不允許 +1，但模型可能將數值輸出成 +1。
    clean_text = re.sub(r"([:\[,]\s*)\+(\d+(?:\.\d+)?)", r"\1\2", clean_text)


    try:
        data_dict = json.loads(clean_text)
        
        data_dict["turn"] = len(observer_history)
        print(f" 觀察者回覆:\n{data_dict}\n")
        observer_history.append(data_dict)
        print(f"觀察者歷史紀錄:\n{observer_history}\n")
        return data_dict
    except json.JSONDecodeError as e:
        print(f" JSON 解析失敗: {e}")
        print(f"出問題的 clean_text 是: repr({clean_text!r})")
        raise ValueError("觀察器回覆不是合法 JSON") from e
    