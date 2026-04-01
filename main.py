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
today_str = now.strftime('%Y-%m-%d')

# PDF 檔案路徑
PDF_DIR = "pdfs"
PDF_FILES = {
    "CPBL": os.path.join(PDF_DIR, "cpbl.pdf"),
    "NPB_CENTRAL": os.path.join(PDF_DIR, "npb_central.pdf"),
    "NPB_PACIFIC": os.path.join(PDF_DIR, "npb_pacific.pdf"),
    "NPB_INTER": os.path.join(PDF_DIR, "npb.pdf")   # 交流賽
}

def extract_today_games(pdf_path, league_name):
    """從 PDF 中提取今天的比賽"""
    if not os.path.exists(pdf_path):
        return [f"{league_name} PDF 檔案不存在"]
    
    games = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    # 尋找包含今天日期或比賽時間的行
                    if (today_str in line or 
                        today_str.replace('-', '/') in line or 
                        today_str.replace('-', '') in line):
                        if any(k in line for k in ['vs', 'VS', '：', ':', '18:', '13:', '14:', '15:']):
                            clean_line = ' '.join(line.split())
                            games.append(clean_line)
        
        return games if games else [f"今天沒有 {league_name} 比賽"]
    except Exception as e:
        return [f"{league_name} PDF 解析失敗: {str(e)}"]

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
        if resp.status_code != 200:
            print("錯誤訊息:", resp.text)
    except Exception as e:
        print(f"發送 LINE 失敗: {str(e)}")

# === 主程式 ===
if __name__ == "__main__":
    print(f"執行時間：{now.strftime('%Y-%m-%d %H:%M:%S')} 台灣時間")
    print(f"正在從 PDF 讀取 {today_str} 的賽程...")

    cpbl_games = extract_today_games(PDF_FILES["CPBL"], "CPBL")
    central_games = extract_today_games(PDF_FILES["NPB_CENTRAL"], "NPB 中央聯盟")
    pacific_games = extract_today_games(PDF_FILES["NPB_PACIFIC"], "NPB 太平洋聯盟")
    inter_games = extract_today_games(PDF_FILES["NPB_INTER"], "NPB 交流賽")

    msg = f"⚾ {today_str} 棒球賽程通知\n\n"

    if any("沒有" not in g for g in central_games):
        msg += "【NPB 中央聯盟】\n" + "\n".join([f"• {g}" for g in central_games if "沒有" not in g]) + "\n\n"
    else:
        msg += "【NPB 中央聯盟】\n今天沒有比賽\n\n"

    if any("沒有" not in g for g in pacific_games):
        msg += "【NPB 太平洋聯盟】\n" + "\n".join([f"• {g}" for g in pacific_games if "沒有" not in g]) + "\n\n"
    else:
        msg += "【NPB 太平洋聯盟】\n今天沒有比賽\n\n"

    if any("沒有" not in g for g in inter_games):
        msg += "【NPB 交流賽】\n" + "\n".join([f"• {g}" for g in inter_games if "沒有" not in g]) + "\n\n"
    else:
        msg += "【NPB 交流賽】\n今天沒有比賽\n\n"

    msg += "【中華職棒 CPBL】\n" + "\n".join([f"• {g}" for g in cpbl_games])

    send_to_line(msg.strip())
    print("✅ 通知處理完成")