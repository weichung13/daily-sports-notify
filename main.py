import pdfplumber
import requests
import os
from datetime import datetime
import pytz

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.getenv('LINE_USER_ID')

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
    raise ValueError("缺少 LINE Secrets")

TAIWAN_TZ = pytz.timezone('Asia/Taipei')
now = datetime.now(TAIWAN_TZ)
today_str = now.strftime('%Y-%m-%d')
today_md = now.strftime('%m/%d')      # 04/01
today_md2 = now.strftime('%-m/%-d')   # 4/1

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
                for line in text.split('\n'):
                    line = line.strip()
                    if not line:
                        continue

                    # CPBL：只保留對戰部分
                    if league_name == "CPBL":
                        if (today_md in line or today_md2 in line or "4/01" in line):
                            # 簡單清理，只留隊伍 vs 隊伍
                            if any(team in line for team in ['雄鷹', '桃猿', '兄弟', '統一', '富邦', '味全', '台鋼']):
                                # 取出對戰部分
                                clean = line.split('先發')[0].strip() if '先發' in line else line
                                clean = ' '.join(clean.split())
                                games.append(clean)

                    # NPB
                    else:
                        if any(k in line for k in ['18:', '14:', '13:']) and any(k in line for k in ['－', 'VS']):
                            clean = ' '.join(line.split())
                            games.append(clean[:150])   # 限制長度

        return games if games else [f"今天沒有 {league_name} 比賽"]
    except Exception as e:
        return [f"{league_name} 解析失敗"]

def send_to_line(message):
    if len(message) > 3800:
        message = message[:3750] + "\n...訊息過長已截斷"

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
        if resp.status_code != 200:
            print("錯誤回應:", resp.text)
    except Exception as e:
        print(f"發送失敗: {str(e)}")

if __name__ == "__main__":
    print(f"執行時間：{now.strftime('%Y-%m-%d %H:%M:%S')}")

    cpbl = extract_today_games(PDF_FILES["CPBL"], "CPBL")
    central = extract_today_games(PDF_FILES["NPB_CENTRAL"], "NPB 中央")
    pacific = extract_today_games(PDF_FILES["NPB_PACIFIC"], "NPB 太平洋")
    inter = extract_today_games(PDF_FILES["NPB_INTER"], "NPB 交流賽")

    msg = f"⚾ {today_str} 棒球賽程\n\n"

    msg += "【NPB 中央聯盟】\n" + "\n".join([f"• {g}" for g in central]) + "\n\n"
    msg += "【NPB 太平洋聯盟】\n" + "\n".join([f"• {g}" for g in pacific]) + "\n\n"
    msg += "【NPB 交流賽】\n" + "\n".join([f"• {g}" for g in inter]) + "\n\n"
    msg += "【CPBL 中華職棒】\n" + "\n".join([f"• {g}" for g in cpbl])

    print(f"準備發送訊息長度: {len(msg)} 字元")
    send_to_line(msg)
    print("程式執行結束")