import requests
import os
from datetime import datetime
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

print(f"今天是 {today}，正在請 Gemini 查詢賽程...")

def ask_gemini():
    prompt = f"""
今天是 {today}（台灣時間）。

請用以下格式告訴我今天的棒球和足球賽程（如果沒有比賽就寫「今天沒有比賽」）：

【NPB 日本職棒】
• 時間 主隊 vs 客隊

【CPBL 中華職棒】
• 時間 主隊 vs 客隊

【五大聯賽＋歐冠＋國家盃賽】
• 時間 主隊 vs 客隊

只回覆今天的比賽，不要回覆其他日期。
"""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')   # 使用較穩定的 1.5-flash
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini 呼叫失敗: {str(e)}")
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

    msg = f"⚾ {today} 棒球＆足球賽程\n\n"
    msg += gemini_reply

    send_to_line(msg)
    print("程式執行結束")