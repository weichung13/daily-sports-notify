# FotMob 抓取方法

2026-09-16 使用 Playwright MCP 實際開啟 https://www.fotmob.com/，透過 `browser_network_requests`（filter: `fotmob.com/api`）觀察到：

```text
GET /api/data/matches?date=20260916&timezone=Asia%2FTaipei&ccode3=TWN&includeNextDayLateNight=true
GET /api/data/allLeagues?locale=en&country=TWN
```

第一個端點直接 HTTP 測試回傳 200 JSON，不需要 API Key、Cookie 或瀏覽器。第二個端點提供 `popular`、`international`、`countries[].leagues`，用來確認賽事 ID；日常不需要下載完整聯賽清單。

## 已確認的結構

- 根物件：`date`（YYYYMMDD 字串）、`leagues` 陣列。
- 聯賽物件：`id`、`primaryId`、`name`、`matches`。
- 比賽：`id`、`home.name`、`away.name`、`status.utcTime`（ISO 8601 UTC）、`status.started/finished/cancelled`、`status.reason`。
- 杯賽必須優先比對 `primaryId`。觀察到 EFL Cup 的 `id=938221`，但 `primaryId=133`；只比 `id` 會漏賽事。
- `time` 是格式化字串，不是可靠的台灣時間；`isNextDay` 也不能代替時間區間篩選。從 `status.utcTime` 轉換 `Asia/Taipei`。
- 首頁 `__NEXT_DATA__` 的 fallback 未提供完整賽程，不使用 HTML 文字或模型知識推測。

## 日常方式

執行專案 `python main.py` 或 `python main.py --date YYYY-MM-DD`。程式分別請求今天和明天、設 `includeNextDayLateNight=false`，再自行限制到台灣時間隔日 04:00（含），避免依賴網站對「深夜」的定義。每次正常執行兩個 GET，不消耗模型 token。測試不要加 `--send`。

## 網站改版時

1. 用 Playwright MCP 開首頁，篩選 `/api/.*matches` 的 network requests；切換日期，確認當前參數和回傳日期。
2. 僅查看一份賽程回應的相關欄位；避免把整頁快照／所有網路請求放入模型。
3. 用普通 HTTP 重放觀察到的公開請求，確認 JSON、日期與杯賽 ID。遇到 401／403 或人機驗證時停止，不加入繞過驗證的程式。
4. 更新 `fotmob.py` 與有代表性的測試，執行離線測試和不發 LINE 的實網預覽。增加賽事先從 `allLeagues` 確認 ID，再改 `competitions.json`。

目前 LINE 發送與 GitHub Actions 雲端網路環境需要各自實際執行才能驗證；本機 HTTP 成功不代表所有執行環境都能存取。
