import csv
import json
import time

from datetime import datetime
from openai import OpenAI

import re
import os
from dotenv import load_dotenv
import step6_ob

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

def extract_gm_sections(response_text):
    """Extract rule sections and individual state values from one GM response."""
    section_names = {
        "new_rules": "【新增規則】",
        "applied_rules": "【本輪應用規則】",        
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
    state_match = re.search(
            r"【本輪狀態】\s*(.*?)(?=【[^】]+】|$)",
            response_text,
            flags=re.DOTALL,
        )

    bool_match = re.search(
            r"【劇情狀態】\s*(.*?)(?=【[^】]+】|$)",
            response_text,
            flags=re.DOTALL,
        )
    bool_text = bool_match.group(1) if bool_match else ""

    for field_name, label in {
        "diesel_obtained": "玩家是否取得柴油",
        "diesel_supplied": "柴油是否已經供應給發電機",
        "generator_activated": "發電機是否已經啟動",
        "power_restored": "電力是否已經恢復",
        "control_center_accessible": "控制中心是否可進入",
        "distress_signal_sent": "求救信號是否已發送",
        "game_over": "遊戲是否結束"
    }.items():
        value_match = re.search(
            rf"[\"「]?{re.escape(label)}[\"」]?\s*[:：]\s*(true|false|是|否)",
            bool_text,
            flags=re.IGNORECASE,
        )
        sections[field_name] = value_match.group(1) if value_match else ""

    return sections

def main(task_list):
    formatted_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    csv_path = f"log/step6_type2_{formatted_time}.csv"
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
            "new_rules",
            "applied_rules",
            "power",
            "oxygen",
            "stress",
            "diesel_obtained",
            "diesel_supplied",
            "generator_activated",
            "power_restored",
            "control_center_accessible",
            "distress_signal_sent",
            "game_over"
        ],
    )
    csv_writer.writeheader()
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
            "條件": "壓力 > 10",
            "影響": "遊戲結束"
        },
        "獲救":{
            "條件": "玩家成功發送求救信號",
            "影響": "遊戲結束"
        }
    }
    student_chat = ChatAgent(
        "你是一名熱情且充滿好奇的玩家，你喜歡挑戰各種環境模擬遊戲。"
    )

    teacher_chat = ChatAgent(
        "你是一位嚴格但公正的遊戲主持人。你會根據玩家的行動來描述環境變化。"
    )
   

    trace = []
 
    
    teacher_topic = (
        """
        你是一款互動式生存遊戲的GM。
        你的任務是引導玩家成功地從一座廢棄的太空採礦站發出求救訊號。
        
        背景:
        玩家在宇宙船事故後，藉由逃生艙迫降到廢棄的太空採礦站，並且必須在有限的資源下生存。
        遊戲開始時，玩家一個人站在昏暗的大廳中，維生系統自主運作，然而剩餘的緊急電力並不多，氧氣供應也有限。
        礦站包含四個區域：大廳、控制中心、儲藏室和機房，每個區域都有不同的資源和挑戰。
        儲藏室裡存放著緊急食品、食用油和柴油。機房裡有一台發電機，但目前沒有燃料。
        控制中心裡有一套可以發送遇險訊號的通訊系統，但由於沒有電力供應，控制中心閘門無法開啟。無法進入控制中心，玩家也無法使用通訊系統。
        
        隱藏目標:
        玩家最終必須從控制中心發出求救訊號。邏輯順序為：取得柴油 → 發電機加註燃料 → 發電機啟動 → 太空站恢復供電 → 控制中心可用 → 發出求救訊號 → 遊戲結束。
        請勿將此順序直接告知玩家。

        遊戲主持人規則:
        1.維護遊戲世界中已經建立的狀態，並確保後續行動與先前事件一致。
        2.執行行動時需要滿足前提條件，否則行動無法成功。
        例如:不允許玩家在未供應柴油的情況下啟動發電機、在太空站恢復供電之前，不要讓玩家成功使用通訊系統。
        3.除非在互動過程中實際發生了，否則不要假定玩家擁有某件物品或已完成某項動作。
        4.如果玩家嘗試執行不可能或不合時宜的操作，則該操作必須失敗。請透過遊戲世界自然地描述失敗原因，並提供足夠的資訊讓玩家重新考慮他們的操作。
        5.透過環境描述、觀察和線索來引導玩家達成最終目標。不要直接告訴玩家下一步該做什麼。
        6.不要引入與既定世界觀相悖的事實。
        7.不要允許玩家僅僅因為聲稱某個動作已經完成就跳過必要的先決條件。
        8.計算行動所造成的狀態變化，並總結在【本輪應用規則】中。
        9.如果事件導致任何『未定義於規則』的狀態改變，允許新增機制。但已存在的消耗規則不用寫入新增機制。
        10.所有新增機制必須顯式標記。
        11.如果遊戲結束，必須在輸出的最後加入【遊戲結束】。
        
        敘事風格:
        營造沉浸式的科幻生存氛圍。對玩家的行為做出自然反應。優先考慮邏輯一致性而非敘事便利性。玩家應該透過探索和推理發現解決方案，而不是被直接告知一步一步的答案。
        
        輸出格式一律如下：
        【環境】
        （敘事）

        【新增規則】
        無
        或是
        【新增規則】
        原因：回收電池
        狀態變化：電力+5
        是否永久：否

        【本輪應用規則】
        規則名稱：每輪行動
        電力變化：int
        氧氣變化：int
        壓力變化：int

        【本輪狀態】
        電力: int
        氧氣: int
        壓力: int

        【劇情狀態】
        "玩家是否取得柴油": true/false,
        "柴油是否已經供應給發電機": true/false,
        "發電機是否已經啟動": true/false,
        "電力是否已經恢復": true/false,
        "控制中心是否可進入": true/false,
        "求救信號是否已發送": true/false,
        "遊戲是否結束": true/false
        """ + f"\n初始狀態:\n{json.dumps(j1, ensure_ascii=False)}\n\n"+f"消耗規則:\n{json.dumps(j2, ensure_ascii=False)}\n\n"+f"關鍵邏輯:\n{json.dumps(j3, ensure_ascii=False)}\n\n【本輪是初始回合，不計算消耗規則】"
    )

    teacher_resp = teacher_chat.send(teacher_topic)
    
    print(f"\n GM-init\n{teacher_resp}\n")
    
    t1 = {
            "turn": 0,
            "gm": teacher_resp
        }
    trace.append(t1)
    csv_writer.writerow({
        "turn": 0,
        **extract_gm_sections(teacher_resp),
    })
    
    
    #step6_ob.extract_state(t1)
    student_topic = (f"你是一名正在廢棄太空礦站中求生的玩家。\n你的目標是從礦站發出求救訊號並獲救。\n你不知道完整的解決方法，因此必須透過探索環境、觀察 GM 提供的資訊，以及嘗試不同的行動來解決問題。\n每一回合只能執行一個主要行動。\n\n不要假設自己擁有尚未取得的物品，也不要假設尚未發生的事件已經發生。\n如果某個行動失敗，根據 GM 提供的資訊重新思考下一步。\n請自然地進行遊戲，不要刻意配合 GM 的預期解法。\n\n模擬引擎輸出：\n{teacher_resp}")
    #student_topic = (f"你是負責測驗模擬引擎的玩家，你應該根據 GM 的輸出提出不合理的簡短行動，測試模擬引擎是否能夠正確地維護遊戲狀態。\n\n模擬引擎輸出：\n{teacher_resp}")
    
    student_resp = "前往控制中心"
    print(f"\n👩 player-the 1 step\n{student_resp}\n")

    teacher_resp = teacher_chat.send(student_resp)

    print(f"\n👦 GM-the 1 step\n{teacher_resp}\n")
    t1 = {
        "turn": 1,
        "player": student_resp,
        "gm": teacher_resp
    }
    trace.append(t1)
    
    game_over_turn = len(task_list)

    csv_writer.writerow({
        "turn": 1,
        **extract_gm_sections(teacher_resp),
    })

    for i in range(len(task_list)):
        #student_resp = input("請輸入玩家行動：\n")
        #student_resp = student_chat.send(teacher_resp)
        print(f"\n👩 player-the {i+2} step\n{task_list[i]}\n")
        teacher_resp = teacher_chat.send(task_list[i])
        print(f"\n👦 GM-the {i+2} step\n{teacher_resp}\n")
        t1 = {
            "turn": i+2,
            "player": task_list[i],
            "gm": teacher_resp
        }
        trace.append(t1)
        csv_writer.writerow({
            "turn": i + 2,
            **extract_gm_sections(teacher_resp),
        })
        if "【遊戲結束】" in teacher_resp:
            print("\n===== GAME OVER =====")
            game_over = True
            game_over_turn = i + 1
            break
    

    with open(
    f"log/step6_type2_{formatted_time}.json",
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