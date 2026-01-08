#include <WiFi.h>
#include <FirebaseESP32.h>
#include <Wire.h>
#include <Adafruit_MLX90614.h>
#include <LiquidCrystal_I2C.h>
#include <WiFiManager.h> // <--- Tambah Library ni

// --- SETTING FIREBASE SAHAJA (WiFi tak payah tulis sini) ---
#define FIREBASE_HOST "hfmd-iot-system-default-rtdb.asia-southeast1.firebasedatabase.app"    
#define FIREBASE_AUTH "f69FBaoxFLgbzGy06MKfUpANzZhBBkg78DFDUSsu"     

// --- OBJEK HARDWARE ---
Adafruit_MLX90614 mlx = Adafruit_MLX90614();
LiquidCrystal_I2C lcd(0x27, 16, 2); 

// --- OBJEK FIREBASE ---
FirebaseData firebaseData;
FirebaseAuth auth;
FirebaseConfig config;

unsigned long sendDataPrevMillis = 0;

void setup() {
  Serial.begin(115200);
  
  // 1. SETUP I2C & SENSOR
  Wire.begin(21, 22); 
  
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("System Booting..");

  if (!mlx.begin()) {
    Serial.println("Ralat Sensor!");
    lcd.setCursor(0, 1);
    lcd.print("Sensor Error!");
    while (1);
  }
  delay(1000);

  // 2. SETUP WIFIMANAGER (INI BAHAGIAN BARU)
  WiFiManager wm;

  // Papar kat LCD tengah cari WiFi
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Connecting WiFi..");

  // Kalau tak jumpa WiFi lama, dia buka Hotspot nama "HFMD_SETUP"
  // Password hotspot takde (boleh biar kosong)
  bool res = wm.autoConnect("HFMD_SETUP"); 

  if(!res) {
      Serial.println("Gagal connect WiFi");
      lcd.setCursor(0, 1);
      lcd.print("WiFi Failed!");
      // Restart ESP32 kalau gagal
      ESP.restart();
  } 
  
  // Kalau sampai sini, maksudnya dah connect
  Serial.println("WiFi Connected!");
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("WiFi OK!");
  lcd.setCursor(0, 1);
  lcd.print(WiFi.localIP()); // Tunjuk IP kat LCD
  delay(2000);

  // 3. SETUP FIREBASE
  config.host = FIREBASE_HOST;
  config.signer.tokens.legacy_token = FIREBASE_AUTH;
  
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);
}

void loop() {
  // --- BACA SUHU ---
  float t_objek = mlx.readObjectTempC();
  float t_amb   = mlx.readAmbientTempC();

  // --- PAPARAN LCD (LIVE) ---
  lcd.setCursor(0, 0);
  lcd.print("Bdn: "); lcd.print(t_objek, 1); lcd.write(0xDF); lcd.print("C "); 

  lcd.setCursor(0, 1);
  lcd.print("Env: "); lcd.print(t_amb, 1); lcd.write(0xDF); lcd.print("C ");

  // --- HANTAR KE FIREBASE (SETIAP 2 SAAT) ---
  if (millis() - sendDataPrevMillis > 2000 || sendDataPrevMillis == 0) {
    sendDataPrevMillis = millis();

    Serial.print("Suhu: "); Serial.println(t_objek);

    if (Firebase.setFloat(firebaseData, "/sensor/suhu", t_objek)) {
      Serial.println("✅ Sent to Firebase");
    } else {
      Serial.print("❌ Fail: ");
      Serial.println(firebaseData.errorReason());
    }
  }
}