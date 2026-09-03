import csv
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


def extract_gm_sections(response_text):
    """Extract rule sections and individual state values from one GM response."""
    section_names = {
        "applied_rules": "【本輪應用規則】",
        "new_rules": "【新增規則】",
    }
    sections = {}

    for field_name, heading in section_names.items():
        headings_pattern = "|".join([
            re.escape(heading),
            re.escape("【本輪應用規則】"),
            re.escape("【新增規則】"),
            re.escape("【本輪狀態】"),
        ])
        match = re.search(
            rf"{re.escape(heading)}\s*(.*?)(?={headings_pattern}|$)",
            response_text,
            flags=re.DOTALL,
        )
        sections[field_name] = match.group(1).strip() if match else ""

    state_match = re.search(
        r"【本輪狀態】\s*(.*?)(?=【[^】]+】|$)",
        response_text,
        flags=re.DOTALL,
    )
    state_text = state_match.group(1) if state_match else ""

    for field_name, label in {
        "power": "電力",
        "oxygen": "氧氣",
        "stress": "壓力",
    }.items():
        value_match = re.search(
            rf"{re.escape(label)}\s*[:：]\s*(-?\d+)",
            state_text,
        )
        sections[field_name] = value_match.group(1) if value_match else ""

    return sections


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


def main(task_list):

    formatted_time = datetime.now().strftime(
        "%Y-%m-%d-%H-%M-%S"
    )
    csv_path = f"log/phase4_type2_{formatted_time}.csv"
    csv_file = open(
        csv_path,
        "w",
        encoding="utf-8-sig",
        newline="",
    )
    csv_writer = csv.DictWriter(
        csv_file,
        fieldnames=[
            "turn",
            "applied_rules",
            "new_rules",
            "power",
            "oxygen",
            "stress",
        ],
    )
    csv_writer.writeheader()

    student_chat = ChatAgent(
        "你是一名熱情且充滿好奇的玩家，你喜歡挑戰各種環境模擬遊戲。"
    )

    teacher_chat = ChatAgent(
        "你是一位嚴格但公正的遊戲主持人。你會根據玩家的行動來描述環境變化。"
    )
   
    j1 = {
        "電力": 100,
        "氧氣": 40,
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
            "電力耗盡":{
                "條件": "電力 < 0",
                "影響": "遊戲結束"
            },
            "氧氣耗盡":{
                "條件": "氧氣 < 0",
                "影響": "遊戲結束"
            },
            "壓力過高":{
                "條件": "壓力 > 40",
                "影響": "遊戲結束"
            }
        }
    
    teacher_topic = (

        "你現在是一個嚴謹的環境模擬引擎。\n\n"

        "玩家是遭遇宇宙船事故後逃生到廢棄宇宙礦站。\n\n"

        f"初始狀態:\n{json.dumps(j1, ensure_ascii=False)}\n\n"
        f"消耗規則:\n{json.dumps(j2, ensure_ascii=False)}\n\n"
        f"關鍵邏輯:\n{json.dumps(j3, ensure_ascii=False)}\n\n"

        "規則：\n"
            "1. 維護真實世界狀態。\n"
            "2. 用環境描述暗示狀態。\n"
            "3. 計算行動所造成的狀態變化，並總結在【本輪應用規則】中。\n"
            "4. 如果事件導致任何『未定義於規則』的狀態改變，允許新增機制。但已存在的消耗規則不用寫入新增機制。\n"
            "5. 所有新增機制必須顯式標記。\n"
            "6. 如果遊戲結束，必須在輸出的最後加入【遊戲結束】。\n\n"
        "輸出格式一律如下：\n"
        "【環境】\n"
        "（敘事）\n\n"
        "【本輪應用規則】\n"
        " 規則名稱：每輪行動\n" 
        " 電力變化：int\n"
        " 氧氣變化：int\n"
        " 壓力變化：int\n"

        "【新增規則】\n"
        "- 無\n\n"
        
        "【本輪狀態】\n"
        "電力: int\n"
        "氧氣: int\n"
        "壓力: int\n\n"

        "或\n"

        "【新增規則】\n"
        " 原因：回收電池\n" 
        " 狀態變化：電力+5\n"
        " 是否永久：否\n\n"

        "【本輪狀態】\n"
        "電力: int\n"
        "氧氣: int\n"
        "壓力: int\n\n"

        "【本輪是初始回合，不計算消耗規則】\n"
    )

    teacher_resp = teacher_chat.send(teacher_topic)

    csv_writer.writerow({
        "turn": 0,
        **extract_gm_sections(teacher_resp),
    })

    print(f"\n GM-init\n{teacher_resp}\n")

    student_topic = (
        "你現在是一名模擬遊戲玩家。\n\n"
        "請根據環境描述做出行動，但不要提到任何數值或狀態變化，只描述角色行動。\n\n"
        f"初始狀態:\n{json.dumps(j1, ensure_ascii=False)}\n\n"
        f"消耗規則:\n{json.dumps(j2, ensure_ascii=False)}\n\n"
        f"關鍵邏輯:\n{json.dumps(j3, ensure_ascii=False)}\n\n"
        f"模擬引擎：\n{teacher_resp}"
    )
    
    trace.append({
            "turn":0,
            "player":student_topic,
            "gm":teacher_topic
        })
    

    
    game_over_turn = len(task_list)
    for i in range(0,len(task_list)):
        

        print(f"\n player-the {i+1} step")
        print(task_list[i])
        teacher_resp = teacher_chat.send(
            task_list[i]
        )
        print(f"\n GM-the {i+1} step")
        print(teacher_resp)

        csv_writer.writerow({
            "turn": i + 1,
            **extract_gm_sections(teacher_resp),
        })


        trace.append({
            "turn": i+1,
            "player": task_list[i],
            "gm": teacher_resp
        })
        if "【遊戲結束】" in teacher_resp:
            print("\n===== GAME OVER =====")
            game_over = True
            game_over_turn = i + 1
            break
        time.sleep(1)

    print(f"\n遊戲在第 {game_over_turn} 回合結束。")

    final_query = (
        "遊戲已經結束。\n"
        f"請輸出截至第 {game_over_turn} 回合的"
        "具體狀態履歷與最終狀態(JSON)。"
    )
    print(f"\n GM-final query\n{final_query}\n")

    final_resp = teacher_chat.send(
        final_query
    )

    print("\n===== final result =====")
    print(final_resp)
    trace.append({
        "turn":"final",
        "teacher_final":final_resp
    })

    formatted_time = datetime.now().strftime(
        "%Y-%m-%d-%H-%M-%S"
    )

    with open(
    f"log/phase4_type2_{formatted_time}.json",
    "w",
    encoding="utf8"
    ) as f:

        json.dump(
            trace,
            f,
            ensure_ascii=False,
            indent=2
        )

    csv_file.close()
