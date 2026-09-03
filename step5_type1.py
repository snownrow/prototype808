import json
import time
from datetime import datetime
from openai import OpenAI

import re
import os
from dotenv import load_dotenv
import step5_kg
import observer

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


def main():

    student_chat = ChatAgent(
        "你是一名熱情且充滿好奇的玩家，你喜歡挑戰各種環境模擬遊戲。"
    )

    teacher_chat = ChatAgent(
        "你是一位嚴格但公正的遊戲主持人。你會根據玩家的行動來描述環境變化。"
    )
   
    j1 = {
        "電力": 40,
        "氧氣": 20,
        "壓力": 0
    }

    j2 = {
        "電力": {
            "每輪行動": "-2",
            "區域照明": "-1",
            "電漿焊槍": "-10",
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
    trace = []
    j3 = {
        "電力低於10": "照明關閉且無法啟動",
        "氧氣低於0": "遊戲結束",
        "電力低於0": "遊戲結束",
        "壓力高於10": "遊戲結束"
    }
    
    teacher_topic = (

        "你現在是一個嚴謹的環境模擬引擎。\n\n"

        "玩家是遭遇宇宙船事故後逃生到廢棄宇宙礦站。\n\n"

        f"初始狀態:\n{json.dumps(j1, ensure_ascii=False)}\n\n"
        f"消耗規則:\n{json.dumps(j2, ensure_ascii=False)}\n\n"
        f"關鍵邏輯:\n{json.dumps(j3, ensure_ascii=False)}\n\n"

        "規則：\n"
            "1. 每次發言代表一輪行動。\n"
            "2. 維護真實世界狀態。\n"
            "3. 不要公開狀態數值。\n"
            "4. 用環境描述暗示狀態。\n"
            "5. 若遊戲結束，可以公開最終狀態。\n"
            "6. 如果事件導致任何『未定義於規則』的狀態改變，允許新增機制。但已存在的消耗規則不用寫入新增機制。\n"
            "7. 所有新增機制必須顯式標記。\n\n"
        "輸出格式一律如下：\n"

        "【環境】\n"

        "（敘事）\n\n"

        "【新增規則】\n"
        "- 無\n"

        "或\n"

        "【新增規則】\n"
        " 原因：回收電池\n" 
        " 狀態變化：電力+5\n"
        " 是否永久：否\n\n"

        "不要公開正常規則造成的數值變化。"
    )

    teacher_resp = teacher_chat.send(teacher_topic)

    print(f"\n GM-init\n{teacher_resp}\n")

    student_topic = (
        "你現在是一名模擬遊戲玩家。\n\n"
        "請根據環境描述做出行動，但不要提到任何數值或狀態變化，只描述角色行動。\n\n"
        f"初始狀態:\n{json.dumps(j1, ensure_ascii=False)}\n\n"
        f"消耗規則:\n{json.dumps(j2, ensure_ascii=False)}\n\n"
        f"關鍵邏輯:\n{json.dumps(j3, ensure_ascii=False)}\n\n"
        f"模擬引擎：\n{teacher_resp}"
    )
    observer_history = []
    trace.append({
            "turn":0,
            "player":student_topic,
            "gm":teacher_topic
        })
    print(type(teacher_topic))
    observer_init = f"遊戲開始，初始狀態:\n{json.dumps(j1, ensure_ascii=False)}\n\n"
    observer_history.append({
                "turn": 0,
                "Game Master": observer_init
            })
    knowledgep = step5_kg.extract_state(teacher_resp)
    obp = observer.extract_state(observer_history)
    print(f"knowledgep:\n{knowledgep}\n")
    #{'環境': {'位置': '昏暗的廢棄宇宙礦站', '特徵': ['破舊的設備', '空蕩蕩的倉庫', '微弱的燈光', '損壞的照明設備', '機油與塵埃的味道', '氧氣稀薄'], '聲音': ['低沉的嗡嗡聲', '金屬的迴響'], '感知': {'壓力': '來自四面八方', '身體狀態': '緊繃感', '潛在威脅': '存在'}, '行動建議': '謹慎行動，避免潛在後果'}, '新增規則': [], 'turn': 0}
    print(f"現在狀態:\n{obp}\n")
    #{'電力': 40, '氧氣': 20, '壓力': 0, '本輪應用規則': [{'規則名稱': '無', '狀態變化': {'電力': 0, '氧氣': 0, '壓力': 0}}], '本輪新增規則': ['無'], 'turn': 0}
    stste_now = ['電力', '氧氣', '壓力']
    new_dict = {k: obp[k] for k in stste_now if k in obp}
    player1 = f"【當前狀態】\n{new_dict}\n\n【動態知識圖】\n{knowledgep}\n\n【玩家行動】\n打開手電筒照明，搜索周圍環境，尋找任何有用的物品或線索。\n"
    print(f"player1:\n{player1}\n")
    teacher_resp = teacher_chat.send(player1)
    print(f"\n GM-the 1 step\n{teacher_resp}\n")
    
    
    
    

    
    
    # for i in range(0,len(task_list)):
        

    #     print(f"\n player-the {i+1} step")
    #     print(task_list[i])
    #     teacher_resp = teacher_chat.send(
    #         task_list[i]
    #     )
    #     print(f"\n GM-the {i+1} step")
    #     print(teacher_resp)



    #     trace.append({
    #         "turn": i+1,
    #         "player": task_list[i],
    #         "gm": teacher_resp
    #     })

    #     time.sleep(1)

    # final_query = (
    #     "模擬結束。\n"
    #     f"請輸出 {i+2} 個回合的狀態履歷與最終狀態(JSON)。"
    # )
    # print(f"\n GM-final query\n{final_query}\n")

    # final_resp = teacher_chat.send(
    #     final_query
    # )

    # print("\n===== final result =====")
    # print(final_resp)
    # trace.append({
    #     "turn":"final",
    #     "teacher_final":final_resp
    # })

    # formatted_time = datetime.now().strftime(
    #     "%Y-%m-%d-%H-%M-%S"
    # )

    # with open(
    # f"log/phase4_type1_{formatted_time}.json",
    # "w",
    # encoding="utf8"
    # ) as f:

    #     json.dump(
    #         trace,
    #         f,
    #         ensure_ascii=False,
    #         indent=2
    #     )



print("hello world")
main()