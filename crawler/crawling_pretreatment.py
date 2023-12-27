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


class JsonFormatter(logging.Formatter):
    def __init__(self):
        super(JsonFormatter, self).__init__()

    def format(self, record):
        # timestamp = datetime.utcfromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        datetime.utcnow()
        log_data = {
            'timestamp': get_utc_now().strftime('%Y-%m-%d %H:%M:%S.%f'),
            'level': record.levelname,
            'message': f'{record.getMessage()}',
            'name': record.name
        }
        record.log_data = log_data
        return super(JsonFormatter, self).format(record)


file_handler = logging.FileHandler('example.log', encoding='utf-8')
formatter = JsonFormatter()
file_handler.setFormatter(formatter)

logger = logging.getLogger("crawlinglog")
logger.setLevel(logging.INFO)

logger.addHandler(file_handler)

class KafkaHandler(logging.Handler):
    def emit(self, record):
        log_data = getattr(record, 'log_data', None)
        if log_data:
            producer.send('open-test', value=json.dumps(log_data, default=str, ensure_ascii=False).encode('utf-8'))
            time.sleep(0.05)

        
kafka_broker_addresses = os.getenv('KAFKA_BROKER_ADDRESSES', '170.0.0.139:9092,170.0.0.155:9092,170.0.0.170:9092').split(',')

producer = KafkaProducer(
    acks=0,
    bootstrap_servers=kafka_broker_addresses,
    value_serializer=lambda x: x,
    metadata_max_age_ms=60000,
    request_timeout_ms=30000
)
kafka_handler = KafkaHandler()
kafka_handler.setLevel(logging.INFO)
kafka_handler.setFormatter(formatter)
logger.addHandler(kafka_handler)

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
chrome_options.add_argument('--log-level=DEBUG')

