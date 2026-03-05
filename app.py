import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import re

# ==========================================
# 1. 網頁基本設定
# ==========================================
st.set_page_config(page_title="朝聖之旅智能導覽", layout="wide")
st.title("🗺️ 歐洲朝聖之路 (Camino de Santiago) 智能導覽")

# ==========================================
# 2. 讀取 AI 生成的 CSV 資料
# ==========================================
@st.cache_data
def load_data():
    try:
        return pd.read_csv("outputs_camino/camino_daily_itinerary.csv")
    except:
        return None

df = load_data()
if df is None:
    st.error("⚠️ 找不到行程資料！請確定已經成功執行 main.py")
    st.stop()

# ==========================================
# 3. Sidebar 控制面板 (左側選單)
# ==========================================
st.sidebar.header("📍 選擇行程")
view_mode = st.sidebar.radio("查看模式", ["🌍 串連全行程 (All Days)", "📅 按日逐日睇 (Daily)"])

selected_day = None
if view_mode == "📅 按日逐日睇 (Daily)":
    selected_day = st.sidebar.selectbox("選擇日數", df['Day'].tolist())

# ==========================================
# 4. 內建座標字典 (保證地圖流暢不卡頓)
# ==========================================
coords_db = {
    "HONG KONG": [22.3080, 113.9185], "HKG": [22.3080, 113.9185],
    "MADRID": [40.4168, -3.7038], "BARCELONA": [41.3851, 2.1734],
    "SANTIAGO": [42.8782, -8.5448], "SARRIA": [42.7758, -7.4116],
    "PORTOMARIN": [42.8077, -7.6158], "PALAS DE REI": [42.8727, -7.8687],
    "MELIDE": [42.9142, -8.0163], "ARZUA": [42.9272, -8.1643],
    "O PEDROUZO": [42.9038, -8.3615], "RUA": [42.9038, -8.3615], 
    "LAVACOLLA": [42.8943, -8.4414], "MONTE DO GOZO": [42.8887, -8.4947],
}

def get_coord(loc_name):
    loc_upper = str(loc_name).upper()
    for key, coord in coords_db.items():
        if key in loc_upper:
            return coord
    return [42.8, -7.8] # 找不到時的預設位置 (西班牙加利西亞)

# ==========================================
# 5. 畫地圖與路線
# ==========================================
m = folium.Map(location=[42.8, -7.8], zoom_start=9)
route_coords = []

# 根據用家選擇，過濾資料
display_df = df[df['Day'] == selected_day] if view_mode == "📅 按日逐日睇 (Daily)" else df

for index, row in display_df.iterrows():
    from_to = str(row['From_To'])
    parts = re.split(r'\s+to\s+|\s*->\s*|\s*-\s*', from_to, flags=re.IGNORECASE)
    
    start_loc = parts[0] if len(parts) > 0 else from_to
    end_loc = parts[1] if len(parts) > 1 else start_loc

    start_c = get_coord(start_loc)
    end_c = get_coord(end_loc)
    
    if view_mode == "🌍 串連全行程 (All Days)":
        route_coords.append(start_c)
        route_coords.append(end_c)
        folium.Marker(start_c, tooltip=start_loc).add_to(m)
    else:
        # 逐日睇：畫起點、終點同連線
        folium.Marker(start_c, popup="起點", tooltip=start_loc, icon=folium.Icon(color='green')).add_to(m)
        folium.Marker(end_c, popup="終點", tooltip=end_loc, icon=folium.Icon(color='red')).add_to(m)
        folium.PolyLine([start_c, end_c], color="blue", weight=5, opacity=0.7).add_to(m)
        m.location = start_c
        m.zoom_start = 11

if view_mode == "🌍 串連全行程 (All Days)" and len(route_coords) > 0:
    folium.PolyLine(route_coords, color="red", weight=3, opacity=0.8).add_to(m)
    if len(route_coords) > 4: # 將鏡頭移去西班牙
        m.location = route_coords[4]

# ==========================================
# 6. 顯示排版 (左地圖，右資料)
# ==========================================
col1, col2 = st.columns([2, 1])

with col1:
    st_folium(m, width=700, height=500)

with col2:
    st.markdown("### 📝 行程明細")
    for index, row in display_df.iterrows():
        with st.expander(f"{row['Day']} : {row['From_To']}", expanded=True):
            st.write(f"**🚶 距離:** {row['Distance']}")
            st.write(f"**🍳 早餐:** {row['Breakfast']}")
            st.write(f"**🐙 晚餐:** {row['Dinner']}")
            st.write(f"**🏨 住宿:** {row['Accommodation']}")
            # 清理 Excel URL 公式，變回真正 Clickable Link
            url_str = str(row.get('Map_Route', ''))
            if "HYPERLINK" in url_str:
                try:
                    url = url_str.split('"')[1]
                    st.markdown(f"[📍 開啟 Google Maps 導航]({url})")
                except: pass

st.markdown("---")
st.markdown("### 📊 完整數據表")
st.dataframe(df)