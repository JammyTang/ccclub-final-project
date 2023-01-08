# 載入 selenium相關模組
import requests
import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# 需要手動點擊 『下一頁』 幾次
page = int(input("請輸入搜尋到第幾頁:"))
page_new = page - 15

# 設定 Chrome Driver的執行檔路徑
options = Options()
options.chrome_executable_path = "D:\python_training\chromedriver.exe"

# 建立 Driver 物件實體，用程式操作瀏覽器運作
driver = webdriver.Chrome(options = options)

# 連線 104 工作搜尋網頁
driver.get("https://www.104.com.tw/jobs/search/?ro=1&kwop=7&keyword=%E6%95%B8%E6%93%9A%E5%88%86%E6%9E%90%E4%BA%BA%E5%93%A1&expansionType=area%2Cspec%2Ccom%2Cjob%2Cwf%2Cwktm&order=15&asc=0&page=1&mode=s&jobsource=2018indexpoc&langFlag=0&langStatus=0&recommendJob=1&hotJob=1")

# 透過程式執行「滑到下方」 動作
n = 0
while n < 15:
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    time.sleep(1)
    n += 1

# 自動載入只會到15頁，第16頁之後須點選「手動載入」
k = 1
while k <= page_new:
    link = driver.find_element(By.CLASS_NAME,"js-more-page",)
    driver.execute_script("arguments[0].click();", link)
    # link.click()
    time.sleep(3)
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    print('Click 手動載入第' + str(15 + k) + '頁')
    k += 1
    time.sleep(3)

soup_104 = BeautifulSoup(driver.page_source, "html.parser")
all_jobs = soup_104.findAll("a", {"class":"js-job-link"})
print('共有' + str(len(all_jobs)) + '筆資料')