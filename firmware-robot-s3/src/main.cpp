/**
 * @file main.cpp
 * @brief Firmware khởi đầu cho BDX-Mini Droid (Chạy được ngay trên Velxio / Wokwi / ESP32-S3 thật)
 * @details Demo đồng bộ Bus I2C dùng chung (SDA=GPIO1, SCL=GPIO2):
 *          - Màn hình OLED 128x64 (0x3C): Vẽ đôi mắt Robot Procedural (Chớp mắt, Liếc, Vui, Tò mò)
 *          - Mạch PCA9685 (0x40): Nội suy mượt (Cosine Easing) cho 3 khớp Cổ + 4 khớp Chân (7-DOF)
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_PWMServoDriver.h>
#include "robot_pins.h"

// Khởi tạo đối tượng OLED và PCA9685 trên cùng Bus I2C (Wire)
Adafruit_SSD1306 oled(OLED_SCREEN_WIDTH, OLED_SCREEN_HEIGHT, &Wire, -1);
Adafruit_PWMServoDriver pca9685 = Adafruit_PWMServoDriver(PCA9685_I2C_ADDR, Wire);

// Cấu hình xung PWM chuẩn cho Servo MG90S/SG90 ở tần số 50Hz (4096 ticks = 20ms)
#define SERVO_MIN_PULSE_TICKS  110  // ~500us  (0 độ)
#define SERVO_MAX_PULSE_TICKS  500  // ~2400us (180 độ)

// Trạng thái biểu cảm của Robot
enum RobotMood {
    MOOD_NEUTRAL = 0,
    MOOD_CURIOUS,
    MOOD_HAPPY,
    MOOD_SLEEPY
};

struct RobotState {
    RobotMood mood = MOOD_NEUTRAL;
    // Góc hiện tại và góc mục tiêu của 7 trục Servo (Đơn vị: Độ, 90° là trung tâm)
    float currentDeg[8] = {90, 90, 90, 90, 90, 90, 90, 90};
    float targetDeg[8]  = {90, 90, 90, 90, 90, 90, 90, 90};
    // Tọa độ liếc mắt (-1.0 đến +1.0)
    float eyeLookX = 0.0f;
    float eyeLookY = 0.0f;
    bool isBlinking = false;
    uint32_t lastBlinkMs = 0;
    uint32_t lastPoseChangeMs = 0;
} bot;

// Chuyển đổi góc (0-180 độ) sang xung PWM 12-bit cho PCA9685
void setServoAngle(uint8_t channel, float angleDeg) {
    angleDeg = constrain(angleDeg, 20.0f, 160.0f);
    uint16_t pulse = map((long)(angleDeg * 10), 0, 1800, SERVO_MIN_PULSE_TICKS, SERVO_MAX_PULSE_TICKS);
    pca9685.setPWM(channel, 0, pulse);
}

// Engine vẽ đôi mắt BDX-Mini Procedural trên màn hình OLED 128x64
void renderProceduralEyes() {
    oled.clearDisplay();

    int offsetX = (int)(bot.eyeLookX * 14.0f);
    int offsetY = (int)(bot.eyeLookY * 8.0f);

    int leftEyeX  = 20 + offsetX;
    int rightEyeX = 76 + offsetX;
    int baseEyeY  = 16 + offsetY;
    int eyeW      = 32;
    int eyeH      = 32;

    if (bot.isBlinking) {
        // Mắt nhắm (vẽ 2 đường ngang dày)
        oled.fillRoundRect(leftEyeX,  baseEyeY + 14, eyeW, 4, 2, SSD1306_WHITE);
        oled.fillRoundRect(rightEyeX, baseEyeY + 14, eyeW, 4, 2, SSD1306_WHITE);
    } else if (bot.mood == MOOD_HAPPY) {
        // Mắt cười cong hình vòm (^ ^)
        oled.fillRoundRect(leftEyeX,  baseEyeY + 4, eyeW, 24, 10, SSD1306_WHITE);
        oled.fillRoundRect(leftEyeX + 4, baseEyeY + 14, eyeW - 8, 20, 8, SSD1306_BLACK);
        oled.fillRoundRect(rightEyeX, baseEyeY + 4, eyeW, 24, 10, SSD1306_WHITE);
        oled.fillRoundRect(rightEyeX + 4, baseEyeY + 14, eyeW - 8, 20, 8, SSD1306_BLACK);
    } else if (bot.mood == MOOD_CURIOUS) {
        // Mắt tò mò: Mắt trái mở to, mắt phải hơi nheo (kiểu BD-1 đang suy nghĩ)
        oled.fillRoundRect(leftEyeX,  baseEyeY - 2, eyeW, 36, 8, SSD1306_WHITE);
        oled.fillRoundRect(rightEyeX, baseEyeY + 6, eyeW, 20, 6, SSD1306_WHITE);
    } else if (bot.mood == MOOD_SLEEPY) {
        // Mắt buồn ngủ (mí mắt sụp xuống nửa trên)
        oled.fillRoundRect(leftEyeX,  baseEyeY + 12, eyeW, 18, 6, SSD1306_WHITE);
        oled.fillRoundRect(rightEyeX, baseEyeY + 12, eyeW, 18, 6, SSD1306_WHITE);
    } else {
        // Mắt tiêu chuẩn (Neutral)
        oled.fillRoundRect(leftEyeX,  baseEyeY, eyeW, eyeH, 8, SSD1306_WHITE);
        oled.fillRoundRect(rightEyeX, baseEyeY, eyeW, eyeH, 8, SSD1306_WHITE);
    }

    oled.display();
}

// Cập nhật nội suy chuyển động mượt (Smoothing Filter) ở tần số 50Hz
void updateKinematicsAndEyes() {
    uint32_t now = millis();

    // 1. Tự động chớp mắt ngẫu nhiên mỗi 3.5 giây
    if (!bot.isBlinking && (now - bot.lastBlinkMs > 3500)) {
        bot.isBlinking = true;
        bot.lastBlinkMs = now;
    } else if (bot.isBlinking && (now - bot.lastBlinkMs > 140)) {
        bot.isBlinking = false;
        bot.lastBlinkMs = now;
    }

    // 2. Nội suy mượt góc Servo tiến dần về targetDeg (Exponential Smoothing)
    const float smoothFactor = 0.15f;
    for (uint8_t ch = 0; ch < 8; ch++) {
        bot.currentDeg[ch] += (bot.targetDeg[ch] - bot.currentDeg[ch]) * smoothFactor;
        setServoAngle(ch, bot.currentDeg[ch]);
    }

    // 3. Đồng bộ hướng liếc mắt OLED theo góc quay Cổ (Yaw & Pitch)
    bot.eyeLookX = (bot.currentDeg[SERVO_CH_NECK_YAW] - 90.0f) / 45.0f;
    bot.eyeLookY = (90.0f - bot.currentDeg[SERVO_CH_NECK_PITCH]) / 35.0f;
}

void setup() {
    Serial.begin(115200);
    delay(300);
    Serial.println("\n=== [BDX-Mini Droid] Starting Shared I2C Bus (OLED + PCA9685) ===");

    // Khởi tạo Bus I2C dùng chung trên GPIO 1 (SDA) và GPIO 2 (SCL)
    Wire.begin(I2C_SHARED_SDA_PIN, I2C_SHARED_SCL_PIN, I2C_SHARED_FREQ_HZ);

    // 1. Khởi tạo màn hình OLED 128x64 tại địa chỉ 0x3C
    if (!oled.begin(SSD1306_SWITCHCAPVCC, OLED_I2C_ADDR)) {
        Serial.println("[WARN] Khong tim thay OLED tai 0x3C! Kiem tra day SDA/SCL.");
    } else {
        Serial.println("[OK] OLED 128x64 (0x3C) san sang.");
    }

    // 2. Khởi tạo mạch PCA9685 tại địa chỉ 0x40
    pca9685.begin();
    pca9685.setPWMFreq(PCA9685_PWM_FREQ_HZ);
    Serial.println("[OK] PCA9685 16-ch Servo Driver (0x40) san sang.");

    // Đưa toàn bộ 7 Servo về vị trí trung tâm (Home = 90 độ)
    for (uint8_t ch = 0; ch < 8; ch++) {
        setServoAngle(ch, 90.0f);
    }
}

void loop() {
    uint32_t now = millis();

    // Demo tự động chuyển đổi kịch bản ngôn ngữ cơ thể mỗi 4 giây
    if (now - bot.lastPoseChangeMs > 4000) {
        bot.lastPoseChangeMs = now;
        static uint8_t step = 0;
        step = (step + 1) % 4;

        switch (step) {
            case 0: // Trạng thái Đứng Thẳng Nhìn Thẳng (Neutral)
                Serial.println("-> Pose: NEUTRAL (Home)");
                bot.mood = MOOD_NEUTRAL;
                bot.targetDeg[SERVO_CH_NECK_YAW]   = 90;
                bot.targetDeg[SERVO_CH_NECK_PITCH] = 90;
                bot.targetDeg[SERVO_CH_NECK_ROLL]  = 90;
                bot.targetDeg[SERVO_CH_LEFT_ANKLE] = 90;
                bot.targetDeg[SERVO_CH_RIGHT_ANKLE]= 90;
                break;

            case 1: // Trạng thái Nghiêng Đầu Tò Mò (Curious BD-1 Tilt)
                Serial.println("-> Pose: CURIOUS HEAD TILT");
                bot.mood = MOOD_CURIOUS;
                bot.targetDeg[SERVO_CH_NECK_YAW]   = 115; // Quay nhẹ sang trái
                bot.targetDeg[SERVO_CH_NECK_PITCH] = 105; // Ngước nhẹ lên nhìn người
                bot.targetDeg[SERVO_CH_NECK_ROLL]  = 112; // Nghiêng đầu 22 độ
                break;

            case 2: // Trạng thái Vui Vẻ Gật Đầu & Nhún Chân (Happy Bounce)
                Serial.println("-> Pose: HAPPY NOD & BOUNCE");
                bot.mood = MOOD_HAPPY;
                bot.targetDeg[SERVO_CH_NECK_YAW]   = 90;
                bot.targetDeg[SERVO_CH_NECK_PITCH] = 120;
                bot.targetDeg[SERVO_CH_NECK_ROLL]  = 80;
                bot.targetDeg[SERVO_CH_LEFT_ANKLE] = 108;
                bot.targetDeg[SERVO_CH_RIGHT_ANKLE]= 72;
                break;

            case 3: // Trạng thái Buồn Ngủ Cúi Đầu (Sleepy Idle)
                Serial.println("-> Pose: SLEEPY IDLE");
                bot.mood = MOOD_SLEEPY;
                bot.targetDeg[SERVO_CH_NECK_YAW]   = 85;
                bot.targetDeg[SERVO_CH_NECK_PITCH] = 68;  // Cúi đầu xuống
                bot.targetDeg[SERVO_CH_NECK_ROLL]  = 90;
                bot.targetDeg[SERVO_CH_LEFT_ANKLE] = 90;
                bot.targetDeg[SERVO_CH_RIGHT_ANKLE]= 90;
                break;
        }
    }

    updateKinematicsAndEyes();
    renderProceduralEyes();
    delay(20); // Chu kỳ 50Hz (20ms)
}
