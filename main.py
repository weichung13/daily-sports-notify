import requests
import os
from datetime import datetime
import pytz
from bs4 import BeautifulSoup

# === GitHub Secrets 讀取 ===
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.getenv('LINE_USER_ID')

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
    raise ValueError("缺少 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_USER_ID，請確認 GitHub Secrets")

TAIWAN_TZ = pytz.timezone('Asia/Taipei')
now = datetime.now(TAIWAN_TZ)
today_str = now.strftime('%Y-%m-%d')      # 2026-04-01
today_url = now.strftime('%Y%m%d')        # 20260401

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}

def get_npb_games():
    """爬取 NPB 官方英文賽程頁"""
    url = f"https://npb.jp/bis/eng/2026/games/gm{today_url}.html"
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        games = []
        # NPB 頁面常見結構：比賽通常在 <p> 或 <div> 中，包含時間 + 球隊 + 球場
        for item in soup.find_all(['p', 'div', 'li']):
            text = item.get_text().strip()
            if text and any(keyword in text for keyword in [':00', '18:00', '13:00', 'Jingu', 'Dome', 'vs', 'VS']):
                # 清理多餘空白
                clean_text = ' '.join(text.split())
                if len(clean_text) > 10:   # 避免抓到無用短文字
                    games.append(clean_text)

        if not games:
            return ["今日 NPB 無比賽 或 頁面結構變動"]
        return games
    except Exception as e:
        return [f"NPB 爬取失敗: {str(e)}"]

def get_cpbl_games():
    """爬取 CPBL 英文版賽程頁"""
    url = "https://en.cpbl.com.tw/schedule"
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        games = []
        # 尋找包含 vs、時間、隊名的文字
        for item in soup.find_all(['td', 'div', 'p', 'a']):
            text = item.get_text().strip()
            if any(team in text for team in ['Brothers', 'Monkeys', 'Dragons', 'Guardians', 'Lions', 'Hawks', 'U-Lions', 'TSG']) and ('vs' in text.lower() or ':' in text):
                clean_text = ' '.join(text.split())
                games.append(clean_text)

        if not games:
            return ["今日 CPBL 無比賽 或 頁面結構變動"]
        return games[:10]   # 避免抓太多重複
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
    print(f"LINE 發送狀態碼: {resp.status_code}")
    if resp.status_code != 200:
        print("錯誤:", resp.text)

# === 主程式 ===
if __name__ == "__main__":
    print(f"執行時間：{now.strftime('%Y-%m-%d %H:%M:%S')} 台灣時間")
    print(f"正在爬取 {today_str} 的棒球賽程...")

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

    send_to_line(msg.strip())
    print("✅ 已發送棒球通知至 LINE")