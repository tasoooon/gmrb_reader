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
        print(f"解析 {page_url} 出错: {e}")
    return None

def send_to_ntfy(image_bytes, filename, title_msg):
    """推送图片到 ntfy"""
    if len(image_bytes) > 2 * 1024 * 1024:
        print(f"跳过 {filename}：大小 {len(image_bytes)} 字节，超过 2MB 限制")
        return False
    r = requests.put(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=image_bytes,
        headers={"Filename": filename, "Title": "光明日报", "Message": title_msg},
        timeout=60
    )
    return r.status_code == 200

def main():
    if not NTFY_TOPIC:
        raise Exception("未设置 NTFY_TOPIC")

    today = datetime.now()
    date_str = today.strftime("%Y%m/%d")  # 例如 202611/02
    date_display = today.strftime("%Y年%m月%d日")
    base_layout = f"https://epaper.gmw.cn/gmrb/html/layout/{date_str}/node_{{}}.html"

    success_count = 0
    page_num = 1

    while True:
        page_url = base_layout.format(f"{page_num:02d}")
        print(f"检查第 {page_num} 版: {page_url}")

        img_url = get_image_url(page_url)
        if not img_url:
            print(f"第 {page_num} 版无图片或页面不存在，停止")
            break

        # 下载图片
        try:
            img_resp = requests.get(img_url, headers=HEADERS, timeout=30)
            img_resp.raise_for_status()
            image_bytes = img_resp.content
        except Exception as e:
            print(f"下载第 {page_num} 版图片失败: {e}")
            page_num += 1
            continue

        filename = f"Guangming_{today.strftime('%Y%m%d')}_第{page_num:02d}版.jpg"
        msg = f"{date_display} 第{page_num:02d}版"

        if send_to_ntfy(image_bytes, filename, msg):
            success_count += 1
            print(f"第 {page_num} 版推送成功")
        else:
            print(f"第 {page_num} 版推送失败")

        page_num += 1
        time.sleep(1)  # 稍微等待，避免请求过快

    if success_count == 0:
        raise Exception("所有版面均未成功推送，请检查")
    print(f"完成，共推送 {success_count} 个版面")

if __name__ == "__main__":
    main()
