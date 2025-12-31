import requests
from bs4 import BeautifulSoup
import time
import math
import webhook
import argparse

class CrawlerService:
    def __init__(self, filter_digits=None):
        self.friends = [] #紀錄所有好友的64位ID
        self.api_url = "https://steamcommunity.com/comment/Profile/render/{steam_id}/-1/" #API端點
        self.comment_url = "https://steamcommunity.com/profiles/{steam_id}/allcomments" #用於生成結果網址
        self.target_userurl = "" #有設定ID作為網址的話，這裡不能填64位ID (範例:"id/abc123")
        self.target_friends_url = f"https://steamcommunity.com/{self.target_userurl}/friends"
        self.target_keyword = [":Aegg:"] #用or尋找，有多個關鍵字，只要其中一個有在留言裡，就會回報。可以找文字或者表情(:emoji:)
        self.count_per_request = 500  # 每次請求的留言數量
        self.filter_digits = filter_digits  # 過濾尾數列表，None 表示不過濾
    
    def fetch_comments_api(self, steam_id, start=0, count=500):
        """調用 Steam API 獲取留言"""
        api_endpoint = self.api_url.format(steam_id=steam_id)
        data = {
            'start': start,
            'count': count,
        }
        try:
            response = requests.post(api_endpoint, data=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API 請求失敗: {e}", flush=True)
            return None
    
    def fetch_friends_list(self):
        """自動抓取好友名單"""
        print(f"開始抓取好友名單: {self.target_friends_url}", flush=True)
        
        try:
            # 請求好友列表頁面
            response = requests.get(self.target_friends_url)
            response.raise_for_status()
            
            # 使用 BeautifulSoup 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 找到所有 class 包含 'selectable friend_block_v2' 的 div
            friend_blocks = soup.find_all('div', class_=lambda x: x and 'selectable' in x and 'friend_block_v2' in x)
            
            # 提取所有 data-steamid 的值
            all_friends = []
            for block in friend_blocks:
                steam_id = block.get('data-steamid')
                if steam_id:
                    all_friends.append(steam_id)
            
            # 根據尾數過濾好友
            if self.filter_digits is not None:
                self.friends = []
                for steam_id in all_friends:
                    # 取得 Steam ID 的最後一位數字
                    last_digit = int(steam_id[-1])
                    if last_digit in self.filter_digits:
                        self.friends.append(steam_id)
                filter_info = f"（過濾尾數: {sorted(self.filter_digits)}，原始 {len(all_friends)} 位）"
            else:
                self.friends = all_friends
                filter_info = ""
            
            # 打印好友數量
            print(f"成功抓取好友名單，共 {len(self.friends)} 位好友{filter_info}", flush=True)
            
            return len(self.friends) > 0
            
        except requests.RequestException as e:
            print(f"抓取好友名單失敗: {e}", flush=True)
            return False
    
    def calculate_page_number(self, comment_index):
        """計算留言所在的頁數（每頁50則留言）"""
        # 無條件進位
        return math.ceil(comment_index / 50)
    
    def check_author_match(self, comment_div):
        """檢查留言作者是否匹配目標用戶"""
        author_link = comment_div.find('a', class_='hoverunderline commentthread_author_link')
        if author_link:
            href = author_link.get('href', '')
            # 檢查 href 中是否包含目標用戶 URL
            if self.target_userurl in href:
                return True
        return False
    
    def check_keyword_match(self, comment_text):
        """檢查留言內容是否包含關鍵字（包含文字和表情符號）"""
        if not comment_text:
            return False
        
        # 提取文字內容
        text = comment_text.get_text(strip=True)
        
        # 提取所有表情符號的 alt 屬性值
        emoticons = comment_text.find_all('img', class_='emoticon')
        emoticon_texts = []
        for emoticon in emoticons:
            alt_text = emoticon.get('alt', '')
            if alt_text:
                emoticon_texts.append(alt_text)
        
        # 將表情符號的 alt 值也加入到要檢查的文字中
        # 用空格分隔，方便搜尋
        full_text = text + ' ' + ' '.join(emoticon_texts)
        
        # 用 or 尋找，只要其中一個關鍵字有在留言裡，就會回報
        for keyword in self.target_keyword:
            if keyword in full_text:
                return True
        return False
    
    def crawl_comments(self):
        """主要爬蟲方法"""
        # 在開始爬取留言前，先自動抓取好友名單，如果好友名單有先寫死一些人，則只抓那些人
        if not self.friends:
            if not self.fetch_friends_list():
                print("無法抓取好友名單，程式結束", flush=True)
                return
        
        for friend_id in self.friends:
            print(f"\n開始抓取好友 {friend_id} 的留言...", flush=True)
            
            start = 0
            total_count = None
            
            while True:
                # 調用 API
                result = self.fetch_comments_api(friend_id, start=start, count=self.count_per_request)
                
                if not result:
                    print(f"無法獲取好友 {friend_id} 的留言資料", flush=True)
                    break
                
                # 檢查是否為私人檔案
                if not result.get('success', False):
                    error = result.get('error', 'Unknown error')
                    print(f"好友 {friend_id} 的檔案為私人或發生錯誤: {error}", flush=True)
                    break
                
                # 獲取總留言數（只在第一次請求時獲取）
                if total_count is None:
                    total_count = result.get('total_count', 0)
                    print(f"該用戶總留言數: {total_count}", flush=True)
                
                # 獲取留言 HTML
                comments_html = result.get('comments_html', '')
                if not comments_html:
                    # 沒有更多留言了
                    break
                
                # 清理 HTML（移除 \n 和 \t）
                comments_html = comments_html.replace('\n', '').replace('\t', '')
                
                # 使用 BeautifulSoup 解析
                soup = BeautifulSoup(comments_html, 'html.parser')
                comments = soup.find_all('div', class_='commentthread_comment_content')
                
                # 遍歷留言
                for index, comment in enumerate(comments):
                    # 檢查作者是否匹配
                    if self.check_author_match(comment):
                        # 找到留言內容
                        comment_text_div = comment.find('div', class_='commentthread_comment_text')
                        if comment_text_div:
                            # 檢查關鍵字
                            if self.check_keyword_match(comment_text_div):
                                # 計算留言編號（start + 索引 + 1）
                                comment_number = start + index + 1
                                # 計算所在頁數
                                page_number = self.calculate_page_number(comment_number)
                                # 生成網址
                                result_url = f"{self.comment_url.format(steam_id=friend_id)}?ctp={page_number}"
                                
                                comment_content = comment_text_div.get_text(strip=True)
                                print(f"\n找到匹配的留言！", flush=True)
                                print(f"留言內容: {comment_content}", flush=True)
                                print(f"留言編號: {comment_number}", flush=True)
                                print(f"所在頁數: {page_number}", flush=True)
                                print(f"網址: {result_url}\n", flush=True)
                                
                                # 發送 webhook
                                webhook.ContentAdd(f"找到匹配的留言！")
                                webhook.ContentAdd(f"留言內容: {comment_content}")
                                webhook.ContentAdd(f"留言編號: {comment_number}")
                                webhook.ContentAdd(f"所在頁數: {page_number}")
                                webhook.ContentAdd(f"網址: {result_url}")
                                webhook.Post()
                
                # 顯示進度
                current_end = start + len(comments)
                print(f"目前抓取: start={start}, count={len(comments)}, 進度: {current_end}/{total_count}", flush=True)
                
                # 如果返回的留言數少於請求的數量，表示已經到最後了
                if len(comments) < self.count_per_request:
                    break
                
                # 更新 start 值，準備下一批請求
                start += self.count_per_request
                
                # sleep 1 秒後再請求下一批
                time.sleep(1)
        
        print("\n所有好友的留言抓取完成！", flush=True)

def parse_filter_argument(filter_arg):
    """解析過濾參數，支援單個數字或範圍（如 0-5）"""
    if not filter_arg:
        return None
    
    try:
        if '-' in filter_arg:
            # 處理範圍格式，如 "0-5"
            start, end = filter_arg.split('-', 1)
            start = int(start.strip())
            end = int(end.strip())
            if start > end:
                raise ValueError("範圍起始值不能大於結束值")
            return list(range(start, end + 1))
        else:
            # 處理單個數字，如 "0" 或 "1"
            digit = int(filter_arg.strip())
            if digit < 0 or digit > 9:
                raise ValueError("尾數必須在 0-9 之間")
            return [digit]
    except ValueError as e:
        print(f"參數解析錯誤: {e}", flush=True)
        print("正確格式: 單個數字（如 0）或範圍（如 0-5）", flush=True)
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Steam 留言爬蟲程式')
    parser.add_argument('filter', nargs='?', type=str, help='過濾好友尾數，格式: 單個數字（如 0）或範圍（如 0-5）')
    args = parser.parse_args()
    
    # 解析過濾參數
    filter_digits = parse_filter_argument(args.filter)
    if filter_digits is not None:
        print(f"已設定過濾條件: 尾數 {sorted(filter_digits)}", flush=True)
    else:
        print("未設定過濾條件，將抓取所有好友", flush=True)
    
    crawler = CrawlerService(filter_digits=filter_digits)
    crawler.crawl_comments()