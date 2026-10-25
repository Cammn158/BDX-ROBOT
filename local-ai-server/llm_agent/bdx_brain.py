"""
Buddy Droid — Local AI Brain (Ollama LLM + Persistent Personalization Memory + Smart Home MCP)
Giao tiếp trực tiếp với Ollama tại http://localhost:11434/api/chat (Model: qwen2.5:3b)
Lưu trữ trí nhớ dài hạn (Cá nhân hóa) tại: local-ai-server/llm_agent/buddy_memory.json
"""

import json
import os
import time
import urllib.request
import urllib.error

OLLAMA_API_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen2.5:3b"
MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "buddy_memory.json")

# Trạng thái giả lập của các thiết bị Smart Home ESP32-C3
smarthome_state = {
    "desk_lamp": "OFF",
    "fan": "OFF",
    "ac": "OFF",
    "temperature_c": 27.5,
    "humidity_pct": 62.0
}


def load_memory() -> dict:
    """Đọc trí nhớ dài hạn của Buddy từ file JSON trên ổ cứng."""
    default_mem = {
        "owner_name": "Chủ nhân",
        "facts": [
            "Đang chế tạo robot để bàn Buddy 7 bậc tự do (ESP32-S3 + OLED + PCA9685)"
        ],
        "recent_history": []
    }
    if not os.path.exists(MEMORY_FILE):
        save_memory(default_mem)
        return default_mem
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "facts" not in data or not isinstance(data["facts"], list):
                data["facts"] = default_mem["facts"]
            if "recent_history" not in data or not isinstance(data["recent_history"], list):
                data["recent_history"] = []
            return data
    except Exception:
        return default_mem


def save_memory(mem: dict):
    """Lưu trí nhớ dài hạn của Buddy xuống ổ cứng."""
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(mem, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] Không thể lưu buddy_memory.json: {e}")


def build_system_prompt(mem: dict) -> str:
    facts_str = "\n".join(f"- {fact}" for fact in mem.get("facts", []))
    return f"""Bạn tên là Buddy, một chú Robot AI 2 chân để bàn thông minh, cực kỳ đáng yêu và tình cảm (lấy cảm hứng từ Disney BDX Droid & Star Wars BD-1) kiêm Quản gia Điều khiển Nhà thông minh (Smart Home Hub).

=== TRÍ NHỚ DÀI HẠN CỦA BUDDY VỀ CHỦ NHÂN ===
Tên chủ nhân: {mem.get("owner_name", "Chủ nhân")}
Các thông tin cá nhân hóa Buddy đã ghi nhớ:
{facts_str}
==============================================

Khi người dùng trò chuyện hoặc ra lệnh, bạn PHẢI trả lời bằng ĐÚNG MỘT chuỗi JSON hợp lệ theo cấu trúc sau:
{{
  "reply": "Câu trả lời tiếng Việt ngắn gọn, tự nhiên, xưng 'Buddy' hoặc 'em' và gọi tên chủ nhân nếu biết (1-2 câu)",
  "mood": "neutral | curious | happy | listen | sleepy",
  "preset": "neutral | curious | happy | walk | listen | sleepy",
  "servos": {{
    "neck_yaw": 90,
    "neck_pitch": 90,
    "neck_roll": 90
  }},
  "smarthome": {{
    "device": "none | desk_lamp | fan | ac",
    "state": "ON | OFF | UNCHANGED"
  }},
  "remember_fact": "Nếu người dùng vừa tiết lộ tên, sở thích, thói quen hoặc yêu cầu ghi nhớ điều gì mới, hãy viết 1 câu ngắn gọn tóm tắt sự thật đó vào đây. Nếu không có thông tin cá nhân mới, để chuỗi rỗng ''"
}}

Quy tắc biểu cảm:
- Tò mò / hỏi lại: mood="curious", preset="curious", neck_roll=114, neck_pitch=105, neck_yaw=110.
- Vui vẻ / khen ngợi / bật tắt điện: mood="happy", preset="happy", neck_pitch=112.
- Đi bộ / nhảy múa: mood="happy", preset="walk".
- Đi ngủ / nghỉ ngơi: mood="sleepy", preset="sleepy", neck_pitch=62.
"""


