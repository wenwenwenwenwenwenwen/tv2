import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=chrome_options)
# 使用WebDriver访问网页
url = "http://tonkiang.us/hotellist.html?s=60.189.35.225:9999"
driver.get(url)  # 将网址替换为你要访问的网页地址
time.sleep(10)
# 获取网页内容
page_content = driver.page_source
print(page_content)
# 关闭WebDriver
driver.quit()

