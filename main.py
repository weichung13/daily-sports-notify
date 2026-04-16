import requests
import os
from datetime import datetime, timedelta
import pytz
from google import genai

# === GitHub Secrets ===
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.getenv('LINE_USER_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID or not GEMINI_API_KEY:
    raise ValueError("缺少 LINE 或 Gemini API Key，請確認 GitHub Secrets")

# 初始化新的 google-genai Client
client = genai.Client(api_key=GEMINI_API_KEY)

TAIWAN_TZ = pytz.timezone('Asia/Taipei')
now = datetime.now(TAIWAN_TZ)
today = now.strftime('%Y-%m-%d')
tomorrow = (now + timedelta(days=1)).strftime('%Y-%m-%d')
today_display = now.strftime('%m月%d日')

print(f"今天是 {today}，正在請 Gemini 查詢賽程...")

def ask_gemini():
    prompt = f"""
台灣時間今天是 {today}。

請根據你的知識，查詢這些賽程，並嚴格按照以下規則：

**重要：日期限制**
- CPBL 和 NPB：只回覆 {today} 這一天的比賽時間表
- 足球：回覆 {today} 的比賽，以及 {tomorrow} 凌晨 00:00-04:00 的比賽

**回覆格式：**

【CPBL 中華職棒】{today}
• 時間 主隊 vs 客隊
（如果 {today} 沒有比賽，寫「沒有比賽」）

【NPB 日本職棒】{today}
• 時間 主隊 vs 客隊
（如果 {today} 沒有比賽，寫「沒有比賽」）

【足球五大聯賽＋歐冠＋杯賽】
{today} 的比賽：
• 時間 主隊 vs 客隊 (聯賽)

{tomorrow} 凌晨 00:00-04:00 的比賽：
• 時間 主隊 vs 客隊 (聯賽)

（如果某天沒有比賽，寫「沒有比賽」）

**注意：**
- 不要混淆日期
- 嚴格按照上面的日期篩選
- 如果不確定日期，寫「日期不確定」而不要亂猜
"""

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini 錯誤: {str(e)}")
        # 如果出錯，嘗試用更輕量的模型
        try:
            print("嘗試用 gemini-1.5-flash...")
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            return response.text.strip()
        except Exception as e2:
            print(f"備選模型也失敗: {str(e2)}")
            return "查詢失敗，請稍後再試。"

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