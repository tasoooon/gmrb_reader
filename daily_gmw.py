import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

NTFY_TOPIC = os.environ.get("NTFY_TOPIC")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def get_image_url(page_url):
    """从单个版面页提取图片绝对链接，失败返回 None"""
    try:
        resp = requests.get(page_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src.startswith('../../../pic/') and src.endswith('.jpg.2'):
                return f"https://epaper.gmw.cn/gmrb/html/{src.replace('../../../', '')}"
    except Exception as e:
        print(f"Error parsing {page_url}: {e}")
    return None

def send_to_ntfy(image_bytes, filename, title_msg):
    """推送图片到 ntfy，确保 Header 全部为纯英文/数字"""
    if len(image_bytes) > 2 * 1024 * 1024:
        print(f"Skip {filename}: size {len(image_bytes)} bytes exceeds 2MB limit")
        return False
        
    # 构造安全的纯英文 Header
    safe_headers = {
        "Filename": filename, 
        "Title": title_msg,
    }
    
    try:
        r = requests.put(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=image_bytes,
            headers=safe_headers,
            timeout=60
        )
        return r.status_code == 200
    except Exception as e:
        print(f"Failed to send {filename}: {e}")
        return False

def main():
    if not NTFY_TOPIC:
        raise Exception("Environment variable NTFY_TOPIC is not set")

    today = datetime.now()
    date_str = today.strftime("%Y%m/%d")  # 例如 202611/02
    base_layout = f"https://epaper.gmw.cn/gmrb/html/layout/{date_str}/node_{{}}.html"

    success_count = 0
    page_num = 1

    while True:
        # 构造 01, 02, 03 格式的版面号
        page_url = base_layout.format(f"{page_num:02d}")
        print(f"Checking page {page_num}: {page_url}")

        img_url = get_image_url(page_url)
        if not img_url:
            print(f"Page {page_num} not found or no image. Stopping.")
            break

        # 下载图片
        try:
            img_resp = requests.get(img_url, headers=HEADERS, timeout=30)
            img_resp.raise_for_status()
            image_bytes = img_resp.content
        except Exception as e:
            print(f"Failed to download page {page_num}: {e}")
            page_num += 1
            continue

        # 纯英文文件名和标题
        filename = f"Guangming_{today.strftime('%Y%m%d')}_Page{page_num:02d}.jpg"
        title_msg = f"Guangming Daily - Page {page_num:02d}"

        if send_to_ntfy(image_bytes, filename, title_msg):
            success_count += 1
            print(f"Successfully sent page {page_num}")
        else:
            print(f"Failed to send page {page_num}")

        page_num += 1
        time.sleep(1)  # 稍微等待，避免请求过快

    if success_count == 0:
        raise Exception("No pages were successfully pushed. Please check.")
    print(f"Done. Successfully pushed {success_count} pages.")

if __name__ == "__main__":
    main()
