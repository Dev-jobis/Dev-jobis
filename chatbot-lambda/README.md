# 챗봇 AWS Lambda

## 각 Lambda 함수 설명
### 1. get_query_and_invoke_lambda
1. 사용자가 봇에게 질문하는 메시지(DM)을 받습니다.
2. 해당 슬랙 request에 3초 이내로 response를 보냅니다. (이 때 slack signature를 점검하여 실제로 슬랙에서 온 메시지인지 검증합니다)
3. 2에서 검증이 완료되면 아래의 reply_rag Lambda를 비동기로 invoke 합니다. 

###  2. reply_rag
1. 위의 get_query_and_invoke_lambda에서 invoke 되어서 실행됩니다. 
2. get_query_and_invoke_lambda로부터 사용자의 DM 내용을 전달 받아, 이에 대한 답변을 준비합니다. (OpenAI, Pinecone)
3. 사용자에게 준비한 내용을 DM으로 보냄으로써 답변을 완료합니다. 

\+ TODO: 필요 레이어 관련 설명 추가