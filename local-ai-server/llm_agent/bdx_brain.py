"""
BDX-Mini Droid — Local AI Brain (Ollama LLM + Emotion/Kinematics Planner + Smart Home MCP)
Giao tiếp trực tiếp với Ollama tại http://localhost:11434/api/chat (Model: qwen2.5:3b)
"""

import json
import urllib.request
import urllib.error

OLLAMA_API_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen2.5:3b"

SYSTEM_PROMPT = """Bạn là BDX-Mini, một chú Robot AI 2 chân để bàn thông minh, đáng yêu (lấy cảm hứng từ Disney BDX Droid & Star Wars BD-1) kiêm Trung tâm Điều khiển Nhà thông minh (Smart Home Hub).

Khi người dùng trò chuyện hoặc ra lệnh, bạn PHẢI trả lời bằng ĐÚNG MỘT chuỗi JSON hợp lệ theo cấu trúc sau (không thêm markdown bên ngoài JSON):
{
  "reply": "Câu trả lời tiếng Việt ngắn gọn, tự nhiên, giàu cảm xúc của BDX-Mini (1-2 câu)",
  "mood": "neutral | curious | happy | listen | sleepy",
  "preset": "neutral | curious | happy | walk | listen | sleepy",
  "servos": {
    "neck_yaw": 90,
    "neck_pitch": 90,
    "neck_roll": 90
  },
  "smarthome": {
    "device": "none | desk_lamp | fan | ac",
    "state": "ON | OFF | UNCHANGED"
  }
}

Quy tắc biểu cảm cơ thể (7-DOF & Mắt OLED):
- Khi tò mò hoặc hỏi lại: mood="curious", preset="curious", neck_roll=114, neck_pitch=105, neck_yaw=110.
- Khi vui vẻ, khen ngợi hoặc vừa thực hiện xong lệnh bật/tắt điện: mood="happy", preset="happy", neck_pitch=112.
- Khi được yêu cầu bước đi, nhảy múa, tuần tra: mood="happy", preset="walk".
- Khi được bảo đi ngủ, nghỉ ngơi: mood="sleepy", preset="sleepy", neck_pitch=62.
- Khi người dùng yêu cầu bật/tắt đèn bàn (desk_lamp), quạt (fan) hoặc điều hòa (ac): cập nhật trường "smarthome" tương ứng.
"""

# Trạng thái giả lập của các thiết bị Smart Home ESP32-C3
smarthome_state = {
    "desk_lamp": "OFF",
    "fan": "OFF",
    "ac": "OFF",
    "temperature_c": 27.5,
    "humidity_pct": 62.0
}

conversation_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]


def ask_bdx_brain(user_message: str, model: str = DEFAULT_MODEL) -> dict:
    """Gửi câu nói của người dùng tới Ollama và nhận về kịch bản Cảm xúc + Góc Servo + Lệnh Smart Home."""
    global conversation_history, smarthome_state

    context_msg = (
        f"[Trạng thái Smart Home hiện tại: Đèn bàn={smarthome_state['desk_lamp']}, "
        f"Quạt={smarthome_state['fan']}, Điều hòa={smarthome_state['ac']}, "
        f"Nhiệt độ={smarthome_state['temperature_c']}°C]\n"
        f"Người dùng nói: {user_message}"
    )
    conversation_history.append({"role": "user", "content": context_msg})

    # Giữ lịch sử tối đa 10 lượt gần nhất để phản hồi nhanh trên GPU
    if len(conversation_history) > 11:
        conversation_history = [conversation_history[0]] + conversation_history[-10:]

    payload = {
        "model": model,
        "messages": conversation_history,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.6,
            "num_predict": 220
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
            conversation_history.append({"role": "assistant", "content": content})
            parsed = json.loads(content)
    except Exception as e:
        return {
            "reply": f"Ối, kết nối tới Ollama gặp lỗi: {e}",
            "mood": "curious",
            "preset": "curious",
            "servos": {"neck_yaw": 110, "neck_pitch": 100, "neck_roll": 112},
            "smarthome": {"device": "none", "state": "UNCHANGED"},
            "smarthome_state": smarthome_state
        }

    # Cập nhật trạng thái Smart Home nếu LLM ra lệnh điều khiển
    sh = parsed.get("smarthome", {})
    dev = sh.get("device", "none")
    st = sh.get("state", "UNCHANGED")
    if dev in smarthome_state and st in ("ON", "OFF"):
        smarthome_state[dev] = st

    parsed["smarthome_state"] = smarthome_state
    return parsed
