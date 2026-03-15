import streamlit as st
import numpy as np
import pandas as pd
import xgboost as xgb
from tensorflow.keras.models import load_model
import json
import time
import os
from datetime import datetime
import requests
import plotly.graph_objects as go

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1482148980325351444/G0Yjw7djDHhDc9X-mVswsReMHnurxTMWEKgF1X-aDJ5PF3aoaYqS9SB4CQ9cgao8Xtmt"
ABUSE_IPDB_KEY = "0d200301cebc542d31c127b835b0ce725d1e307dad6903bd58a669df0497f5f87dfd74503d6034ee"

# Fast translator so the map understands the API country codes
ISO2_TO_ISO3 = {
    'US': 'USA', 'GB': 'GBR', 'DE': 'DEU', 'LT': 'LTU', 'PA': 'PAN',
    'CN': 'CHN', 'RU': 'RUS', 'BR': 'BRA', 'IN': 'IND', 'FR': 'FRA',
    'CA': 'CAN', 'JP': 'JPN', 'KR': 'KOR', 'IT': 'ITA', 'ES': 'ESP',
    'NL': 'NLD', 'UA': 'UKR', 'VN': 'VNM', 'TR': 'TUR', 'IR': 'IRN'
}

# --- DISCORD ALERT ENGINE ---
def fire_discord_alert(ip, score, features):
    if not features:
        causes = "Unknown XAI Causes"
    else:
        causes = "\n".join([f"• {f[0]} (Deviation: {f[1]:.2f})" for f in features])
    
    payload = {
        "content": "**CRITICAL SECURITY ALERT: ZERO-DAY DETECTED**",
        "embeds": [{
            "title": "Sentinel-AI Intrusion Detection System",
            "description": "The Deep Autoencoder has blocked a highly anomalous network packet.",
            "color": 15158332, 
            "fields": [
                {"name": "Targeted IP Address", "value": f"`{ip}`", "inline": True},
                {"name": "AI Anomaly Score", "value": f"`{score:.4f}`", "inline": True},
                {"name": "XAI Root Causes", "value": causes[:1000], "inline": False}
            ],
            "footer": {"text": "System: Hybrid XGBoost + Autoencoder Framework"}
        }]
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except Exception:
        pass

# --- PHASE 4: THREAT INTEL ENGINE ---
def check_threat_intel(ip_address):
    if ip_address in st.session_state['threat_cache']:
        return st.session_state['threat_cache'][ip_address] + (True,)
        
    url = "https://api.abuseipdb.com/api/v2/check"
    querystring = {'ipAddress': ip_address, 'maxAgeInDays': '90'}
    headers = {'Accept': 'application/json', 'Key': ABUSE_IPDB_KEY}
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()['data']
            st.session_state['threat_cache'][ip_address] = (data['abuseConfidenceScore'], data['totalReports'], data['countryCode'])
            return data['abuseConfidenceScore'], data['totalReports'], data['countryCode'], False
    except Exception:
        pass
    return None, None, None, False

# --- 1. PAGE CONFIGURATION & ENTERPRISE CSS INJECTION ---
st.set_page_config(page_title="Sentinel-AI Platform", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #94A3B8; font-family: 'Inter', sans-serif; }
    header[data-testid="stHeader"] {background-color: transparent;}
    .stAppDeployButton {display: none;}
    footer {display: none;}
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; max-width: 95% !important; }
    h1, h2, h3 { color: #F8FAFC !important; font-weight: 500 !important; letter-spacing: -0.02em; }
    h1 { font-size: 1.8rem !important; margin-bottom: 0.2rem !important; }
    div[data-testid="metric-container"] { background-color: #161822; border: 1px solid #232533; padding: 24px 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.4); display: flex; flex-direction: column; justify-content: center; }
    div[data-testid="metric-container"] > div { align-items: flex-start !important; }
    div[data-testid="metric-container"] label { color: #94A3B8 !important; font-size: 0.85rem !important; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #F8FAFC !important; font-size: 1.8rem !important; font-weight: 600 !important; }
    [data-testid="stVerticalBlock"] > div > div > div[data-testid="stVerticalBlock"] { background-color: #161822; border: 1px solid #232533; border-radius: 12px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    [data-testid="stSidebar"] { background-color: #0E1117; border-right: 1px solid #1F2330; }
    [data-testid="stSidebar"] hr { border-color: #1F2330; }
    .stAlert { border-radius: 8px !important; border: 1px solid #232533 !important; color: #F8FAFC !important; }
    div[data-testid="stAlert"]:has(> div > div > div:contains("ACTION TAKEN")) { background-color: rgba(239, 68, 68, 0.1) !important; border: 1px solid #EF4444 !important; }
    div[data-testid="stAlert"]:has(> div > div > div:contains("CONNECTION AUTHORIZED")) { background-color: rgba(16, 185, 129, 0.05) !important; border: 1px solid #10B981 !important; }
    .st-bb { background-color: #232533; }
    .st-bc { background-color: #8B5CF6; } 
    .stMarkdown p { color: #94A3B8; font-size: 0.95rem; }
    code { background-color: #0B0E14 !important; color: #38BDF8 !important; border: 1px solid #1F2330 !important; }
    </style>
""", unsafe_allow_html=True)

# --- HEADER LAYOUT ---
col_title, col_view = st.columns([4, 1])
with col_title:
    st.markdown("<h1>Sentinel-AI Platform</h1>", unsafe_allow_html=True)
    st.markdown("Enterprise Hybrid IDS: Distributed Autoencoder & XGBoost Analysis")
with col_view:
    st.markdown("<div style='text-align: right; margin-top: 15px; color: #8B5CF6; font-size: 0.9rem; font-weight: 600;'>SYSTEM ACTIVE</div>", unsafe_allow_html=True)

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# --- 2. INITIALIZE SESSION STATE ---
if 'blocked_ips' not in st.session_state: st.session_state['blocked_ips'] = []
if 'mse_history' not in st.session_state: st.session_state['mse_history'] = []
if 'threat_cache' not in st.session_state: st.session_state['threat_cache'] = {}          
if 'threshold_history' not in st.session_state: st.session_state['threshold_history'] = []     
if 'baseline_history' not in st.session_state: st.session_state['baseline_history'] = [] 
if 'total_scanned' not in st.session_state: st.session_state['total_scanned'] = 0
if 'total_flagged' not in st.session_state: st.session_state['total_flagged'] = 0
if 'threat_map_data' not in st.session_state: st.session_state['threat_map_data'] = {} 
if 'packet_index' not in st.session_state: st.session_state['packet_index'] = 0

# --- 3. LOAD MODELS & DATA ---
@st.cache_resource
def load_system():
    xgb_super = xgb.XGBClassifier()
    xgb_super.load_model("hybrid_xgb_model.json")
    autoencoder = load_model("deep_autoencoder.h5", compile=False)
    with open("deployment_config.json", "r") as f:
        config = json.load(f)
    return xgb_super, autoencoder, config

@st.cache_data
def load_sample_data():
    df = pd.read_csv("sample_traffic.csv")
    labels = pd.read_csv("sample_labels.csv").values.flatten()
    return df.values, labels

xgb_super, autoencoder, config = load_system()
sample_data, sample_labels = load_sample_data() 
threshold = config["anomaly_threshold"]

current_dir = os.path.dirname(os.path.abspath(__file__))
feature_file_path = os.path.join(current_dir, "kdd_feature_names.csv")
if os.path.exists(feature_file_path):
    df_names = pd.read_csv(feature_file_path, header=None)
    feature_names = df_names.iloc[:, 0].astype(str).values.tolist()
else:
    feature_names = [f"Feature_{i}" for i in range(129)]

# --- 4. THE SIDEBAR ---
st.sidebar.markdown("### System Controls")
st.sidebar.markdown(f"**Baseline Floor:** `{threshold:.4f}`")
st.sidebar.markdown("<br>", unsafe_allow_html=True)

# 1. Action buttons pinned to the top!
auto_pilot = st.sidebar.toggle("Enable Live Stream (Auto-Pilot)") 
manual_intercept = st.sidebar.button("Intercept Packet", type="primary", use_container_width=True)

st.sidebar.markdown("---")

# 2. Logs neatly tucked into a collapsible expander!
with st.sidebar.expander("🚨 View Active Intercept Logs", expanded=False):
    if len(st.session_state['blocked_ips']) == 0:
        st.info("Network stream secure. No threats detected yet.")
    else:
        for block in reversed(st.session_state['blocked_ips']):
            st.error(f"**Target IP:** `{block['ip']}`\n\n**Class:** {block['reason']}")

with st.sidebar.expander("AI Telemetry & Live Math"):
    if len(st.session_state['baseline_history']) > 5:
        current_mu = np.mean(st.session_state['baseline_history'][-50:])
        current_std = np.std(st.session_state['baseline_history'][-50:])
        raw_calc = current_mu + (3 * current_std)
        st.code(f"μ (Mean): {current_mu:.6f}\nσ (Std):  {current_std:.6f}")
        st.metric(label="Calculated Dynamic Score", value=f"{raw_calc:.6f}")
        st.caption(f"Floor limit: {threshold:.4f}")
    else:
        st.info("Gathering baseline telemetry...")

# --- 5. MAIN DASHBOARD ---
# 3. Using the new pinned button variable
if manual_intercept or auto_pilot:
    
    with st.spinner("Live monitoring active..." if auto_pilot else "Analyzing packet stream..."):
        
        # --- DATA PREP (WITH SEQUENTIAL TRACKER) ---
        idx = st.session_state['packet_index']
        packet = np.array(sample_data[idx]).reshape(1, -1).astype(np.float32)
        actual_label = "Attack" if sample_labels[idx] == 1 else "Normal"
        
        # Increment index for the next run so it doesn't repeat
        st.session_state['packet_index'] = (st.session_state['packet_index'] + 1) % len(sample_data)
        
        if actual_label == "Attack":
            known_bad_ips = ["185.220.101.54", "194.165.16.130", "141.98.10.12"]
            source_ip = np.random.choice(known_bad_ips)
        else:
            source_ip = f"{np.random.randint(10, 200)}.{np.random.randint(0, 255)}.{np.random.randint(0, 255)}.{np.random.randint(1, 254)}"
        
        # --- MODEL INFERENCE ---
        xgb_pred = xgb_super.predict(packet)[0]
        raw_packet = packet[:, :129]
        reconstruction = autoencoder(raw_packet, training=False).numpy()
        mse = np.mean(np.power(raw_packet - reconstruction, 2))
        
        # --- DYNAMIC THRESHOLD LOGIC ---
        if len(st.session_state['baseline_history']) > 5:
            recent_safe_traffic = st.session_state['baseline_history'][-50:]
            moving_avg = np.mean(recent_safe_traffic)
            moving_std = np.std(recent_safe_traffic)
            dynamic_threshold = moving_avg + (3 * moving_std)
            active_threshold = max(dynamic_threshold, threshold)
        else:
            active_threshold = threshold
            
        ae_pred = 1 if mse > active_threshold else 0
        final_verdict = int(xgb_pred or ae_pred)

        # --- UPDATE HISTORY & COUNTERS ---
        st.session_state['total_scanned'] += 1
        if final_verdict == 1:
            st.session_state['total_flagged'] += 1

        st.session_state['mse_history'].append(mse)
        st.session_state['threshold_history'].append(active_threshold)
        
        if final_verdict == 0:
            st.session_state['baseline_history'].append(mse)
            
        for history_list in ['mse_history', 'threshold_history', 'baseline_history']:
            if len(st.session_state[history_list]) > 50:
                st.session_state[history_list].pop(0)
        
        # --- XAI LOGIC ---
        feature_errors = np.power(raw_packet[0] - reconstruction[0], 2)
        top_3_indices = np.argsort(feature_errors)[-3:][::-1]
        top_3_features = [(feature_names[i] if i < len(feature_names) else f"Feature_{i}", feature_errors[i]) for i in top_3_indices]

        # ==========================================
        # --- TOP KPI ROW ---
        # ==========================================
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1: st.metric(label="Target Source IP", value=source_ip)
        with kpi2: st.metric(label="XGBoost Signature", value="MALICIOUS" if xgb_pred else "CLEAN")
        with kpi3: st.metric(label="Autoencoder MSE", value=f"{mse:.4f}")
        with kpi4: st.metric(label="Ground Truth Status", value=actual_label.upper())

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        # ==========================================
        # --- MIDDLE VISUALIZATION ROW ---
        # ==========================================
        col_donut, col_line = st.columns([1, 2.5])
        
        with col_donut:
            with st.container():
                st.markdown("### Traffic Distribution")
                st.markdown("Ratio of Clean vs. Malicious Packets")
                
                clean_count = st.session_state['total_scanned'] - st.session_state['total_flagged']
                flagged_count = st.session_state['total_flagged']
                
                fig = go.Figure(data=[go.Pie(
                    labels=['Authorized', 'Blocked'], values=[clean_count, flagged_count], hole=.75,
                    marker_colors=['#3B82F6', '#EF4444'], textinfo='none', hoverinfo='label+value'
                )])
                fig.update_layout(
                    showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(color="#94A3B8")),
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=10, r=10), height=280,
                    annotations=[dict(text=f"{st.session_state['total_scanned']}", x=0.5, y=0.5, font_size=32, showarrow=False, font_color="#F8FAFC")]
                )
                st.plotly_chart(fig, use_container_width=True)

        with col_line:
            with st.container():
                st.markdown("### Live Network Telemetry")
                st.markdown("Autoencoder MSE Deviation vs. Dynamic Z-Score Threshold")
                min_length = min(len(st.session_state['mse_history']), len(st.session_state['threshold_history']))
                safe_mse = st.session_state['mse_history'][-min_length:] if min_length > 0 else []
                safe_threshold = st.session_state['threshold_history'][-min_length:] if min_length > 0 else []

                chart_data = pd.DataFrame({"Anomaly Score (MSE)": safe_mse, "Dynamic Threshold": safe_threshold})
                st.line_chart(chart_data, color=["#8B5CF6", "#EF4444"], height=280)

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        # ==========================================
        # --- DEEP DIVE COLUMNS (OSINT + XAI) ---
        # ==========================================
        col_osint, col_xai = st.columns([1.5, 1])
        
        # Get OSINT Data early so we can use the country for the Map!
        confidence_score, total_reports, country_code, is_cached = check_threat_intel(source_ip)
        
        with col_osint:
            with st.container():
                st.markdown("### Global Threat Intelligence (OSINT)")
                if confidence_score is not None:
                    cache_badge = "[MEMORY CACHE]" if is_cached else "[LIVE API]"
                    if confidence_score > 0:
                        st.warning(f"**THREAT IDENTIFIED:** IP originates from **{country_code}**. Confidence Score: **{confidence_score}%** across **{total_reports}** reports. {cache_badge}")
                    else:
                        st.info(f"**NETWORK CLEAR:** IP ({country_code}) has no recent reports of malicious activity. {cache_badge}")
                else:
                    st.caption("OSINT verification bypassed or unavailable.")

        with col_xai:
            with st.container():
                st.markdown("### Explainable AI (XAI)")
                st.write("Top anomalous network features:")
                for f_name, f_err in top_3_features:
                    st.markdown(f"- **`{f_name}`** (Deviation: {f_err:.4f})")

        # ==========================================
        # --- THE GLOBAL THREAT MAP ---
        # ==========================================
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        with st.container():
            st.markdown("### Global Threat Origin Map")
            st.markdown("Live geolocation tracking of intercepted network attacks.")
            
            # Map Logic: Update tracker if a threat is detected
            if final_verdict == 1 and country_code:
                iso3 = ISO2_TO_ISO3.get(country_code, "USA") # Fallback to USA if code isn't in our dictionary
                st.session_state['threat_map_data'][iso3] = st.session_state['threat_map_data'].get(iso3, 0) + 1

            # Render the Map
            if st.session_state['threat_map_data']:
                df_map = pd.DataFrame(list(st.session_state['threat_map_data'].items()), columns=['Country', 'Threats'])
                
                fig_map = go.Figure(data=go.Scattergeo(
                    locations=df_map['Country'],
                    locationmode='ISO-3',
                    marker=dict(
                        size=df_map['Threats'] * 7 + 12, # Dots grow larger with more attacks
                        color='rgba(239, 68, 68, 0.6)',  # Glowing translucent red
                        line=dict(width=2, color='#EF4444'), # Solid red border
                        sizemode='diameter'
                    ),
                    text=df_map['Country'] + ": " + df_map['Threats'].astype(str) + " blocks",
                    hoverinfo="text"
                ))
                
                fig_map.update_layout(
                    geo=dict(
                        bgcolor='rgba(0,0,0,0)',
                        landcolor='#161822',    # Dark indigo lands
                        oceancolor='#0B0E14',   # Deep navy oceans
                        showocean=True,
                        lakecolor='#0B0E14',
                        coastlinecolor='#232533',
                        showcoastlines=True,
                        showframe=False,
                        projection_type='natural earth'
                    ),
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.info("Awaiting threat data to map geographical origins...")

        # ==========================================
        # --- FINAL VERDICT BANNER ---
        # ==========================================
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        if final_verdict == 1:
            st.error("ACTION TAKEN: THREAT DETECTED & CONNECTION TERMINATED")
            
            if xgb_pred and ae_pred: exact_reason = "Known Attack + High Anomaly"
            elif xgb_pred: exact_reason = "Known Signature (XGBoost)"
            else: exact_reason = "Zero-Day Anomaly (Autoencoder)"

            st.session_state['blocked_ips'].append({
                "ip": source_ip, 
                "time": datetime.now().strftime("%H:%M:%S"), 
                "reason": exact_reason
            })
            
            if ae_pred == 1:
                fire_discord_alert(source_ip, mse, top_3_features)
                
        else:
            st.success("STATUS: CONNECTION AUTHORIZED")
else:
    st.info("System Standby. Initialize packet interception or enable Live Stream.")

# --- CONTINUOUS LOG TAILING LOOP ---
if auto_pilot:
    time.sleep(1.5) 
    st.rerun()