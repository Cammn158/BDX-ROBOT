# 📡 Kiến Trúc Phần Mềm & Giao Thức Truyền Thông (Robot - Server - SmartHome)

Tài liệu này định nghĩa kiến trúc đa luồng trên `ESP32-S3`, luồng xử lý của `Local AI Server` và đặc tả gói tin **WebSocket / MQTT** kết nối toàn hệ thống.

---

## 1. Phân Chia Tác Vụ Đa Luồng Trên `ESP32-S3` (Dual-Core FreeRTOS)

Chip `ESP32-S3 N16R8` sở hữu 2 nhân xử lý (`Xtensa LX7 @ 240MHz`) và `8MB Octal PSRAM`. Để đảm bảo đôi mắt OLED luôn mượt `60 FPS`, 7 Servo nội suy không bị giật cục trong khi vẫn truyền/nhận âm thanh thời gian thực, hệ thống được chia về 2 Core như sau:

| Nhân xử lý | Tên Task (FreeRTOS) | Độ ưu tiên | Chu kỳ / Tần số | Nhiệm vụ chi tiết |
| :---: | :--- | :---: | :---: | :--- |
| **Core 0** *(Network & Media)* | `Task_Net_WS` | Cao (4) | Event-driven | Duy trì kết nối WebSocket với Local AI Server, phân tích JSON lệnh điều khiển và đóng gói dữ liệu gửi đi. |
| | `Task_Audio_Stream` | Rất cao (5) | `16kHz` DMA | Đọc DMA từ Mic `INMP441` đẩy vào RingBuffer PSRAM và đọc luồng PCM từ Server phát ra `MAX98357A`. |
| | `Task_Camera_Snap` | Trung bình (2)| On-demand / 1Hz | Chụp ảnh JPEG từ `OV2640` lưu vào PSRAM khi AI Server yêu cầu (`capture_vision`) hoặc khi có người mới xuất hiện. |
| **Core 1** *(Real-time Robotics)*| `Task_Kinematics_7DOF`| Rất cao (5) | `50Hz` (`20ms`) | Tính toán nội suy mượt (Cubic Bezier / Cosine Easing & Sine Oscillator) cho 7 trục Servo và cập nhật qua `PCA9685`. |
| | `Task_Display_OLED` | Cao (4) | `30-60Hz` | Render đôi mắt hoạt họa (Procedural Eye Engine: chớp mắt ngẫu nhiên, nhìn liếc đồng bộ góc cổ `Yaw/Pitch`, biểu cảm cảm xúc). |
| | `Task_Sensors_Input` | Thấp (1) | `20Hz` (`50ms`) | Đọc cảm biến chạm đỉnh đầu (`GPIO 14`) và radar hiện diện `HLK-LD2410C` (`GPIO 42`). |

> [!IMPORTANT]
> **Đồng bộ khóa Mutex cho Bus I2C Dùng Chung (`i2c_bus_mutex`):**
> Vì cả `Task_Kinematics_7DOF` (`PCA9685 @ 0x40`) và `Task_Display_OLED` (`SSD1306 @ 0x3C`) đều chạy trên Core 1 và dùng chung bus `I2C_NUM_0 (400kHz)`, chúng được bọc qua một `SemaphoreHandle_t i2c_mutex` (hoặc gộp chung vào một vòng lặp `SuperLoop_I2C` trên Core 1) để tuyệt đối không xảy ra xung đột khung truyền I2C.

---

## 2. Giao Thức WebSocket Giữa `Robot (ESP32-S3)` & `Local AI Server`

Giao tiếp giữa Robot (hoặc `Web Simulator` trên PC) với `Local AI Server` sử dụng **1 kết nối WebSocket duy nhất** (`ws://<SERVER_LAN_IP>:8765/ws/robot`) hỗ trợ 2 loại frame:
1. **Binary Frames:** Truyền luồng âm thanh thô (`PCM 16-bit, 16kHz, Mono`) và khung hình ảnh JPEG (`OV2640`) để tối ưu băng thông tối đa.
2. **Text Frames (JSON):** Truyền sự kiện cảm biến, trạng thái biểu cảm mắt, lệnh phối hợp chuyển động 7-DOF và đồng bộ câu thoại.

### 2.1. Gói tin từ `Robot` -> `Local AI Server`

