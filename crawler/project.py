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
    for i in range(194000, 195100, 1): 
        URL = "https://www.wanted.co.kr/wd/" + str(i)
        URL_LIST.append(URL)

MAKE_URL()

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
            title = soup.title.text
           
            details = soup.select("#__next > div.JobDetail_cn__WezJh > \
                                    div.JobDetail_contentWrapper__DQDB6 > div.JobDetail_relativeWrapper__F9DT5 > \
                                    div.JobContent_className___ca57 > div.JobContent_descriptionWrapper__SM4UD > \
                                    section.JobDescription_JobDescription__VWfcb")
            
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
           
            #data = {'detail': combined_text}
            #producer = KafkaProducer(acks=0, bootstrap_servers=["43.200.4.150:9092","15.164.229.162:9092","3.39.25.90:9092"], value_serializer=lambda x: json.dumps(x, default=str, ensure_ascii=False).encode('utf-8'))
            #producer.send('job-data', value=data)
            time.sleep(0.1)
            job_titles = [
                    "Data Engineer",
                    "Embedded Developer",
                    "Java Developer",
                    ".NET Developer",
                    "Network Administrator",
                    "System, Network Administrator",
                    "Front-end Engineer",
                    "Security Engineer",
                    "Hardware Engineer",
                    "DevOps / System Admin",
                    "Test Engineer",
                    "QA, Test Engineer",
                    "Android Developer",
                    "iOS Developer",
                    "Chief Information Officer",
                    "CIO, Chief Information Officer",
                    "Chief Technology Officer",
                    "CTO, Chief Technology Officer",
                    "Back-end Engineer",
                    "Web Developer",
                    "Product Manager",
                    "Development Manager",
                    "PHP Developer",
                    "Ruby on Rails Developer",
                    "Node.js Developer",
                    "Voice Engineer",
                    "Video, Voice Engineer",
                    "Graphics Engineer",
                    "Python Developer",
                    "C++ Developer",
                    "C, C++ Developer",
                    "Web Publisher",
                    "BI Engineer",
                    "Data Scientist",
                    "Big Data Engineer",
                    "Technical Support",
                    "Blockchain Platform Engineer",
                    "Machine Learning Engineer",
                    "Software Engineer",
                    "Cross-platform App Developer",
                    "VR Engineer",
                    "ERP Consultant",
                    "Database Administrator",
                ]

            if any(job in job_titles for job in jikmoo_list):
                cleaned_title = re.sub(r'[\\/*?:"<>]', '', str(title))
                cleaned_title = re.sub(r'\| 원티드', '', cleaned_title)
                txt_file_path = f"{cleaned_title}.txt"
                print(f"채용 공고 : {cleaned_title}")
                # 채용공고 잘 가져오는 지 확인
                with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
                    for detail in details:
                        combined_text = f"{title}\n\n직무: {jikmoo_list}\n\n{detail.get_text()}\n\n{URL.split('/')[-1]}"
                        txt_file.write(combined_text + '\n')
                        
                        data = {'detail': combined_text}
                        producer = KafkaProducer(acks=0, bootstrap_servers=["43.200.4.150:9092","15.164.229.162:9092","3.39.25.90:9092"], 
                                                 value_serializer=lambda x: json.dumps(x, default=str, ensure_ascii=False).encode('utf-8'))
                        producer.send('job-data', value=data)
        completed_count += 1
        time.sleep(1)         
driver.close()
