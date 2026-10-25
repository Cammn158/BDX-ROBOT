#pragma once

/**
 * @file robot_pins.h
 * @brief Định nghĩa Pinout chuẩn cho BDX-Mini Droid (ESP32-S3 N16R8)
 * @warning KHÔNG sử dụng GPIO 35, 36, 37 (Đã dùng nội bộ cho 8MB Octal PSRAM)
 */

// ============================================================================
// 1. BUS I2C DÙNG CHUNG (Màn hình mắt OLED + Mạch 16 kênh Servo PCA9685)
// ============================================================================
#define I2C_SHARED_SDA_PIN      1
#define I2C_SHARED_SCL_PIN      2
#define I2C_SHARED_FREQ_HZ      400000UL  // 400kHz Fast Mode

#define OLED_I2C_ADDR           0x3C      // SSD1306 / SH1106 128x64
#define OLED_SCREEN_WIDTH       128
#define OLED_SCREEN_HEIGHT      64

#define PCA9685_I2C_ADDR        0x40      // Mặc định không hàn jumper A0-A5
#define PCA9685_PWM_FREQ_HZ     50        // Chuẩn 50Hz (20ms) cho Servo MG90S/SG90

// ============================================================================
// 2. KÊNH SERVO 7 BẬC TỰ DO TRÊN PCA9685 (7-DOF KINEMATICS)
// ============================================================================
// Cụm Cổ Biểu Cảm (3-DOF)
#define SERVO_CH_NECK_YAW       0         // Quay ngang Trái/Phải (Home: 90°)
#define SERVO_CH_NECK_PITCH     1         // Gật/Ngửa đầu (Home: 90°)
#define SERVO_CH_NECK_ROLL      2         // Nghiêng đầu tò mò (Home: 90°)
#define SERVO_CH_EAR_ANTENNA    3         // Dự phòng Ăng-ten BD-1

// Cụm Chân Biped (4-DOF)
#define SERVO_CH_LEFT_HIP       4         // Hông Trái (Home: 90°)
#define SERVO_CH_RIGHT_HIP      5         // Hông Phải (Home: 90°)
#define SERVO_CH_LEFT_ANKLE     6         // Cổ chân Trái (Home: 90°)
#define SERVO_CH_RIGHT_ANKLE    7         // Cổ chân Phải (Home: 90°)

// ============================================================================
// 3. ÂM THANH 2 CHIỀU FULL-DUPLEX I2S (INMP441 + MAX98357A)
// ============================================================================
#define I2S_SHARED_BCLK_PIN     38        // Nối vào SCK (INMP441) & BCLK (MAX98357A)
#define I2S_SHARED_WS_LRC_PIN   39        // Nối vào WS (INMP441)  & LRC (MAX98357A)
#define I2S_MIC_DIN_PIN         40        // Nối vào SD của Micro INMP441
#define I2S_SPK_DOUT_PIN        41        // Nối vào DIN của Amply MAX98357A
#define I2S_AUDIO_SAMPLE_RATE   16000     // 16kHz, 16-bit Mono chuẩn cho STT/TTS

// ============================================================================
// 4. CẢM BIẾN TƯƠNG TÁC (TOUCH ĐỈNH ĐẦU + RADAR MMWAVE HLK-LD2410C)
// ============================================================================
#define HEAD_TOUCH_PIN          14        // Cảm ứng chạm trên đỉnh đầu (TOUCH14)
#define RADAR_PRESENCE_OUT_PIN  42        // Chân OUT từ radar HLK-LD2410C (HIGH = Có người)
#define RADAR_UART_TX_PIN       47        // Nối với RX của HLK-LD2410C (Tùy chọn)
#define RADAR_UART_RX_PIN       48        // Nối với TX của HLK-LD2410C (Tùy chọn)

// ============================================================================
// 5. CAMERA OV2640 (CHUẨN KHE FPC 24-PIN TRÊN BOARD ESP32-S3-CAM N16R8)
// ============================================================================
#define CAM_PIN_PWDN            -1
#define CAM_PIN_RESET           -1
#define CAM_PIN_XCLK            15
#define CAM_PIN_SIOD            4
#define CAM_PIN_SIOC            5
#define CAM_PIN_Y9              16
#define CAM_PIN_Y8              17
#define CAM_PIN_Y7              18
#define CAM_PIN_Y6              12
#define CAM_PIN_Y5              10
#define CAM_PIN_Y4              8
#define CAM_PIN_Y3              9
#define CAM_PIN_Y2              11
#define CAM_PIN_VSYNC           6
#define CAM_PIN_HREF            7
#define CAM_PIN_PCLK            13