#### A. Sự kiện Tương tác & Cảm biến (`event`)
```json
{
  "type": "sensor_event",
  "timestamp_ms": 124500,
  "event": "head_touch_petting",
  "payload": {
    "touch_duration_ms": 850,
    "radar_presence": true,
    "radar_distance_cm": 65
  }
}
```
*(Các giá trị `event`: `"wake_word_detected"`, `"head_touch_tap"`, `"head_touch_petting"`, `"human_approached"`, `"human_left"`)*

#### B. Báo cáo Trạng thái Robot (`telemetry`)
```json
{
  "type": "telemetry",
  "battery_mv": 7850,
  "wifi_rssi": -54,
  "current_pose": "standing_idle",
  "servos_deg": [90, 90, 90, 90, 90, 90, 90]
}
```

---

### 2.2. Gói tin từ `Local AI Server` -> `Robot` (Kịch bản Biểu cảm & Hành động)

Khi LLM Agent trả lời người dùng, nó sinh ra đồng thời câu thoại (chuyển qua TTS) và một gói tin **Choreography (Biên đạo Biểu cảm)** gửi xuống Robot:

```json
{
  "type": "choreography_cmd",
  "utterance_id": "utt_0042",
  "text_subtitle": "Dạ, em đã bật đèn bàn làm việc cho anh rồi ạ!",
  "eye_expression": {
    "mood": "happy_squint",
    "look_x": 0.2,
    "look_y": 0.1,
    "blink_rate": "normal"
  },
  "neck_motion": {
    "preset": "nod_yes_enthusiastic",
    "keyframes": [
      { "t_ms": 0,   "yaw": 90, "pitch": 90,  "roll": 95, "easing": "ease_out" },
      { "t_ms": 200, "yaw": 90, "pitch": 115, "roll": 95, "easing": "ease_in_out" },
      { "t_ms": 400, "yaw": 90, "pitch": 85,  "roll": 95, "easing": "ease_in_out" },
      { "t_ms": 650, "yaw": 90, "pitch": 90,  "roll": 90, "easing": "ease_out" }
    ]
  },
  "leg_action": {
    "gait": "happy_bounce",
    "cycles": 2,
    "speed": 1.2
  }
}
```

#### Danh sách các Biểu cảm Mắt (`eye_expression.mood`)
- `neutral`: Mắt chữ nhật bo góc tiêu chuẩn, chớp tự nhiên mỗi 3–5 giây.
- `curious`: Một mắt mở to, một mắt hơi nheo, kết hợp cổ nghiêng (`Neck Roll = ±20°`).
- `happy_squint`: Hai mắt cong hình vòm cười (`^ ^`).
- `listening`: Đôi mắt sáng, con ngươi hơi hướng lên người nói, viền mắt nhấp nháy theo biên độ giọng nói.
- `thinking`: Mắt liếc lên góc trên bên phải/trái khi chờ LLM suy luận.
- `sleepy`: Mí mắt sụp xuống 60%, ngáp nhẹ khi không có người ở bàn làm việc.
- `surprised` / `alert`: Mắt mở to đột ngột khi bị chạm bất ngờ hoặc có cảnh báo Smart Home.

---

## 3. Giao Thức MQTT Cho Hệ Sinh Thái Smart Home DIY (`ESP32-C3`)

`Local AI Server` tích hợp sẵn `mqtt_bridge` kết nối tới MQTT Broker nội bộ (ví dụ: Mosquitto chạy trên PC hoặc Docker ở cổng `1883`). Khi người dùng ra lệnh bằng giọng nói cho Robot (*"BDX ơi, trời hơi nóng, bật quạt giúp mình"*), LLM gọi công cụ (Tool Calling / MCP) để xuất bản lệnh MQTT:

### Cấu trúc Topic MQTT Chuẩn
- **Điều khiển thiết bị (Server -> Node C3):** `bdx_home/nodes/<node_id>/cmd`
  ```json
  {
    "device": "desk_lamp",
    "action": "SET",
    "state": "ON",
    "brightness": 80
  }
  ```
- **Trạng thái phản hồi (Node C3 -> Server):** `bdx_home/nodes/<node_id>/state`
- **Dữ liệu cảm biến phòng (Node C3 -> Server):** `bdx_home/nodes/<node_id>/telemetry`
  ```json
  {
    "node_id": "bedroom_env_01",
    "temperature_c": 27.4,
    "humidity_pct": 62.5,
    "presence": true
  }
  ```
