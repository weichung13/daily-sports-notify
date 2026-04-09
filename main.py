import pdfplumber
import requests
import os
from datetime import datetime
import pytz

# === GitHub Secrets ===
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.getenv('LINE_USER_ID')

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
    raise ValueError("缺少 LINE Secrets")

TAIWAN_TZ = pytz.timezone('Asia/Taipei')
now = datetime.now(TAIWAN_TZ)

today_md = now.strftime('%m/%d')        # 04/09
today_short = now.strftime('%-m/%-d')   # 4/9
today_key = f"{int(now.month)}/{int(now.day)}"  # 4/9

print(f"今天是 {now.strftime('%Y-%m-%d')}，正在抓取 {today_md} 的比賽...")

PDF_DIR = "pdfs"
PDF_FILES = {
    "CPBL": os.path.join(PDF_DIR, "cpbl.pdf"),
    "NPB_CENTRAL": os.path.join(PDF_DIR, "npb_central.pdf"),
    "NPB_PACIFIC": os.path.join(PDF_DIR, "npb_pacific.pdf"),
    "NPB_INTER": os.path.join(PDF_DIR, "npb.pdf")
}

def extract_today_games(pdf_path, league_name):
    if not os.path.exists(pdf_path):
        return [f"{league_name} PDF 不存在"]

    games = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # ==================== CPBL ====================
                    if league_name == "CPBL":
                        if any(d in line for d in [today_md, today_short, today_key]):
                            if any(team in line for team in ['雄鷹', '桃猿', '兄弟', '統一', '富邦', '味全', '台鋼']):
                                clean = line.split('先發')[0].strip() if '先發' in line else line
                                clean = ' '.join(clean.split())
                                if len(clean) > 10:
                                    games.append(clean)

                    # ==================== NPB (中央 / 太平洋 / 交流賽) ====================
                    else:
                        # 處理「4/1 下一行是 2」這種跨行格式
                        if any(d in line for d in [today_md, today_short, today_key, f" {int(now.day)} "]):
                            if any(k in line for k in ['18:', '14:', '13:', '東京ドーム', '神宮', '甲子園', '横浜', 'マツダ', 'バンテリンドーム']):
                                clean = ' '.join(line.split())
                                if len(clean) > 15:
                                    games.append(clean)

        return games if games else [f"今天沒有 {league_name} 比賽"]
    except Exception as e:
        return [f"{league_name} 解析失敗: {str(e)}"]

def send_to_line(message):
    if len(message) > 3800:
        message = message[:3750] + "\n...(已截斷)"

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
    cpbl = extract_today_games(PDF_FILES["CPBL"], "CPBL")
    central = extract_today_games(PDF_FILES["NPB_CENTRAL"], "NPB 中央")
    pacific = extract_today_games(PDF_FILES["NPB_PACIFIC"], "NPB 太平洋")
    inter = extract_today_games(PDF_FILES["NPB_INTER"], "NPB 交流賽")

    msg = f"⚾ {now.strftime('%Y-%m-%d')} 棒球賽程\n\n"

    msg += "【NPB 中央聯盟】\n" + "\n".join([f"• {g}" for g in central]) + "\n\n"
    msg += "【NPB 太平洋聯盟】\n" + "\n".join([f"• {g}" for g in pacific]) + "\n\n"
    msg += "【NPB 交流賽】\n" + "\n".join([f"• {g}" for g in inter]) + "\n\n"
    msg += "【CPBL 中華職棒】\n" + "\n".join([f"• {g}" for g in cpbl])

    send_to_line(msg)
    print("程式執行結束")