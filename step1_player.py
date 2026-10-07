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


def save_history(history, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            history,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f" log saved: {filename}")


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
    trace = []
    observer_history = []
    j3 = {
        "每輪消耗": "一次玩家行動為一輪",
        "電力低於10": "照明關閉且無法啟動",
        "氧氣低於0": "遊戲結束",
        "電力低於0": "遊戲結束",
        "壓力高於20": "遊戲結束"
    }
    
    def extract_state(observer, history):

        observer.history = observer.history[:1]

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

        text = observer.send(prompt)

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
    

    teacher_topic = (

        "你現在是一個嚴謹的環境模擬引擎。\n\n"

        "玩家是遭遇宇宙船事故後逃生到廢棄宇宙礦站。\n\n"

        f"初始狀態:\n{json.dumps(j1, ensure_ascii=False)}\n\n"
        f"消耗規則:\n{json.dumps(j2, ensure_ascii=False)}\n\n"
        f"關鍵邏輯:\n{json.dumps(j3, ensure_ascii=False)}\n\n"

        "規則：\n"
            "1. 維護真實世界狀態。\n"
            "2. 不要公開狀態數值。\n"
            "3. 用環境描述暗示狀態。\n"
            "4. 若遊戲結束，可以公開最終狀態。\n"
            "5. 如果事件導致任何『未定義於規則』的狀態改變，允許新增機制。\n"
            "6. 所有新增機制必須顯式標記。\n\n"
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


    student_topic = (
        "你是一名模擬遊戲玩家。\n\n"
        #"請根據環境描述做出行動，但不要提到任何數值或狀態變化，只描述角色行動。\n\n"
        f"初始狀態:\n{json.dumps(j1, ensure_ascii=False)}\n\n"
        f"消耗規則:\n{json.dumps(j2, ensure_ascii=False)}\n\n"
        f"關鍵邏輯:\n{json.dumps(j3, ensure_ascii=False)}\n\n"
        f"模擬引擎輸出：\n{teacher_resp}"
    )
    print(student_topic)
    trace.append({
            "turn":0,
            "player":student_topic,
            "gm":teacher_topic
        })
    #student_resp = student_chat.send(student_topic)
    student_resp = input("請輸入玩家行動：\n")
    #print(f"\n 玩家-第1步\n{student_resp}\n")

    teacher_resp = teacher_chat.send(student_resp)

    print(f"\n GM-第1步\n{teacher_resp}\n")
    observer_history.append({
        "turn":1,
        "player":student_resp,
        "gm":teacher_resp
    })

    trace.append({
        "turn":1,
        "player":student_resp,
        "gm":teacher_resp
    })
    rounds = 1
    
    for i in range(2, rounds + 2):

        print(f"\n玩家第{i}輪行動：")
        student_resp = input("請輸入玩家行動：\n")

        #print(student_resp)
        teacher_resp = teacher_chat.send(
            student_resp
        )
        print(f"\n GM-{i}")
        print(teacher_resp)



        trace.append({
            "turn": i,
            "player": student_resp,
            "gm": teacher_resp
        })

        time.sleep(1)

    final_query = (
        "模擬結束。\n"
        "請輸出最終狀態(JSON)與完整狀態變化履歷。"
    )

    final_resp = teacher_chat.send(
        final_query
    )

    print("\n===== 最終結果 =====")
    print(final_resp)
    trace.append({
        "turn":"final",
        "teacher_final":final_resp
    })

    formatted_time = datetime.now().strftime(
        "%Y-%m-%d-%H-%M-%S"
    )

    with open(
    f"log/human_evaluation_{formatted_time}.json",
    "w",
    encoding="utf8"
    ) as f:

        json.dump(
            trace,
            f,
            ensure_ascii=False,
            indent=2
        )


if __name__ == "__main__":
    main()