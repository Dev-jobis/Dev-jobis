# 자비스(Job-is) !
![face-green-280](https://github.com/Dev-jobis/Dev-jobis/assets/44356311/5e6bea20-0625-406f-bf53-7408d5760787)
![face-gray-280](https://github.com/Dev-jobis/Dev-jobis/assets/44356311/675c65a6-c8dd-4651-ac8b-5998e53418ce)


<aside>
새싹 취준생들을 위한 개발 직무 Q&A 챗봇🌱 <br>
언제 어디서든 자비스! 를 불러 주세요. <br>
원티드 채용공고를 기반으로 개발 직무에 대한 궁금증을 해결해 드립니다. <br>
</aside>

<br> 
<br>

* [자비스(Job-is)의 Brand Identity](https://jungpark.notion.site/Job-is-Brand-Identity-353f65ce7d9949ffac32c1edf75ae497)

<br> 
<br>

## 자비스 아키텍처
![아키텍쳐_git](https://github.com/Dev-jobis/Dev-jobis/assets/44356311/6a526c4b-1415-477a-b9a4-cba54719e9d7)

### 1. 데이터 및 로그 파이프라인
Go to 👉 [kafka-cluster](https://github.com/Dev-jobis/Dev-jobis/tree/main/kafka-cluster) <br>
`Kafka` `Fluentd` `OpenSearch` `Terraform` `Ansible` `Prometheus` `Grafana`
### 2. 원티드 크롤러
Go to 👉 [crawler](https://github.com/Dev-jobis/Dev-jobis/tree/main/crawler) <br>
`Python` `Selenium` `AWS` `S3` `EC2`
### 3. 텍스트 임베딩과 벡터 데이터베이스
Go to 👉 [vector_db_pinecone](https://github.com/Dev-jobis/Dev-jobis/tree/main/vector_db_pinecone) <br>
`Python` `OpenAI` `Langchain` `Pinecone` `Docker`
<br>
### 4. 자비스 본체 : Slack Bot
Go to 👉 [chatbot-lambda](https://github.com/Dev-jobis/Dev-jobis/tree/main/chatbot-lambda) <br>
`Python` `Slack API` `Lambda` `AWS` 
