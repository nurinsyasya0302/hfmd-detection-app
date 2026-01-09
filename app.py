import streamlit as st
import requests
from roboflow import Roboflow
from PIL import Image
import io
import time

# --- CONFIGURATION (IoT & AI) ---
# URL Firebase anda yang telah disahkan aktif
FIREBASE_URL = "https://hfmd-iot-system-default-rtdb.asia-southeast1.firebasedatabase.app/sensor/suhu.json" 

# Kredential Roboflow anda
ROBOFLOW_API_KEY = "NwFYMjnLg2zG5rk2F2dZ"
ROBOFLOW_MODEL_ID = "hand-hfmd-3qdrq/3" 

# --- PAGE SETUP ---
st.set_page_config(page_title="HFMD Detector FYP", layout="wide")

st.title("🏥 Sistem Pintar Pengesanan HFMD")
st.write("Dashboard Integrasi IoT (Suhu) & AI (Computer Vision)")

# --- BAHAGIAN 1: IoT DATA MONITORING (Real-time) ---
st.header("1. Status Pesakit (IoT Sensor)")

# Placeholder untuk membolehkan auto-refresh tanpa kelip skrin
placeholder = st.empty()

def get_temperature():
    try:
        # Mengambil data suhu terkini dari Firebase
        response = requests.get(FIREBASE_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data is None:
                return 0.0
            return float(data)
    except Exception:
        return 0.0
    return 0.0

# Ambil data dari Firebase
suhu_semasa = get_temperature()

# Paparan Status Suhu
with placeholder.container():
    kpi1, kpi2 = st.columns([1, 2])
    
    # Metrik Suhu Utama
    diff = suhu_semasa - 37.0
    kpi1.metric(
        label="Suhu Badan Terkini",
        value=f"{suhu_semasa:.1f} °C",
        delta=f"{diff:.1f} °C dari normal",
        delta_color="inverse" if suhu_semasa >= 37.5 else "normal"
    )
    
    # --- LOGIC STATUS YANG DIKEMASKINI ---
    # 1. Jika suhu tinggi (Demam)
    if suhu_semasa >= 37.5:
        kpi2.error(f"STATUS: DEMAM PANAS 🥵 ({suhu_semasa:.1f} °C)")
        st.toast("Amaran! Suhu pesakit tinggi!", icon="🔥")
        
    # 2. Jika suhu sangat rendah (Sensor tidak dipakai/error)
    elif suhu_semasa < 20.0:
        kpi2.warning("STATUS: SENSOR ERROR / TAK PAKAI")
        
    # 3. Jika suhu normal (Termasuk suhu bilik 28.6 C)
    else:
        kpi2.success("STATUS: SUHU NORMAL ✅")

# --- BAHAGIAN 2: AI DETECTION ---
st.markdown("---")
st.header("2. AI Scan Tangan")
col1, col2 = st.columns(2)

with col1:
    st.info("Sila halakan kamera pada tangan/kaki pesakit.")
    picture = st.camera_input("Ambil Gambar", key="camera")

with col2:
    if picture:
        st.image(picture, caption="Gambar Diambil", use_column_width=True)
        st.write("⏳ Sedang menganalisis dengan AI...")
        
        try:
            # Integrasi Roboflow API
            rf = Roboflow(api_key=ROBOFLOW_API_KEY)
            project_name = ROBOFLOW_MODEL_ID.split("/")[0]
            version_number = ROBOFLOW_MODEL_ID.split("/")[1]
            
            project = rf.workspace().project(project_name)
            model = project.version(int(version_number)).model
            
            # Analisis gambar
            temp_filename = "temp_scan.jpg"
            with open(temp_filename, "wb") as f:
                f.write(picture.getvalue())

            prediction = model.predict(temp_filename, confidence=40, overlap=30).json()
            predictions_list = prediction['predictions']
            
            if len(predictions_list) > 0:
                st.error(f"⚠️ POSITIF HFMD DIKESAN!")
                st.metric("Jumlah Lesion", f"{len(predictions_list)} bintik")
                st.warning("Cadangan: Segera rujuk pakar perubatan.")
            else:
                st.success("✅ NEGATIF: Tiada bintik HFMD dikesan.")
                
        except Exception as e:
            st.error(f"Ralat AI: {e}")

# --- AUTO REFRESH SETIAP 3 SAAT ---
# Membolehkan data dari ESP32 sentiasa sync secara automatik
time.sleep(3)

st.rerun()

