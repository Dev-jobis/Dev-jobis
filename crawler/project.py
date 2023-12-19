import os
import time
import requests
from selenium import webdriver
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import openpyxl
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from datetime import datetime
import pyautogui
import sys
from openpyxl import Workbook
from selenium.common.exceptions import StaleElementReferenceException   
from webdriver_manager.chrome import ChromeDriverManager

# 크롬 옵션 설정
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
#pyautogui : 키보드 자동화
pyautogui.FAILSAFE = False

chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
service = Service(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
# driver.maximize_window()
#크롤링방지옵션 해제
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
            """
})
#크롤링페이지
wait = webdriver.support.ui.WebDriverWait(driver, 1)
url = "https://www.wanted.co.kr/wdlist/518?country=kr&job_sort=job.latest_order&years=0&years=2&locations=all" #3
driver.get(url=url)
time.sleep(1)

write_wb = Workbook()
write_ws = write_wb.active

while True:
    ids = driver.find_elements(by=By.CSS_SELECTOR, value=".Card_className__u5rsb")
    time.sleep(1)

    for link_num, job_card in enumerate(ids, start=1):
        try:
            link = job_card.find_element(By.CSS_SELECTOR, "div > a").get_attribute('href')
            co_name = job_card.find_element(By.CSS_SELECTOR, "div > a > div > div.job-card-company-name").text
        except StaleElementReferenceException:
            continue
#테스트용으로 20개 처리로 설정(나중에 늘림)
        if link_num > 20:
            break

        link = job_card.find_element(By.CSS_SELECTOR, "div > a").get_attribute('href')
        co_name = job_card.find_element(By.CSS_SELECTOR, "div > a > div > div.job-card-company-name").text
        print(f"{link_num} : {co_name}")

        pyautogui.hotkey("command", "")
        time.sleep(2)
        all_windows = driver.window_handles

        driver.execute_script("window.open('');")
        all_windows = driver.window_handles
        driver.switch_to.window(all_windows[1])
#공고 페이지 열기
        driver.get(link)
        time.sleep(2)

        page_source = driver.page_source
        soup = bs(page_source, 'html.parser')
        details = soup.select("#__next > div.JobDetail_cn__WezJh > \
                                div.JobDetail_contentWrapper__DQDB6 > div.JobDetail_relativeWrapper__F9DT5 > \
                                div.JobContent_className___ca57 > div.JobContent_descriptionWrapper__SM4UD > \
                                section.JobDescription_JobDescription__VWfcb")
        txt_file_path = f"{co_name}.txt"
        with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
            for detail in details:
                txt_file.write(detail.get_text() + '\n')
        print(f"크롤링 완료 : {txt_file_path}")

#웹페이지 닫기
        driver.close()
        all_windows = driver.window_handles
        driver.switch_to.window(all_windows[-1])

