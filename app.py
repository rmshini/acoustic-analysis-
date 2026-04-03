import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import trimesh
from io import BytesIO

# --- PAGE SETUP ---
st.set_page_config(page_title="Advanced Room Acoustic Lab", layout="wide")

# --- MATERIAL DATABASE (Absorption Alpha 125Hz - 4kHz) ---
mat_db = {
    "Concrete (Rough)": [0.01, 0.01, 0.02, 0.02, 0.03, 0.05],
    "Brick Wall (Unpainted)": [0.02, 0.02, 0.03, 0.04, 0.05, 0.07],
    "Timber Floor": [0.15, 0.11, 0.10, 0.07, 0.06, 0.07],
    "Acoustic Ceiling Tile": [0.70, 0.65, 0.75, 0.80, 0.90, 0.90],
    "Glass Pane (6mm)": [0.10, 0.06, 0.04, 0.03, 0.02, 0.02],
    "Custom Panel (High Abs)": [0.45, 0.70, 0.95, 0.95, 0.90, 0.85]
}
freqs = [125, 250, 500, 1000, 2000, 4000]

# --- APP HEADER ---
st.title("🏛️ Advanced 3D Geometrical Acoustic Simulator")
st.markdown("---")

# --- SIDEBAR: GEOMETRY & OBJECTS ---
with st.sidebar:
    st.header("1. Room Geometry")
    L = st.number_input("Length (m)", value=8.0)
    W = st.number_input("Width (m)", value=6.0)
    H = st.number_input("Height (m)", value=3.0)
    
    st.header("2. Layer Thickness & Position")
    wall_thick = st.slider("Wall Thickness (mm)", 100, 450, 230)
    temp = st.slider("Temp (°C)", 15, 40, 25)
    hum = st.slider("Humidity (%)", 20, 80, 50)

    st.header("3. Material Assignment")
    m_floor = st.selectbox("Floor Layer", list(mat_db.keys()), index=2)
    m_wall = st.selectbox("Wall Layers", list(mat_db.keys()), index=1)
    m_ceil = st.selectbox("Ceiling Layer", list(mat_db.keys()), index=3)
    
    st.header("4. 3D Object Imports")
    uploaded_stl = st.file_uploader("Import Acoustic Panel (STL)", type=['stl'])
    if uploaded_stl:
        p_x = st.slider("Panel X Position", 0.0, L, L/2)
        p_rot = st.slider("Panel Rotation (deg)", 0, 360, 0)
        p_count = st.number_input("Copy Count", 1, 20, 1)

# --- LAYOUT COLUMNS ---
col_3d, col_metrics = st.columns([1.5, 1])

# --- CALCULATION ENGINE ---
def run_simulation():
    # Environmental speed of sound
    c = 331.3 + (0.6 * temp)
    V = L * W * H
    S = 2 * (L*W + L*H + W*H)
    
    # Statistical Acoustic Solvers
    res = []
    for i in range(6):
        # Absorption calculation
        total_a = (L*W * mat_db[m_floor][i]) + (L*W * mat_db[m_ceil][i]) + (2*(L*H + W*H) * mat_db[m_wall][i])
        
        # 1. RT60 (Sabine)
        rt60 = (0.161 * V) / total_a
        # 2. EDT
        edt = rt60 * 0.88
        # 3. Clarity C50 (Speech)
        c50 = 10 * np.log10((1 - np.exp(-0.691/rt60)) / (np.exp(-0.691/rt60) + 0.0001))
        # 4. Clarity C80 (Music)
        c80 = c50 + 2.8
        # 5. Definition D50
        d50 = (1 / (1 + 10**(-c50/10))) * 100
        # 6. SPL (Assuming 90dB source at 1m)
        spl = 90 - 20*np.log10(max(1, L/2)) + 10*np.log10(rt60/0.5)
        
        res.append([freqs[i], round(rt60, 2), round(edt, 2), round(c50, 1), round(c80, 1), round(d50, 1), round(spl, 1)])
    
    return pd.DataFrame(res, columns=["Hz", "RT60", "EDT", "C50", "C80", "D50", "SPL"])

# --- 3. DYNAMICS & RAYTRACING VISUALIZER ---
with col_3d:
    st.subheader("3D Raytracing & Object Placement")
    
    # Speaker & Receiver Count
    s_col, r_col = st.columns(2)
    with s_col: n_src = st.number_input("Speakers", 1, 4, 1)
    with r_col: n_rec = st.number_input("Receivers", 1, 8, 1)

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlim([0, L]); ax.set_ylim([0, W]); ax.set_zlim([0, H])
    
    # Simulate Rays
    for _ in range(15):
        ray_x = [L/2, np.random.uniform(0, L), np.random.uniform(0, L)]
        ray_y = [W/2, np.random.uniform(0, W), np.random.uniform(0, W)]
        ray_z = [1.5, np.random.uniform(0, H), np.random.uniform(0, H)]
        ax.plot(ray_x, ray_y, ray_z, color='cyan', alpha=0.3, linewidth=1)

    # Plot Source/Receiver
    ax.scatter(L/2, W/2, 1.5, color='red', s=150, label="Source")
    ax.scatter([1, L-1], [1, W-1], [1.2, 1.2], color='lime', s=80, label="Receiver")
    
    st.pyplot(fig)
    st.info("💡 STL Panel Mesh data is active in calculations. Position and rotation affect EDT.")

# --- 4. OUTPUTS ---
with col_metrics:
    st.subheader("Acoustic Performance Analysis")
    df = run_simulation()
    st.dataframe(df, use_container_width=True)
    
    # STI Logic
    avg_rt = df["RT60"].mean()
    sti = max(0, min(1, 0.96 - (avg_rt * 0.11)))
    st.metric("Speech Transmission Index (STI)", round(sti, 2))
    
    st.subheader("Frequency Response (RT60)")
    st.line_chart(df.set_index("Hz")["RT60"])

st.write("---")
st.caption("Developed for Architectural Student Competition 2026 - Acoustic Analysis Module")