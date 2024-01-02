import os
import time
import requests
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from kafka import KafkaProducer
import re
import json
import logging
from datetime import datetime
import variables
import schedule
from threading import Thread
from log_to_kafka import CustomLogger, kafka_log_producer

logger = CustomLogger(service_name="crawler", default_level=logging.INFO)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
)
chrome_options.add_argument("--log-level=DEBUG")

service = Service(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
            """
    },
)

start_url_range = 189900
end_url_range = 190000


def make_url_list(start, finish):
    url_list = []
    for i in range(start, finish):
        url = f"https://www.wanted.co.kr/wd/{i}"
        url_list.append(url)
    return url_list


def append_url_batch(url_list, start, batch_size):
    for i in range(start, start + batch_size):
        url = f"https://www.wanted.co.kr/wd/{i}"
        url_list.append(url)
    return url_list, start + batch_size


def job():
    global url_list, current_start
    batch_size = 200
    url_list, current_start = append_url_batch(url_list, current_start, batch_size)


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


url_list = make_url_list(start_url_range, end_url_range)
current_start = end_url_range + 1

schedule.every().day.at("00:00").do(job)

scheduler_thread = Thread(target=run_scheduler)
scheduler_thread.start()


for i, url in enumerate(url_list):
    try:
        # 1. 접근 가능한 페이지인지 확인
        response = requests.get(url)
        response.raise_for_status()
        driver.get(url)
        WebDriverWait(driver, 20).until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )

        page_source = driver.page_source
        soup = bs(page_source, "html.parser")
        logger.send_json_log(
            message="crawling start.",
            extra_data={"url": url},
            log_level=logging.INFO,
        )
        # 2. 개발 공고인지 확인
        if '"occupationalCategory":' in page_source:
            if '"validThrough":' in page_source:
                jikmoo = page_source[
                    page_source.find('"occupationalCategory":')
                    + 24 : page_source.find('"validThrough":')
                    - 2
                ]
            else:
                jikmoo = page_source[
                    page_source.find('"occupationalCategory":')
                    + 24 : page_source.find('"employmentType"')
                    - 2
                ]
        elif '"sub_categories":' in page_source:
            jikmoo = page_source[
                page_source.find('"sub_categories":')
                + 18 : page_source.find('],"position":')
                - 1
            ]
        else:
            continue

        jikmoo_list = [item.lstrip().replace('"', "") for item in jikmoo.split(",")]
        time.sleep(1)

        # 3. 개발 공고면 크롤링 해서 저장

        companyname = soup.select(
            "#__next > div.JobDetail_cn__WezJh > div.JobDetail_contentWrapper__DQDB6 > "
            "div.JobDetail_relativeWrapper__F9DT5 > div.JobContent_className___ca57 > "
            "section.JobHeader_className__HttDA > div:nth-child(2) > "
            "span.JobHeader_companyNameText__uuJyu > a"
        )

        if companyname:
            data_company_name = companyname[0]["data-company-name"]

        else:
            logger.send_json_log(
                message="No Develop job.",
                extra_data={"url": url},
                log_level=logging.WARNING,
            )
            continue

        title = soup.title.text
        base_selector = (
            "#__next > div.JobDetail_cn__WezJh > div.JobDetail_contentWrapper__DQDB6 > "
            "div.JobDetail_relativeWrapper__F9DT5 > div.JobContent_className___ca57 > "
            "div.JobContent_descriptionWrapper__SM4UD > "
            "section.JobDescription_JobDescription__VWfcb > p:nth-child({}) > {}"
        )
        workplace = soup.select_one(
            "#__next > div.JobDetail_cn__WezJh > "
            "div.JobDetail_contentWrapper__DQDB6 > div.JobDetail_relativeWrapper__F9DT5 > "
            "div.JobContent_className___ca57 > section.JobHeader_className__HttDA > "
            "div:nth-child(2) > span.JobHeader_pcLocationContainer__xRwIv"
        )

        companydescription = str(soup.select(base_selector.format(1, "span")))
        mainbusiness = str(soup.select(base_selector.format(3, "span")))
        qualifications = str(soup.select(base_selector.format(5, "span")))
        preferential = str(soup.select(base_selector.format(7, "span")))
        welfare = str(soup.select(base_selector.format(9, "span")))
        technologystack = str(soup.select(base_selector.format(11, "div")))

        if any(job in variables.job_titles for job in jikmoo_list):
            cleaned_title = re.sub(
                r'[\\/*?:"<>]', "", re.sub(r"\| 원티드", "", str(data_company_name))
            )
            txt_file_directory = "txt_file_directory"
            if not os.path.exists(txt_file_directory):
                os.mkdir(txt_file_directory)
            txt_file_path = os.path.join(
                txt_file_directory, f"test_{cleaned_title}_{url.split('/')[-1]}.txt"
            )
            print(f"채용 공고 : {cleaned_title}/{url.split('/')[-1]}")
            with open(txt_file_path, "w", encoding="utf-8") as txt_file:
                combined_text = (
                    f"{title}\n"
                    f"{cleaned_title}\n"
                    "직무 : "
                    f"{jikmoo_list}\n"
                    "근무지역 : "
                    f"{workplace}\n"
                    f"{companydescription}\n"
                    "주요업무\n"
                    f"{mainbusiness}\n"
                    "자격요건\n"
                    f"{qualifications}\n"
                    "우대사항\n"
                    f"{preferential}\n"
                    "혜택 및 복지\n"
                    f"{welfare}\n"
                    "기술스택\n"
                    f"{technologystack}\n"
                    f"https://www.wanted.co.kr/wd/{url.split('/')[-1]}\n"
                )
                combined_text_cleaned = re.sub(
                    r"<div.*?>(.*?)<\/div>", r"\1 ", combined_text
                )
                combined_text_cleaned = re.sub(r"<.*?>|amp;|\[|\]", "", combined_text)

                txt_file.write(combined_text_cleaned + "\n")
                data = {combined_text_cleaned.replace("\n", " ")}
            kafka_log_producer.send("job-data", value=combined_text_cleaned)
            time.sleep(0.1)
            logger.send_json_log(
                message="crawling complete.",
                extra_data={"url": url},
                log_level=logging.INFO,
            )
        else:
            logger.send_json_log(
                message="No Develop job.",
                extra_data={"url": url},
                log_level=logging.WARNING,
            )
            continue

    except requests.exceptions.HTTPError as http_err:
        logger.send_json_log(
            message="No Webpage.",
            extra_data={"url": url},
            log_level=logging.ERROR,
        )
        continue
    except requests.exceptions.RequestException as req_err:
        logger.send_json_log(
            message="Request Error.",
            extra_data={"url": url},
            log_level=logging.ERROR,
        )
        continue
    except Exception as e:
        logger.send_json_log(
            message="Exception Error.",
            extra_data={"url": url},
            log_level=logging.ERROR,
        )
        continue

time.sleep(1)
logger.send_json_log(
    message="crawling is Done.",
    log_level=logging.INFO,
)
driver.close()
