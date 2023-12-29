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
import crawling_logging


class JsonFormatter(logging.Formatter):
    def __init__(self):
        super(JsonFormatter, self).__init__()

    def format(self, record):
        # timestamp = datetime.utcfromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        datetime.utcnow()
        log_data = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "level": record.levelname,
            "message": f"{record.getMessage()}",
            "name": record.name,
        }
        record.log_data = log_data
        return super(JsonFormatter, self).format(record)


file_handler = logging.FileHandler("example.log", encoding="utf-8")
formatter = JsonFormatter()
file_handler.setFormatter(formatter)

logger = logging.getLogger("crawlinglog")
logger.setLevel(logging.INFO)

logger.addHandler(file_handler)


class KafkaHandler(logging.Handler):
    def emit(self, record):
        log_data = getattr(record, "log_data", None)
        if log_data:
            producer.send(
                "open-test",
                value=json.dumps(log_data, default=str, ensure_ascii=False).encode(
                    "utf-8"
                ),
            )
            time.sleep(0.05)


kafka_broker_addresses = os.getenv(
    "KAFKA_BROKER_ADDRESSES", "170.0.0.139:9092,170.0.0.155:9092,170.0.0.170:9092"
).split(",")

producer = KafkaProducer(
    acks=0,
    bootstrap_servers=kafka_broker_addresses,
    value_serializer=lambda x: x,
    metadata_max_age_ms=60000,
    request_timeout_ms=30000,
)
kafka_handler = KafkaHandler()
kafka_handler.setLevel(logging.INFO)
kafka_handler.setFormatter(formatter)
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


### 아래 주석 부분으로 수정 예정 - 코드 리뷰 때 확인
def make_url_list(start, end, step):
    url_list = [f"https://www.wanted.co.kr/wd/{i}" for i in range(start, end, step)]
    return url_list


URL_LIST = make_url_list(185000, 186000, 1)


## 루프 코딩을 어떻게 할 것인가
def make_url_list(start, finish):
    url_list = []

    # start부터 end까지의 숫자를 이용하여 URL을 생성하고 리스트에 추가
    for i in range(start, finish):
        url = f"https://www.wanted.co.kr/wd/{i}"
        url_list.append(url)

    return url_list


# MAKE_URL 함수를 사용하여 URL 리스트 생성
URL_LIST = make_url_list(1, 100, 1)


for i, url in enumerate(URL_LIST):
    try:
        # 1. 접근 가능한 페이지인지 확인
        response = requests.get(url)
        response.raise_for_status()  # TODO: 어떤 경우 있는지 확인

        driver.get(url)
        WebDriverWait(driver, 20).until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )

        crawling_logging.log_crawling_start()

        # 2. 개발 공고인지 확인

        # 3. 개발 공고면 크롤링 해서 저장
        page_source = driver.page_source
        soup = bs(page_source, "html.parser")

        companyname = soup.select(
            "#__next > div.JobDetail_cn__WezJh > div.JobDetail_contentWrapper__DQDB6 > "
            "div.JobDetail_relativeWrapper__F9DT5 > div.JobContent_className___ca57 > "
            "section.JobHeader_className__HttDA > div:nth-child(2) > "
            "span.JobHeader_companyNameText__uuJyu > a"
        )

        if companyname:
            data_company_name = companyname[0]["data-company-name"]

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

        soup = str(soup)
        if '"occupationalCategory":' in soup:  # TODO: 직무 찾기 function으로 빼기
            if '"validThrough":' in soup:
                jikmoo = soup[
                    soup.find('"occupationalCategory":')
                    + 24 : soup.find('"validThrough":')
                    - 2
                ]
            else:
                jikmoo = soup[
                    soup.find('"occupationalCategory":')
                    + 24 : soup.find('"employmentType"')
                    - 2
                ]
        elif '"sub_categories":' in soup:
            jikmoo = soup[
                soup.find('"sub_categories":') + 18 : soup.find('],"position":') - 1
            ]

        jikmoo_list = [item.lstrip().replace('"', "") for item in jikmoo.split(",")]

        time.sleep(1)

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
                    r"<span.*?>|amp;|<\/span>|<div.*?>|<\/div>|<h3>|<\/h3>|\]|\[|,",
                    "",
                    combined_text,
                )
                combined_text_cleaned = re.sub(r"<br/>", "\n", combined_text_cleaned)
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
