import requests
import os
from datetime import datetime, timedelta
import pytz
from bs4 import BeautifulSoup

# === GitHub Secrets 讀取 ===
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.getenv('LINE_USER_ID')

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
    raise ValueError("缺少 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_USER_ID")

TAIWAN_TZ = pytz.timezone('Asia/Taipei')
now = datetime.now(TAIWAN_TZ)
today_str = now.strftime('%Y-%m-%d')        # 例如 2026-04-01
today_url = now.strftime('%Y%m%d')          # 例如 20260401

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}

def get_npb_games():
    url = f"https://npb.jp/bis/eng/2026/games/gm{today_url}.html"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 這裡先簡單抓文字內容，之後再細調
        text = soup.get_text()
        games = []
        
        # 簡單關鍵字搜尋（後續會優化）
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if any(team in line for team in ['Giants', 'Tigers', 'Dragons', 'BayStars', 'Swallows', 'Carp', 'Lions', 'Hawks', 'Buffaloes', 'Marines', 'Eagles', 'Fighters']):
                if ':' in line or 'vs' in line.lower():
                    games.append(line.strip())
        
        return games if games else ["目前無法抓取 NPB 賽程（頁面結構可能變動）"]
    except Exception as e:
        return [f"NPB 爬取失敗: {str(e)}"]

def get_cpbl_games():
    # 先用英文版主頁，之後可改成特定日期
    url = "https://en.cpbl.com.tw/schedule"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 簡單取文字（後續會針對表格優化）
        text = soup.get_text()
        games = [line.strip() for line in text.split('\n') if line.strip() and any(k in line for k in ['vs', 'Brothers', 'Monkeys', 'Dragons', 'Guardians', 'Lions', 'Fubon'])]
        
        return games if games else ["目前無法抓取 CPBL 賽程"]
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

# === 主程式 ===
if __name__ == "__main__":
    print(f"執行時間：{now.strftime('%Y-%m-%d %H:%M:%S')} 台灣時間")
    print(f"正在爬取 {today_str} 棒球賽程...")

    npb_games = get_npb_games()
    cpbl_games = get_cpbl_games()

    msg = f"⚾ {today_str} 棒球賽程通知\n\n"

    msg += "【日本職棒 NPB】\n"
    for g in npb_games:
        msg += f"• {g}\n"
    msg += "\n"

    msg += "【中華職棒 CPBL】\n"
    for g in cpbl_games:
        msg += f"• {g}\n"

    if not npb_games and not cpbl_games:
        msg += "今天沒有棒球比賽，或爬取失敗。\n"

    send_to_line(msg.strip())
    print("✅ 已發送棒球通知至 LINE")