import re
import json
import logging
import time
from datetime import datetime
import requests
from kafka import KafkaProducer
from bs4 import BeautifulSoup as bs
from bs4.element import Tag, ResultSet
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import variables
from log_to_kafka import CustomLogger, kafka_log_producer
from utils import START_URL_NUMBER, URL_RANGE, update_start_url_number

logger = CustomLogger(service_name="crawler", default_level=logging.INFO)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
)
chrome_options.add_argument("--log-level=DEBUG")

service = Service(executable_path=ChromeDriverManager().install())  # 시간 오래 걸림
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


def get_job_list(page_source):
    if '"occupationalCategory":' in page_source:
        if '"validThrough":' in page_source:
            job = page_source[
                page_source.find('"occupationalCategory":')
                + 24 : page_source.find('"validThrough":')
                - 2
            ]
        else:
            job = page_source[
                page_source.find('"occupationalCategory":')
                + 24 : page_source.find('"employmentType"')
                - 2
            ]
        job_list = [item.lstrip().replace('"', "") for item in job.split(",")]
        return job_list
    elif '"sub_categories":' in page_source:
        job = page_source[
            page_source.find('"sub_categories":')
            + 18 : page_source.find('],"position":')
            - 1
        ]
        job_list = [item.lstrip().replace('"', "") for item in job.split(",")]
        return job_list
    else:
        return None


def cleaning_bs_Tag(tag_data):
    assert type(tag_data) == Tag
    text = tag_data.get_text()
    # re.sub(r"<div.*?>(.*?)<\/div>", r"\1 ", data)
    text = re.sub("“|”|'", "", text)  # json 처리
    text = re.sub(r"<.*?>|amp;|-|\[|\]|▪|▶|'| 원티드'|•|●|#|※|■", " ", text)
    return text.strip()


def combined_text_company_address(data):
    if isinstance(data, Tag):
        data = str(data)
    combined_text_delete_tag = re.sub(r"<div.*?>(.*?)<\/div>", r"\1 ", data)
    combined_text = re.sub(
        r"<.*?>|amp;|-|\[|\]|▪|▶|'| 원티드'|•|●|#|※|■", " ", combined_text_delete_tag
    )
    combined_text = re.sub("“|”", " ", combined_text)
    return combined_text


def check_response(url):
    response = requests.get(url)
    # response.raise_for_status()
    if response.status_code != 200:  # TODO: logger가 붙는 곳이 일관성이 없음
        logger.send_json_log(
            message=f"URL Request {response.status_code}",
            timestamp=datetime.utcnow(),
            extra_data={"url": url, "code": response.status_code},
            log_level=logging.WARNING,
        )
        return False
    return True


def check_if_developer_job(page_source):
    job_list = get_job_list(page_source)
    if (job_list is not None) and any(job in variables.job_titles for job in job_list):
        return True
    return False


def get_post_details(soup, idx, tag):
    selector = base_selector + job_content_wrapper_selector + job_description_selector
    res = soup.select(selector.format(idx, tag))
    return res


base_selector = (
    "#__next > div.JobDetail_cn__WezJh > div.JobDetail_contentWrapper__DQDB6 > "
    "div.JobDetail_relativeWrapper__F9DT5 > div.JobContent_className___ca57 > "
)
job_header_selector = "section.JobHeader_className__HttDA > div:nth-child(2) > "
job_header_company_name_selector = "span.JobHeader_companyNameText__uuJyu > a"
job_header_location_selector = "span.JobHeader_pcLocationContainer__xRwIv"
job_content_wrapper_selector = "div.JobContent_descriptionWrapper__SM4UD > "
job_description_selector = (
    "section.JobDescription_JobDescription__VWfcb > p:nth-child({}) > {}"
)
# selector 자체는 그냥 텍스트네
# base_selector.format(1, "span") -> 이거는 {} 안에 넣는 fstring


def crawling_post(url):
    """
    한 개의 url에 대해서 크롤링
    """
    if not check_response(url):
        return

    driver.get(url)
    WebDriverWait(driver, 20).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )  # assert return True
    page_source = driver.page_source

    if not check_if_developer_job(page_source):
        logger.send_json_log(
            message=f"Not Developer's job post.",
            timestamp=datetime.utcnow(),
            extra_data={"url": url},
            log_level=logging.WARNING,
        )
        return

    # unrefined data ...
    soup = bs(page_source, "html.parser")

    title = soup.title.get_text()
    location = soup.select_one(
        base_selector + job_header_selector + job_header_location_selector
    )  # type: bs4.element.Tag
    company_description = get_post_details(soup, 1, "span")  # ResultSet, list
    main_business = get_post_details(soup, 3, "span")  # ResultSet, list
    qualifications = get_post_details(soup, 5, "span")  # ResultSet, list
    preferential = get_post_details(soup, 7, "span")  # ResultSet, list
    welfare = get_post_details(soup, 9, "span")  #  ResultSet, list
    technology_stack = get_post_details(soup, 11, "div")  # ResultSet, list / 없는 경우 있음

    # 전처리
    title_refined = re.sub(r"[|\[\]원티드]", "", title).strip()
    location_refined = location.get_text()  # 서울.한국
    company_description_refined = [cleaning_bs_Tag(x) for x in company_description]
    main_business_refined = [cleaning_bs_Tag(x) for x in main_business]
    qualifications_refined = [cleaning_bs_Tag(x) for x in qualifications]
    preferential_refined = [cleaning_bs_Tag(x) for x in preferential]
    welfare_refined = [cleaning_bs_Tag(x) for x in welfare]
    technology_stack_refined = [cleaning_bs_Tag(x) for x in technology_stack]

    # json dumps
    combined_text = {
        "title": title_refined,
        "url": url,
        "job_category": get_job_list(page_source),
        "location": location_refined,
        "technology_stack": technology_stack_refined,
        "contents": company_description_refined
        + main_business_refined
        + qualifications_refined
        + preferential_refined
        + welfare_refined,
    }
    combined_text_json = json.dumps(combined_text, ensure_ascii=False)
    print("combined_text_json : ", combined_text_json)
    kafka_log_producer.send("job-data", value=combined_text_json)
    logger.send_json_log(
        message="crawling complete.",
        timestamp=datetime.utcnow(),
        extra_data=combined_text_json,
        log_level=logging.INFO,
    )
    return


def main():
    start_time = time.time()
    wanted_post_base_url = "https://www.wanted.co.kr/wd/"
    url_list = [
        f"{wanted_post_base_url}{i}"
        for i in range(START_URL_NUMBER, START_URL_NUMBER + URL_RANGE)
    ]

    print("start here", url_list[0])
    for url in url_list:
        crawling_post(url)
    print("end here", url)

    # parameter update
    update_start_url_number(str(START_URL_NUMBER + URL_RANGE))
    end_time = time.time()
    logger.send_json_log(
        message=f"All crawling Done. ",
        timestamp=datetime.utcnow(),
        extra_data={"duration_sec": end_time - start_time},
        log_level=logging.INFO,
    )
    return


if __name__ == "__main__":
    main()
