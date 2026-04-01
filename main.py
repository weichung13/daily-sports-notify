import requests
import os
from datetime import datetime
import pytz
from bs4 import BeautifulSoup

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.getenv('LINE_USER_ID')

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
    raise ValueError("缺少 LINE Secrets")

TAIWAN_TZ = pytz.timezone('Asia/Taipei')
now = datetime.now(TAIWAN_TZ)
today_str = now.strftime('%Y-%m-%d')
today_url = now.strftime('%Y%m%d')

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}

def get_npb_games():
    url = f"https://npb.jp/bis/eng/2026/games/gm{today_url}.html"
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        games = []
        # 針對 NPB 頁面結構優化
        for text in soup.stripped_strings:
            t = text.strip()
            if any(time in t for time in [':00', '18:00', '13:00', '14:00']) and any(stadium in t for stadium in ['Jingu', 'Dome', 'FIELD', 'Mobile', 'Belluna']):
                games.append(t)
        return games if games else ["今天沒有 NPB 比賽"]
    except Exception as e:
        return [f"NPB 爬取失敗: {str(e)}"]

def get_cpbl_games():
    url = "https://en.cpbl.com.tw/schedule"
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        games = []
        for text in soup.stripped_strings:
            t = text.strip()
            if ('VS.' in t or 'vs' in t.lower()) and any(team in t for team in ['Brothers', 'Monkeys', 'Dragons', 'Guardians', 'Lions', 'Hawks', 'U-Lions']):
                games.append(t)
        return games[:8] if games else ["今天沒有 CPBL 比賽"]
    except Exception as e:
        return [f"CPBL 爬取失敗: {str(e)}"]

def send_to_line(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers_line = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    resp = requests.post(url, headers=headers_line, json=data)
    print(f"LINE 發送狀態: {resp.status_code}")

if __name__ == "__main__":
    print(f"執行時間：{now.strftime('%Y-%m-%d %H:%M:%S')}")

    npb = get_npb_games()
    cpbl = get_cpbl_games()

    msg = f"⚾ {today_str} 棒球賽程\n\n"
    msg += "【NPB 日本職棒】\n" + "\n".join([f"• {g}" for g in npb]) + "\n\n"
    msg += "【CPBL 中華職棒】\n" + "\n".join([f"• {g}" for g in cpbl])

    send_to_line(msg)
    print("✅ 通知已發送")