service = Service(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
            """
})

def log_crawling_start():
    extra_data = {'timestamp': datetime.utcnow()}
    logger.info('crawling start.', extra=extra_data)

def log_crawling_success(url):
    extra_data = {'timestamp': datetime.utcnow()}
    logger.info(f'success - URL: {url}', extra=extra_data)

def log_http_error(url, http_err):
    extra_data = {'timestamp': datetime.utcnow()}
    logger.error(f'Not found. {http_err}', extra=extra_data)

def log_request_error(url, req_err):
    extra_data = {'timestamp': datetime.utcnow()}
    logger.error(f'fail requests: {req_err}', extra=extra_data)

def log_crawling_error(error):
    extra_data = {'timestamp': datetime.utcnow()}
    logger.error(f'fail crawling: {error}', extra=extra_data)

def log_non_dev_related(url):
    extra_data = {'timestamp': datetime.utcnow()}
    logger.info(f'this url({url})is not for developer', extra=extra_data)
    
### 아래 주석 부분으로 수정 예정 - 코드 리뷰 때 확인
def make_url_list(start, end, step):
    url_list = [f"https://www.wanted.co.kr/wd/{i}" for i in range(start, end, step)]
    return url_list

URL_LIST = make_url_list(185000, 186000, 1)

### 루프 코딩을 어떻게 할 것인가
# def MAKE_URL(start, finish, step):
#     URL_LIST = []
    
#     # 주어진 finish 횟수만큼 반복
#     for _ in range(finish):
#         end = start + step
        
#         # start부터 end까지의 숫자를 이용하여 URL을 생성하고 리스트에 추가
#         for i in range(start, end):
#             url = "https://www.wanted.co.kr/wd/" + str(i)
#             URL_LIST.append(url)
        
#         # 다음 반복을 위해 start 값을 end로 업데이트
#         start = end      
    
#     return URL_LIST

# # MAKE_URL 함수를 사용하여 URL 리스트 생성
# URL_LIST = MAKE_URL(1, 100, 1)

# # 다음 루프를 위해 start 값을 설정
# next_start = URL_LIST[-1].split("/")[-1]
# next_start = int(next_start) + 1

# # 다음 루프를 위한 URL 리스트 생성
# NEXT_LOOP = MAKE_URL(next_start, 100, 1)



completed_count = 0
max_completed_count = len(URL_LIST)

while completed_count < max_completed_count:
    for i, URL in enumerate(URL_LIST):
        try:
            response = requests.get(URL)
            response.raise_for_status()

            driver.get(URL)
            WebDriverWait(driver, 20).until(lambda driver: driver.execute_script("return document.readyState") == "complete")

            log_crawling_start()

            page_source = driver.page_source
            soup = bs(page_source, 'html.parser')

            companyname = soup.select("#__next > div.JobDetail_cn__WezJh > div.JobDetail_contentWrapper__DQDB6 > "
                                      "div.JobDetail_relativeWrapper__F9DT5 > div.JobContent_className___ca57 > "
                                      "section.JobHeader_className__HttDA > div:nth-child(2) > "
                                      "span.JobHeader_companyNameText__uuJyu > a")

            if companyname:
                data_company_name = companyname[0]['data-company-name']

            title = soup.title.text
            base_selector = "#__next > div.JobDetail_cn__WezJh > div.JobDetail_contentWrapper__DQDB6 > " \
                             "div.JobDetail_relativeWrapper__F9DT5 > div.JobContent_className___ca57 > " \
                             "div.JobContent_descriptionWrapper__SM4UD > " \
                             "section.JobDescription_JobDescription__VWfcb > p:nth-child({}) > {}"
            workplace = soup.select_one('#__next > div.JobDetail_cn__WezJh > '
                                         'div.JobDetail_contentWrapper__DQDB6 > div.JobDetail_relativeWrapper__F9DT5 > '
                                         'div.JobContent_className___ca57 > section.JobHeader_className__HttDA > '
                                         'div:nth-child(2) > span.JobHeader_pcLocationContainer__xRwIv')

            companydescription = str(soup.select(base_selector.format(1, 'span')))
            mainbusiness = str(soup.select(base_selector.format(3, 'span')))
            qualifications = str(soup.select(base_selector.format(5, 'span')))
            preferential = str(soup.select(base_selector.format(7, 'span')))
            welfare = str(soup.select(base_selector.format(9, 'span')))
            technologystack = str(soup.select(base_selector.format(11, 'div')))

            soup = str(soup)
            if '"occupationalCategory":' in soup:
                if '"validThrough":' in soup:
                    jikmoo = soup[soup.find('"occupationalCategory":') + 24: soup.find('"validThrough":') - 2]
                else:
                    jikmoo = soup[soup.find('"occupationalCategory":') + 24: soup.find('"employmentType"') - 2]
            elif '"sub_categories":' in soup:
                jikmoo = soup[soup.find('"sub_categories":') + 18: soup.find('],"position":') - 1]

            jikmoo_list = [item.lstrip().replace('"', '') for item in jikmoo.split(",")]

            time.sleep(1)

            job_titles = [
                "Data Engineer", "Embedded Developer", "Java Developer", ".NET Developer",
                "Network Administrator", "System, Network Administrator", "Front-end Engineer", "Security Engineer",
                "Hardware Engineer", "DevOps", "System Admin", "DevOps / System Admin",
                "Test Engineer", "QA, Test Engineer", "Android Developer", "iOS Developer",
                "Chief Information Officer", "CIO, Chief Information Officer", "Chief Technology Officer",
                "CTO, Chief Technology Officer",
                "Back-end Engineer", "Web Developer", "Product Manager", "Development Manager",
                "PHP Developer", "Ruby on Rails Developer", "Node.js Developer", "Voice Engineer",
                "Video, Voice Engineer", "Graphics Engineer", "Python Developer", "C++ Developer",
                "C, C++ Developer", "Web Publisher", "BI Engineer", "Data Scientist", "Big Data Engineer",
                "Technical Support", "Blockchain Platform Engineer", "Machine Learning Engineer", "Software Engineer",
                "Cross-platform App Developer", "VR Engineer", "ERP Consultant", "Database Administrator"
            ]

            if any(job in job_titles for job in jikmoo_list):
                cleaned_title = re.sub(r'[\\/*?:"<>]', '', re.sub(r'\| 원티드', '', str(data_company_name)))
                txt_file_path = f"test_{cleaned_title}_{URL.split('/')[-1]}.txt"
                print(f"채용 공고 : {cleaned_title}/{URL.split('/')[-1]}")

                with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
                    combined_text = f"{title}\n" \
                                    f"{cleaned_title}\n" \
                                    "직무 : " f"{jikmoo_list}\n" \
                                    "근무지역 : " f"{workplace}\n" \
                                    f"{companydescription}\n" \
                                    "주요업무\n" \
                                    f"{mainbusiness}\n" \
                                    "자격요건\n" \
                                    f"{qualifications}\n" \
                                    "우대사항\n" \
                                    f"{preferential}\n" \
                                    "혜택 및 복지\n" \
                                    f"{welfare}\n" \
                                    "기술스택\n" \
                                    f"{technologystack}\n" \
                                    f"https://www.wanted.co.kr/wd/{URL.split('/')[-1]}\n"

                    combined_text_cleaned = re.sub(r'<span.*?>|amp;|<\/span>|<div.*?>|<\/div>|<h3>|<\/h3>|\]|\[|,',
                                                  '', combined_text)
                    combined_text_cleaned = re.sub(r'<br/>', '\n', combined_text_cleaned)
                    txt_file.write(combined_text_cleaned + '\n')
                    data = {combined_text_cleaned.replace('\n', ' ')}
                    serialized_data = json.dumps(data, default=str, ensure_ascii=False).encode('utf-8')

                    producer.send('job-data', value=serialized_data)
                        
                    log_crawling_success(URL)
            else:
                log_non_dev_related(URL)

        except requests.exceptions.HTTPError as http_err:
            log_http_error(URL, http_err)
        except requests.exceptions.RequestException as req_err:
            log_request_error(URL, req_err)
        except Exception as e:
            log_crawling_error(e)
            continue

        completed_count += 1
        time.sleep(1)

logger.removeHandler(file_handler)
driver.close()