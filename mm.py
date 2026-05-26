import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# ==========================================
# ⚙️ 系統核心設定與資料處理
# ==========================================
st.set_page_config(layout="wide", page_title="雲端同步 Trello 看板")

def init_connection():
    """建立與 Google Sheets 的安全連接"""
    return st.connection("gsheets", type=GSheetsConnection)

def load_data(conn):
    """讀取雲端資料並進行標準化清洗"""
    try:
        df = conn.read(worksheet="Tasks", ttl=0) # ttl 設為 0 確保即時同步
        # 強制將欄位名稱轉為去空白的小寫，防止雲端表頭格式隱形出錯
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"❌ 雲端資料讀取失敗，請檢查連線或工作表名稱。錯誤訊息: {e}")
        return pd.DataFrame(columns=["title", "status", "owner"])

def render_task_card(title, owner, status):
    """動態渲染單個 Trello 卡片元件"""
    with st.container(border=True):
        if status == "Done":
            st.write(f"~~**✅ {title}**~~")  # 已完成任務加上刪除線
        elif status == "In Progress":
            st.write(f"**⚡ {title}**")
        else:
            st.write(f"**📌 {title}**")
        st.caption(f"👤 負責人: {owner}")

# ==========================================
# 📊 主程式邏輯開始
# ==========================================
conn = init_connection()
df = load_data(conn)

# 標題與頁首標註
st.title("📋 GitHub 雲端同步 Trello 看板")
st.caption("授權標註：edit by 闕河正 | 終極重整優化版")

# ------------------------------------------
# ➕ 區塊一：指派新任務表單
# ------------------------------------------
st.write("### ➕ 指派新任務")
with st.form("task_input_form", clear_on_submit=True):
    c_title, c_status, c_owner = st.columns([2, 1, 1])
    with c_title:
        new_title = st.text_input("📝 任務名稱", placeholder="輸入任務名稱...")
    with c_status:
        new_status = st.selectbox("🚦 狀態", ["To Do", "In Progress", "Done"])
    with c_owner:
        new_owner = st.text_input("👤 負責人", placeholder="誰來負責...")
    
    submit_btn = st.form_submit_button("確認指派並同步雲端")

# 表單提交邏輯與防呆
if submit_btn:
    cleaned_title = new_title.strip()
    cleaned_owner = new_owner.strip()
    
    if cleaned_title and cleaned_owner:
        # 建立結構對齊的新資料列
        new_row = pd.DataFrame([{
            "title": cleaned_title,
            "status": new_status,
            "owner": cleaned_owner
        }])
        
        # 安全拼接並上傳雲端
        updated_df = pd.concat([df, new_row], ignore_index=True)
        conn.update(worksheet="Tasks", data=updated_df)
        
        st.success("🎉 資料已跨越限制，成功同步寫入 Google 試算表！")
        st.rerun()
    else:
        st.error("⚠️ 欄位防呆：任務名稱與負責人不能為空或純空白鍵！")

st.write("---")

# ------------------------------------------
# 🗂️ 區塊二：Trello 三縱欄畫布動態監控
# ------------------------------------------
st.write("### 🗂️ 看板動態狀態監控")
trello_col1, trello_col2, trello_col3 = st.columns(3)

# 定義看板三欄位的設定參數 (狀態Key, 欄位元件, 標題HTML)
columns_config = [
    ("To Do", trello_col1, "<span style='color:red'>🔴 To Do (待辦)</span>"),
    ("In Progress", trello_col2, "<span style='color:orange'>🟡 In Progress (執行中)</span>"),
    ("Done", trello_col3, "<span style='color:green'>🟢 Done (已完成)</span>")
]

# 運用迴圈自動化渲染三個縱欄，消滅重複代碼（DRY原則）
for status_key, col_obj, header_html in columns_config:
    with col_obj:
        st.markdown(f"### {header_html}", unsafe_allow_html=True)
        filtered_list = df[df["status"] == status_key]
        
        if not filtered_list.empty:
            for idx, row in filtered_list.iterrows():
                render_task_card(row["title"], row["owner"], status_key)
        else:
            st.info(f"暫無 {status_key} 任務")
