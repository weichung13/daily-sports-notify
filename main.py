import pdfplumber
import requests
import os
from datetime import datetime
import pytz

# === GitHub Secrets ===
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.getenv('LINE_USER_ID')

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
    raise ValueError("缺少 LINE Secrets，請確認 GitHub Secrets")

TAIWAN_TZ = pytz.timezone('Asia/Taipei')
now = datetime.now(TAIWAN_TZ)
today_str = now.strftime('%Y-%m-%d')        # 2026-04-01
today_md = now.strftime('%m/%d')            # 04/01
today_md2 = now.strftime('%-m/%-d')         # 4/1   (macOS/Linux 格式)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# PDF 檔案路徑
PDF_DIR = "pdfs"
PDF_FILES = {
    "CPBL": os.path.join(PDF_DIR, "cpbl.pdf"),
    "NPB_CENTRAL": os.path.join(PDF_DIR, "npb_central.pdf"),
    "NPB_PACIFIC": os.path.join(PDF_DIR, "npb_pacific.pdf"),
    "NPB_INTER": os.path.join(PDF_DIR, "npb.pdf")
}

def extract_today_games(pdf_path, league_name):
    if not os.path.exists(pdf_path):
        return [f"{league_name} PDF 檔案不存在"]

    games = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # CPBL 判斷 (4/01 (三)、4/1 等格式)
                    if league_name == "CPBL":
                        if (today_md in line or today_md2 in line or "4/01" in line) and any(k in line for k in ['VS', 'vs', '先發', '雄鷹', '桃猿', '兄弟', '統一', '富邦', '味全', '台鋼']):
                            clean_line = ' '.join(line.split())
                            games.append(clean_line)

                    # NPB 判斷
                    else:
                        if any(k in line for k in ['18:', '14:', '13:', '東京ドーム', '神宮', '甲子園', '横浜', 'マツダ']) and any(k in line for k in ['－', 'VS', 'vs']):
                            clean_line = ' '.join(line.split())
                            games.append(clean_line)

        return games if games else [f"今天沒有 {league_name} 比賽"]
    except Exception as e:
        return [f"{league_name} PDF 解析失敗: {str(e)}"]

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
    try:
        resp = requests.post(url, headers=headers_line, json=data)
        print(f"LINE 發送狀態: {resp.status_code}")
    except Exception as e:
        print(f"發送失敗: {str(e)}")

# === 主程式 ===
if __name__ == "__main__":
    print(f"執行時間：{now.strftime('%Y-%m-%d %H:%M:%S')} 台灣時間")
    print(f"正在從 PDF 讀取 {today_str} 的賽程...")

    cpbl_games = extract_today_games(PDF_FILES["CPBL"], "CPBL")
    central_games = extract_today_games(PDF_FILES["NPB_CENTRAL"], "NPB 中央聯盟")
    pacific_games = extract_today_games(PDF_FILES["NPB_PACIFIC"], "NPB 太平洋聯盟")
    inter_games = extract_today_games(PDF_FILES["NPB_INTER"], "NPB 交流賽")

    msg = f"⚾ {today_str} 棒球賽程通知\n\n"

    msg += "【NPB 中央聯盟】\n" + "\n".join([f"• {g}" for g in central_games]) + "\n\n"
    msg += "【NPB 太平洋聯盟】\n" + "\n".join([f"• {g}" for g in pacific_games]) + "\n\n"
    msg += "【NPB 交流賽】\n" + "\n".join([f"• {g}" for g in inter_games]) + "\n\n"
    msg += "【中華職棒 CPBL】\n" + "\n".join([f"• {g}" for g in cpbl_games])

    send_to_line(msg.strip())
    print("✅ 通知處理完成")