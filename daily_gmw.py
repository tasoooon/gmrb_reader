import os
import requests
from bs4 import BeautifulSoup

NTFY_TOPIC = os.environ.get("NTFY_TOPIC")
BASE_URL = "https://epaper.gmw.cn/gmrb/html"

def get_today_image_urls():
    """访问今天的版面导航页，提取版面图片链接。这里需要根据实际页面结构调整选择器。"""
    # 先访问首页或版面导航页，找到当天所有版面的链接
    # 然后逐个打开版面页，从里面找到代表整个版面的那张大图的 src
    # 具体选择器需要你观察实际页面的 HTML 结构来写
    # 下面是一个示意框架
    image_urls = []
    # ... 解析逻辑 ...
    return image_urls

def send_via_ntfy(image_url, index):
    """下载图片并通过 ntfy PUT 请求发送为附件"""
    # 下载图片
    resp = requests.get(image_url, timeout=30)
    if resp.status_code != 200:
        print(f"图片下载失败: {image_url}")
        return False

    image_bytes = resp.content
    # 粗略检查大小，ntfy 匿名用户附件限制约 2MB
    if len(image_bytes) > 2 * 1024 * 1024:
        print(f"图片过大，跳过: {image_url}, 大小 {len(image_bytes)} bytes")
        return False

    # 用 PUT 发送文件附件
    filename = f"gmrb_page_{index}.jpg"
    r = requests.put(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=image_bytes,
        headers={
            "Filename": filename,
            "Message": f"光明日报版面 {index}",
        },
        timeout=60
    )
    return r.status_code == 200

def main():
    if not NTFY_TOPIC:
        raise Exception("NTFY_TOPIC 环境变量未设置")

    urls = get_today_image_urls()
    if not urls:
        raise Exception("未获取到任何版面图片，请检查页面结构是否变化")

    success = 0
    for i, url in enumerate(urls, 1):
        if send_via_ntfy(url, i):
            success += 1
            print(f"已推送版面 {i}")

    if success == 0:
        raise Exception("所有版面推送均失败")
    print(f"完成，成功推送 {success}/{len(urls)} 个版面")

if __name__ == "__main__":
    main()