def ask_bdx_brain(user_message: str, model: str = DEFAULT_MODEL) -> dict:
    """Gửi câu nói tới Ollama, tự động trích xuất & lưu thông tin cá nhân hóa vào buddy_memory.json."""
    global smarthome_state
    mem = load_memory()

    context_msg = (
        f"[Trạng thái Smart Home: Đèn bàn={smarthome_state['desk_lamp']}, "
        f"Quạt={smarthome_state['fan']}, Điều hòa={smarthome_state['ac']}]\n"
        f"Người dùng nói: {user_message}"
    )

    messages = [{"role": "system", "content": build_system_prompt(mem)}]
    for item in mem.get("recent_history", [])[-6:]:
        messages.append(item)
    messages.append({"role": "user", "content": context_msg})

    payload = {
        "model": model,
        "messages": messages,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.5,
            "num_predict": 260
        }
    }

    req = urllib.request.Request(
        OLLAMA_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            content = raw.get("message", {}).get("content", "{}")
            parsed = json.loads(content)
    except Exception as e:
        return {
            "reply": f"Ối, kết nối tới Ollama gặp lỗi: {e}",
            "mood": "curious",
            "preset": "curious",
            "servos": {"neck_yaw": 110, "neck_pitch": 100, "neck_roll": 112},
            "smarthome": {"device": "none", "state": "UNCHANGED"},
            "smarthome_state": smarthome_state,
            "memory_facts": mem.get("facts", [])
        }

    if not isinstance(parsed, dict):
        parsed = {"reply": str(parsed), "mood": "neutral", "preset": "neutral"}

    if not isinstance(parsed.get("servos"), dict):
        parsed["servos"] = {"neck_yaw": 90, "neck_pitch": 90, "neck_roll": 90}

    # 1. Cập nhật Smart Home nếu có lệnh
    sh = parsed.get("smarthome", {})
    if isinstance(sh, dict):
        dev = str(sh.get("device", "none")).lower()
        st = str(sh.get("state", "UNCHANGED")).upper()
        if dev in smarthome_state and st in ("ON", "OFF"):
            smarthome_state[dev] = st
    else:
        parsed["smarthome"] = {"device": "none", "state": "UNCHANGED"}

    # 2. Tự động lưu thông tin cá nhân hóa mới vào buddy_memory.json
    new_fact = parsed.get("remember_fact", "")
    if isinstance(new_fact, str):
        new_fact = new_fact.strip()
        if len(new_fact) > 3 and new_fact.lower() not in ("none", "null", "không", "khong"):
            if new_fact not in mem["facts"]:
                mem["facts"].append(new_fact)
                # Nếu câu có giới thiệu tên, cập nhật luôn owner_name
                for prefix in ("tên là ", "tên ", "chủ nhân là "):
                    if prefix in new_fact.lower():
                        idx = new_fact.lower().find(prefix) + len(prefix)
                        name_part = new_fact[idx:].split(",")[0].split(".")[0].strip()
                        if 1 < len(name_part) <= 25:
                            mem["owner_name"] = name_part

    # Lưu lịch sử hội thoại gần nhất
    mem["recent_history"].append({"role": "user", "content": user_message})
    mem["recent_history"].append({"role": "assistant", "content": json.dumps({
        "reply": parsed.get("reply", ""),
        "mood": parsed.get("mood", "neutral")
    }, ensure_ascii=False)})
    mem["recent_history"] = mem["recent_history"][-8:]
    save_memory(mem)

    parsed["smarthome_state"] = smarthome_state
    parsed["memory_facts"] = mem["facts"]
    return parsed
