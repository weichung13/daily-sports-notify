# daily-sports-notify

每天台灣時間 09:00 從 FotMob 取得足球賽程並推送 LINE。日常執行只用 Python 標準函式庫與 HTTP，不使用 MCP、Gemini 或其他模型，也不查詢棒球。

## 執行

需要 Python 3.11+。

```sh
python main.py                       # 僅預覽今天賽程
python main.py --date 2026-09-16      # 指定台灣日期預覽
python -m unittest discover -s tests -v
python main.py --send                # 實際發送 LINE
```

發送時設定 `LINE_CHANNEL_ACCESS_TOKEN`、`LINE_USER_ID`；GitHub Actions 使用同名 Secrets，不再需要 `GEMINI_API_KEY`。workflow 已改用 `--send`，推送到 GitHub 後才會套用新版排程。

## 範圍與架構

- 五大聯賽、歐冠、歐霸。
- 杯賽預設包含英格蘭足總杯／聯賽杯、西班牙國王杯、德國杯、義大利杯、法國杯，以及這五國的超級杯／社區盾。未包含世界盃、歐協聯、女子或青年賽事與另外列出的資格賽；可編輯 `competitions.json` 擴充。
- 以台灣時間今天 00:00 到明天 04:00（含）開賽的比賽為準，保留今日已結束場次並標示狀態。主隊在前，隊名沿用來源，不用模型翻譯。
- `fotmob.py`：抓今天及明天兩份資料、檢查回傳日期、轉換時區、篩選賽事、依比賽 ID 去重及排序。
- `competitions.json`：集中管理 FotMob 賽事 ID 與中文名稱。
- `main.py`：命令列預覽與 LINE 發送，長訊息分段。

資料格式異常或請求失敗會讓程式／workflow 失敗，不將查詢失敗寫成「沒有比賽」。GET 暫時性錯誤最多嘗試三次；LINE 發送失敗直接回報，避免自動重試重複通知。

抓取探索與維護方式見 [FotMob 方法記錄](docs/fotmob.md)。FotMob 網站內部端點沒有此專案可依賴的穩定性保證；若改版，依記錄重新用 MCP 確認。
