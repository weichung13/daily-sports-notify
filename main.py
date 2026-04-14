import requests
import os
from datetime import datetime, timedelta
import pytz
import google.generativeai as genai

# === GitHub Secrets ===
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.getenv('LINE_USER_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID or not GEMINI_API_KEY:
    raise ValueError("缺少 LINE 或 Gemini API Key，請確認 GitHub Secrets")

genai.configure(api_key=GEMINI_API_KEY)

TAIWAN_TZ = pytz.timezone('Asia/Taipei')
now = datetime.now(TAIWAN_TZ)
today = now.strftime('%Y-%m-%d')
tomorrow = (now + timedelta(days=1)).strftime('%Y-%m-%d')
today_display = now.strftime('%m月%d日')

print(f"今天是 {today}，正在請 Gemini 查詢賽程...")

def ask_gemini():
    prompt = f"""
現在是台灣時間 {today} 早上 09:00。

請根據你的知識，告訴我以下賽程：

**棒球賽程（中華職棒 CPBL 和日本職棒 NPB）：**
- 只顯示 {today} 的比賽

**足球賽程（五大聯賽、歐冠、杯賽等）：**
- 顯示 {today} 的比賽
- 以及 {tomorrow} 凌晨 0:00-04:00 台灣時間的比賽（也就是今晚到明天凌晨歐洲時間的比賽）

格式如下（如果沒有比賽就寫「沒有比賽」）：

【NPB 日本職棒】
• 時間 主隊 vs 客隊

【CPBL 中華職棒】
• 時間 主隊 vs 客隊

【五大聯賽＋歐冠＋杯賽】
• 時間 主隊 vs 客隊 (聯賽名稱)

足球部分要包含 {tomorrow} 凌晨 0:00-04:00 的比賽。
"""

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')   # 使用目前最穩定的 model
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini 錯誤: {str(e)}")
        return "Gemini 查詢失敗，請稍後再試。"

def send_to_line(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    try:
        resp = requests.post(url, headers=headers, json=data)
        print(f"LINE 發送狀態: {resp.status_code}")
    except Exception as e:
        print(f"發送失敗: {str(e)}")

if __name__ == "__main__":
    gemini_reply = ask_gemini()

    msg = f"⚾ {today_display} 賽程\n"
    msg += "=" * 28 + "\n\n"
    msg += gemini_reply

    send_to_line(msg)
    print("程式執行結束")