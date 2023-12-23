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

chrome_options = Options()
chrome_options.add_argument('--headless')
   
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
chrome_options.add_argument('--log-level=3')

service = Service(executable_path=ChromeDriverManager().install())
   
driver = webdriver.Chrome(service=service, options=chrome_options)
  
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
            """
})
URL_LIST = []

def MAKE_URL():
    for i in range(195000, 195100, 1): # 리눅스로 크론탭할 때 변수 변경이 가능한가
        URL = "https://www.wanted.co.kr/wd/" + str(i)
        URL_LIST.append(URL)

MAKE_URL()

# def MAKE_URL(start, iterations, step):
#     URL_LIST = []
    
#     for _ in range(iterations):
#         end = start + step
#         for i in range(start, end):
#             url = "https://www.wanted.co.kr/wd/" + str(i)
#             URL_LIST.append(url)
#         start = end      
#     return URL_LIST

# URL_LIST = MAKE_URL(195000, 100, 1)

# # 다음 루프를 위해 start 값을 설정
# start_for_next_loop = URL_LIST[-1].split("/")[-1]
# start_for_next_loop = int(start_for_next_loop) + 1

# URL_LIST_NEXT_LOOP = MAKE_URL(start_for_next_loop, 100, 1)

completed_count = 0
max_completed_count = len(URL_LIST)


while completed_count < max_completed_count:
    for i, URL in enumerate(URL_LIST):
        response = requests.get(URL)
        if response.status_code == 200:
            
            driver.get(URL)
            try:
                WebDriverWait(driver, 20).until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            except TimeoutException:
                print("페이지 로딩 시간 초과")

            page_source = driver.page_source
            soup = bs(page_source, 'html.parser')
            
            companyname = soup.select("#__next > div.JobDetail_cn__WezJh > div.JobDetail_contentWrapper__DQDB6 > \
                div.JobDetail_relativeWrapper__F9DT5 > div.JobContent_className___ca57 > section.JobHeader_className__HttDA > \
                div:nth-child(2) > span.JobHeader_companyNameText__uuJyu > a")

            if companyname:
                data_company_name = companyname[0]['data-company-name']            
            
            title = soup.title.text
            base_selector = "#__next > div.JobDetail_cn__WezJh > div.JobDetail_contentWrapper__DQDB6 > \
                  div.JobDetail_relativeWrapper__F9DT5 > div.JobContent_className___ca57 > \
                  div.JobContent_descriptionWrapper__SM4UD > \
                  section.JobDescription_JobDescription__VWfcb > p:nth-child({}) > {}"
            
            companydescription = str(soup.select(base_selector.format(1, 'span')))
            mainbusiness = str(soup.select(base_selector.format(3, 'span')))
            qualifications = str(soup.select(base_selector.format(5, 'span')))
            preferential = str(soup.select(base_selector.format(7, 'span')))
            welfare = str(soup.select(base_selector.format(9, 'span')))
            technologystack = str(soup.select(base_selector.format(11, 'div')))

            soup = str(soup)

            if soup.find('"occupationalCategory":')!= -1:
                if soup.find('"validThrough":')!= -1:
                    jikmoo = soup[soup.find('"occupationalCategory":') + 24: soup.find('"validThrough":') - 2]
                else:
                    jikmoo = soup[soup.find('"occupationalCategory":') + 24: soup.find('"employmentType"') - 2]
            elif soup.find('"sub_categories":')!= -1:
                jikmoo = soup[soup.find('"sub_categories":') + 18: soup.find('],"position":') - 2]
            
            jikmoo_list = []
            current_item = ""
            for item in jikmoo:
                if item == ",":
                    jikmoo_list.append(current_item)
                    current_item = ""
                else:
                    current_item += item
            jikmoo_list.append(current_item)
            
            jikmoo_list = [item.lstrip().replace('"', '') 
                for item in jikmoo_list]   
            time.sleep(1)
            
            job_titles = [
                    "Data Engineer","Embedded Developer","Java Developer",".NET Developer",
                    "Network Administrator","System, Network Administrator","Front-end Engineer","Security Engineer",
                    "Hardware Engineer","DevOps""System Admin""DevOps / System Admin",
                    "Test Engineer","QA, Test Engineer","Android Developer","iOS Developer",
                    "Chief Information Officer","CIO, Chief Information Officer","Chief Technology Officer","CTO, Chief Technology Officer",
                    "Back-end Engineer","Web Developer","Product Manager","Development Manager",
                    "PHP Developer","Ruby on Rails Developer","Node.js Developer","Voice Engineer",
                    "Video, Voice Engineer","Graphics Engineer","Python Developer","C++ Developer",
                    "C, C++ Developer","Web Publisher","BI Engineer","Data Scientist","Big Data Engineer",
                    "Technical Support","Blockchain Platform Engineer","Machine Learning Engineer","Software Engineer",
                    "Cross-platform App Developer","VR Engineer","ERP Consultant","Database Administrator"
                ]

            if any(job in job_titles for job in jikmoo_list):
                cleaned_title = re.sub(r'[\\/*?:"<>]', '', re.sub(r'\| 원티드', '', str(data_company_name)))
                txt_file_path = f"{cleaned_title} _{URL.split('/')[-1]}.txt"
                print(f"채용 공고 : {cleaned_title}/{URL.split('/')[-1]}")

                with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
                    combined_text = f"{title}\n\n직무: {jikmoo_list}\n\n"\
                                    f"{companydescription}\n\n"\
                                    "주요업무\n"\
                                    f"{mainbusiness}\n\n"\
                                    "자격요건\n"\
                                    f"{qualifications}\n\n"\
                                    "우대사항\n"\
                                    f"{preferential}\n\n"\
                                    "혜택 및 복지\n"\
                                    f"{welfare}\n\n"\
                                    "기술스택\n"\
                                    f"{technologystack}\n\n"\
                                    f"https://www.wanted.co.kr/wd/{URL.split('/')[-1]}\n"\
                                    # "마감일\n"\
                                    # f"{deadline}\n\n"\
                                    # "근무지역\n"\
                                    # f"{workplace}\n\n"\
                                    
                    combined_text_cleaned = combined_text.replace('<div class="SkillItem_SkillItem__E2WtM">', ', ')
                    combined_text_cleaned = re.sub(r'<span.*?>|amp;|<\/span>|<div.*?>|<\/div>|<h3>|<\/h3>|\]|\[|,', '', combined_text_cleaned)
                    combined_text_cleaned = re.sub(r'<br/>', '\n', combined_text_cleaned)
                    txt_file.write(combined_text_cleaned + '\n')
                    data = {combined_text_cleaned.replace('\n', ' ')}
                    serialized_data = json.dumps(data, default=str, ensure_ascii=False).encode('utf-8')

                    # producer = KafkaProducer(
                    #         acks=0,
                    #         bootstrap_servers=["13.125.213.220:9092", "54.180.81.131:9092", "54.180.91.234:9092"],
                    #         value_serializer=lambda x: x,)
                    # producer.send('job-data', value=serialized_data)
                    # time.sleep(0.05)
        completed_count += 1
        time.sleep(1)         
driver.close()
