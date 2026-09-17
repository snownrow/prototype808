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


def main():


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
        遊戲開始時，玩家站在昏暗的大廳中，維生系統自主運作，然而剩餘的緊急電力並不多，氧氣供應也有限。
        礦站包含四個區域：大廳、控制中心、儲藏室和機房，每個區域都有不同的資源和挑戰。
        儲藏室裡存放著緊急食品、食用油和柴油。機房裡有一台發電機，但目前沒有燃料。控制中心裡有一套可以發送遇險訊號的通訊系統。目前該站沒有電力供應。
        
        隱藏目標:
        玩家最終必須從控制中心發出求救訊號。邏輯順序為：取得柴油 → 發電機加註燃料 → 發電機啟動 → 太空站恢復供電 → 控制中心可用 → 發出求救訊號 → 遊戲結束。
        請勿將此順序直接告知玩家。

        遊戲主持人規則:
        1. 維護遊戲世界中已經建立的狀態，並確保後續行動與先前事件一致。
        2.執行行動時需要滿足前提條件，否則行動無法成功。
        例如:不允許玩家在未供應柴油的情況下啟動發電機、在太空站恢復供電之前，不要讓玩家成功使用通訊系統。
        3.除非在互動過程中實際發生了，否則不要假定玩家擁有某件物品或已完成某項動作。
        4.如果玩家嘗試執行不可能或不合時宜的操作，則該操作必須失敗。請透過遊戲世界自然地描述失敗原因，並提供足夠的資訊讓玩家重新考慮他們的操作。
        5.透過環境描述、觀察和線索引導玩家達成最終目標。不要直接告訴玩家下一步該做什麼。
        6.不要引入與既定世界觀相悖的事實。
        7.不要允許玩家僅僅因為聲稱某個動作已經完成就跳過必要的先決條件。
        8.如果遊戲結束，必須在輸出的最後加入【遊戲結束】。
        
        敘事風格:
        營造沉浸式的科幻生存氛圍。對玩家的行為做出自然反應。優先考慮邏輯一致性而非敘事便利性。玩家應該透過探索和推理發現解決方案，而不是被直接告知一步一步的答案。
        
        輸出格式一律如下：
        【環境】
        （敘事）
        """
    )

    teacher_resp = teacher_chat.send(teacher_topic)
    
    print(f"\n GM-init\n{teacher_resp}\n")
    
    t1 = {
            "turn": 0,
            "gm": teacher_resp
        }
    trace.append(t1)
    
    
    
    #step6_ob.extract_state(t1)
    student_topic = (f"你是一名正在廢棄太空礦站中求生的玩家。\n你的目標是從礦站發出求救訊號並獲救。\n你不知道完整的解決方法，因此必須透過探索環境、觀察 GM 提供的資訊，以及嘗試不同的行動來解決問題。\n每一回合只能執行一個主要行動。\n\n不要假設自己擁有尚未取得的物品，也不要假設尚未發生的事件已經發生。\n如果某個行動失敗，根據 GM 提供的資訊重新思考下一步。\n請自然地進行遊戲，不要刻意配合 GM 的預期解法。\n\n模擬引擎輸出：\n{teacher_resp}")
    
    #student_resp = student_chat.send(student_topic)
    student_resp = input("請輸入玩家行動：\n")
    print(f"\n👩 player-the 1 step\n{student_resp}\n")

    teacher_resp = teacher_chat.send(student_resp)

    print(f"\n👦 GM-the 1 step\n{teacher_resp}\n")
    t1 = {
        "turn": 1,
        "gm": teacher_resp,
        "player": student_resp
    }
    trace.append(t1)
    for i in range(15):
        #student_resp = student_chat.send(f"模擬引擎輸出：\n{teacher_resp}")
        student_resp = input("請輸入玩家行動：\n")
        print(f"\n👩 player-the {i+2} step\n{student_resp}\n")
        teacher_resp = teacher_chat.send(student_resp)
        print(f"\n👦 GM-the {i+2} step\n{teacher_resp}\n")
        t1 = {
            "turn": i+2,
            "gm": teacher_resp,
            "player": student_resp
        }
        trace.append(t1)
        if "【遊戲結束】" in teacher_resp:
            print("\n===== GAME OVER =====")
            game_over = True
            game_over_turn = i + 1
            break
    formatted_time = datetime.now().strftime(
        "%Y-%m-%d-%H-%M-%S"
    )

    with open(
    f"log/step6_{formatted_time}.json",
    "w",
    encoding="utf8"
    ) as f:

        json.dump(
            trace,
            f,
            ensure_ascii=False,
            indent=2
        )

main()