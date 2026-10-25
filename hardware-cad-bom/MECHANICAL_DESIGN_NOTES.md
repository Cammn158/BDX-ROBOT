# 🛠️ Ghi Chú Thiết Kế Cơ Khí & In 3D: BDX-Mini Droid (7-DOF)

Tài liệu này định hướng việc thiết kế CAD (Fusion 360 / SolidWorks / Onshape) và thông số in 3D cho chú Robot **BDX-Mini 7 Bậc Tự Do**, kết hợp vẻ ngoài biểu cảm của **Star Wars BD-1 / Disney BDX Droid** với cơ cấu chân cân bằng ổn định trên mặt bàn.

---

## 1. Triết Lý Thiết Kế Cơ Học (Mechanical Philosophy)

Các dòng Robot BDX thực tế của Disney sử dụng động cơ BLDC truyền động trực tiếp kết hợp thuật toán Học tăng cường (Reinforcement Learning) và IMU tốc độ cao để tự cân bằng trên 2 chân điểm nhỏ. Khi thu nhỏ xuống quy mô **Desktop DIY sử dụng Servo MG90S/SG90**, chúng ta áp dụng giải pháp **"Visual BDX + Functional Otto-Plus"**:

1. **Giữ trọn linh hồn BDX / BD-1 ở phần Đầu & Thân trên:**
   - Đầu phẳng dẹt chữ nhật bo góc, vươn nhẹ về phía trước.
   - Mặt trước bố trí **Màn hình OLED 128x64** lệch tâm hoặc chính giữa, bên cạnh là **ống kính giả/thật của Camera OV2640** tạo vẻ ngoài bất đối xứng đặc trưng của BD-1.
   - Cụm **Cổ 3 Bậc Tự Do (Yaw - Pitch - Roll)** cho phép đầu thực hiện các chuyển động biểu cảm sống động nhất: nghiêng đầu tò mò (`Roll`), gật gù theo nhịp nhạc (`Pitch`), liếc nhìn theo người (`Yaw`).
2. **Chân tạo dáng Gấp Khúc Ngược (Reverse-Knee / Digitigrade Silhouette) nhưng Đế Bàn Chân phẳng thông minh:**
   - Phần đùi và ống chân in 3D tạo hình chữ `Z` gấp khúc về phía sau giống hệt chân đà điểu của BDX Droid.
   - Tuy nhiên, cơ cấu truyền động bên trong sử dụng **4 Servo MG90S (2 Hông Xoay + 2 Cổ Chân Nghiêng)** cùng bàn chân có diện tích tiếp xúc đủ rộng và đệm cao su mỏng.
   - Nhờ vậy, Robot **đứng vững 100% ngay cả khi ngắt điện Servo**, đồng thời có thể dồn trọng tâm sang trái/phải để nhấc chân bước đi, xoay người hoặc ngồi gập chân gọn gàng trên bàn.

---

## 2. Phân Bổ Trọng Tâm (Center of Mass - CoM)

Để cụm Cổ 3 trục không bị rung và Robot không bị chúi đầu về phía trước khi đi bộ:

- **Phần Đầu (`Head Pod` - Mục tiêu `< 45g`):**
  - Chỉ đặt các linh kiện siêu nhẹ: Màn hình OLED 0.96"/1.3" (~5g), cụm thấu kính Camera OV2640 (~3g), Micro INMP441 (~2g), lá đồng cảm ứng chạm (~1g).
  - In 3D vỏ đầu với `Infill 15%` (vật liệu PLA+ hoặc Matte PLA), độ dày thành `1.2mm - 1.6mm`.
- **Phần Thân Giữa (`Torso / Pelvis` - Đặt thấp sát trục Hông):**
  - Chứa toàn bộ linh kiện nặng: Board `ESP32-S3-CAM`, mạch `PCA9685`, mạch khuếch đại `MAX98357A`, Loa `4Ω 3W`, Radar `HLK-LD2410C` (hướng ra ngực trước) và mạch nguồn `UBEC`.
  - Nếu dùng Pin `2S 18650`, đặt khay pin nằm ngang ngay phía dưới/sau trục Hông để hạ thấp trọng tâm tối đa.

---

## 3. Thiết Kế Chi Tiết Cụm Cổ 3-DOF (`Yaw - Pitch - Roll`)

```text
         [ ĐẦU BDX-MINI (OLED + CAM + MIC + TOUCH) ]
                            │
                   ┌────────┴────────┐
                   │ Servo CH2: ROLL │  <-- Nghiêng đầu Trái/Phải (±30°)
                   └────────┬────────┘
                            │ (Khung chữ U nhỏ)
                   ┌────────┴────────┐
                   │ Servo CH1: PITCH│  <-- Gật/Ngửa đầu (-35° đến +45°)
                   └────────┬────────┘
                            │ (Trục đứng gắn xuống đỉnh thân)
                   ┌────────┴────────┐
                   │ Servo CH0: YAW  │  <-- Quay ngang Trái/Phải (±60°)
                   └─────────────────┘
```

- **Mẹo cơ khí quan trọng:**
  - Tại khớp `Pitch` (chịu mô-men xoắn lớn nhất do đầu vươn về trước), nên dùng **Servo MG90S bánh răng kim loại** và bố trí 1 vòng bi mini `MR85ZZ` (hoặc chốt trục đồng tâm) ở phía đối diện trục servo để chống xệ đầu.
  - Chừa rãnh luồn dây đường kính `8mm` xuyên qua tâm trục `Yaw` để bó dây Silicon AWG28 và cáp FPC Camera không bị căng khi cổ quay `±60°`.

---

## 4. Thông Số Khuyến Nghị Khi In 3D (Slicer Settings)

| Bộ phận | Vật liệu khuyên dùng | Độ cao lớp (Layer Height) | Số lớp thành (Wall Loops) | Độ đặc (Infill) | Hỗ trợ (Support) |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Vỏ Đầu (Head Shell & Bezel)** | Matte PLA (Trắng/Đỏ/Vàng kiểu BD-1) | `0.16 mm` | 2 | `15%` Gyroid | Tree Support (tối thiểu) |
| **Cụm Khớp Cổ (Neck Gimbal)** | PETG hoặc PLA+ (Chịu lực tốt) | `0.16 mm` | 3 - 4 | `35%` | Có (chỉnh khoảng hở Z `0.2mm`) |
| **Khung Thân (Main Torso)** | PLA+ / PETG | `0.20 mm` | 3 | `20%` | Tối ưu góc nghiêng `45°` để hạn chế support |
| **Đùi & Bàn Chân (Legs & Feet)**| PETG / PLA+ | `0.20 mm` | 4 | `30% - 40%` | Có tại hốc gắn Servo MG90S |
