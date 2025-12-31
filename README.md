# Steam-FindComment-Crawler

一個自動化爬蟲工具，用於在 Steam 平台上搜尋特定用戶在好友留言板中留下的特定關鍵字留言。

## 📋 專案簡介

這個工具可以自動：
- 抓取指定 Steam 用戶的好友名單
- 遍歷所有好友的留言板
- 搜尋包含特定關鍵字（文字或表情符號）的留言
- 檢查留言是否由目標用戶發布
- 找到匹配的留言後，自動發送 Discord Webhook 通知

## 📦 安裝說明

### 前置需求

- Python 3.11 或更高版本

### 安裝步驟

1. 克隆或下載此專案
```bash
git clone https://github.com/ani20168/Steam-FindComment-Crawler.git
cd Steam-FindComment-Crawler
```

2. 安裝套件
```bash
pip install -r requirements.txt
```

## ⚙️ 配置說明

在使用前，請先修改 `main.py` 中的以下配置：

### 1. 目標用戶 URL（第 13 行）

```python
self.target_userurl = "" #有設定ID作為網址的話，這裡不能填64位ID (範例:"id/abc123")
```

**說明**：
- 填入目標用戶的 URL，例如：`"id/abc123"` 或 `"profiles/76561198000000000"`
- ⚠️ **注意**：如果用戶有設定自訂 ID，這裡不能填 64 位 Steam ID
- 此 URL 用於：
  - 抓取該用戶的好友名單
  - 檢查留言是否由該用戶發布

### 2. 搜尋關鍵字（第 15 行）

```python
self.target_keyword = [":Aegg:"] #用or尋找，有多個關鍵字，只要其中一個有在留言裡，就會回報。可以找文字或者表情(:emoji:)
```

**說明**：
- 使用 **OR 邏輯**搜尋：只要留言中包含任一關鍵字就會回報
- 支援文字和表情符號
- 表情符號格式：`:表情名稱:`（例如：`:Aegg:`、`:steamhappy:`）

**範例**：
```python
# 搜尋單一關鍵字
self.target_keyword = [":Aegg:"]

# 搜尋多個關鍵字（OR 邏輯）
self.target_keyword = [":Aegg:", "你好", ":steamhappy:", "謝謝"]
```

### 3. 每次請求的留言數量（第 16 行）

```python
self.count_per_request = 500  # 每次請求的留言數量
```

**說明**：
- 設定每次 API 請求抓取的留言數量
- 建議值：500以上
- 數值越大，請求次數越少，但單次請求時間可能較長

### 4. Discord Webhook 設定（webhook.py）

如需使用 Discord 通知功能，請修改 `webhook.py` 中的 Webhook URL：

```python
url = "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"
```

## 🚀 使用方法

### 基本使用

直接執行主程式，會抓取所有好友的留言：

```bash
python main.py
```

### 過濾好友尾數

使用命令行參數過濾好友 ID 尾數，方便分散式爬取：

```bash
# 只爬取尾數為 0 的好友
python main.py 0

# 只爬取尾數為 0-5 的好友
python main.py 0-5

# 只爬取尾數為 7 的好友
python main.py 7
```

**使用場景**：
- 當好友數量很多時，且你擁有數台伺服器，可以透過分散式部屬來避免steam rate limit


## ⚠️ 注意事項

1. **好友名單權限**：
   - 目標用戶的好友名單必須是公開的
   - 如果好友名單為私人，程式將無法抓取

3. **留言板權限**：
   - 如果好友的留言板為私人，程式會跳過該好友並顯示錯誤訊息
   - 因此，如果曾在好友的留言板留了某筆留言，而好友的隱私設定未公開，則就算設好搜尋條件，該筆留言也無法被搜尋到
