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

file_handler = logging.FileHandler("example.log", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

logger = logging.getLogger("example_logger")
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

log_data = {
    "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f"),
    "level": logging.INFO,
    "message": "Log message",
    "name": "logger-name",
}

json_log_data = json.dumps(log_data)
logger.info(json_log_data)

# Kafka 관련 설정
kafka_broker_addresses = os.getenv(
    "kafka_broker_address",
    "175.0.0.139:9092,175.0.0.155:9092,175.0.0.170:9092",
).split(",")

producer = KafkaProducer(
    acks=0,
    bootstrap_servers=kafka_broker_addresses,
    value_serializer=lambda x: x,
    metadata_max_age_ms=60000,
    request_timeout_ms=30000,
)


class KafkaHandler(logging.Handler):
    def emit(self, record):
        log_data = getattr(record, "log_data", None)
        if log_data:
            producer.send("open-test", value=json.dumps(log_data))
            time.sleep(0.05)


kafka_handler = KafkaHandler()
kafka_handler.setLevel(logging.INFO)
kafka_handler.setLevel(logging.DEBUG)
logger.addHandler(kafka_handler)

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

start_url_range = 100
end_url_range = 200000


def make_url_list(start, finish):
    url_list = []

    for i in range(start, finish):
        url = f"https://www.wanted.co.kr/wd/{i}"
        url_list.append(url)

    return url_list


url_list = make_url_list(start_url_range, end_url_range)


for i, url in enumerate(URL_LIST):
    try:
        # 1. 접근 가능한 페이지인지 확인
        response = requests.get(url)
        response.raise_for_status()  # HTTP 상태 코드가 200이 아니면 예외 발생
        driver.get(url)
        WebDriverWait(driver, 20).until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )

        page_source = driver.page_source
        soup = bs(page_source, "html.parser")

        logger.info(f"crawling start, url: {url}")

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
            logger.info(f"{datetime.utcnow()} url: {url}, 에러: 개발 직군이 아님.")
            continue  # continue를 사용하여 이후의 코드를 실행하지 않고 다음 반복으로 넘어갑니다.

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
                serialized_data = json.dumps(
                    data, default=str, ensure_ascii=False
                ).encode("utf-8")
                producer.send("job-data", value=serialized_data)

                crawling_logging.log_crawling_success(url)
        else:
            crawling_logging.log_non_dev_related(url)

    except requests.exceptions.HTTPError as http_err:  # 404
        crawling_logging.log_http_error(url, http_err)
    except requests.exceptions.RequestException as req_err:
        crawling_logging.log_request_error(url, req_err)
    except Exception as e:
        crawling_logging.log_crawling_error(e)
        continue

    time.sleep(1)

logger.removeHandler(file_handler)
driver.close()
