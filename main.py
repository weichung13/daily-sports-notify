import pdfplumber
import requests
import os
from datetime import datetime

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.getenv('LINE_USER_ID')

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
    raise ValueError("缺少 LINE Secrets")

now = datetime.now()
print(f"今天是: {now.strftime('%Y-%m-%d')}")

PDF_PATH = "pdfs/cpbl.pdf"

print("=== CPBL PDF 中所有包含 '4/' 的行（用來診斷） ===")
try:
    with pdfplumber.open(PDF_PATH) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            for line in text.split('\n'):
                line = line.strip()
                if '4/' in line and any(team in line for team in ['雄鷹', '桃猿', '兄弟', '統一', '富邦', '味全', '台鋼']):
                    print(f"頁 {page_num}: {line}")
except Exception as e:
    print("讀取 PDF 失敗:", str(e))

print("\n=== 程式執行結束 ===")