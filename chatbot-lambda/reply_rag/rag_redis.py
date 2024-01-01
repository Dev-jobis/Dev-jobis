import os
from slack_bolt import App
from langchain.schema import format_document
from langchain_core.messages import AIMessage, HumanMessage, get_buffer_string
from langchain_core.runnables import RunnableParallel

from langchain.prompts.prompt import PromptTemplate
from operator import itemgetter

from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Pinecone
import pinecone
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.memory.chat_message_histories import RedisChatMessageHistory

from langchain.memory import ConversationBufferMemory

from langchain_core.runnables.history import RunnableWithMessageHistory

import redis
from utils import (
    OPENAI_API_KEY,
    PINECONE_API_KEY,
    SLACK_BOT_TOKEN,
    SLACK_SIGNING_SECRET,
)

REDIS_URL = ""
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
PINECONE_ENV = "gcp-starter"


app = App(
    token=SLACK_BOT_TOKEN,  # bot user token
    signing_secret=SLACK_SIGNING_SECRET,
)
slack_client = app.client

# 1. retriever 만들기
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
index_name = "test-metadata"
index = pinecone.Index(index_name)
embeddings = OpenAIEmbeddings()
vectorstore = Pinecone(index, embeddings, text_key="text")
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.8, "k": 3},
)


# 2. standalone question 만들기
_template = """
Given the following conversation and a follow up question,
rephrase the follow up question to be a standalone question, in its original language.

Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:
"""
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)


# 3. retriever 이용한 프롬프트 만들기
template = """
    You are Q&A bot. A highly intelligent system that answers user questions
    based only on the following context below.
    Your task is to help Job seeker and applicants get information about jobs
    they are finding.
    If the information can not be found in the information
    provided by the user you truthfully say "I don't know".
    Your answer should be in Korean.

    Context : {context}

    Question: {question}
    """
ANSWER_PROMPT = ChatPromptTemplate.from_template(template)


# 4. 모델
model = ChatOpenAI()  # 근데 딱히 안 쓰네요

# 5. rag로 들고온 documents
DEFAULT_DOCUMENT_PROMPT = PromptTemplate.from_template(template="{page_content}")


def _combine_documents(
    docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"
):
    doc_strings = [format_document(doc, document_prompt) for doc in docs]
    return document_separator.join(doc_strings)


# 6. 메모리, 히스토리
user_id = "U05PL5WCHF0"  # 내 슬랙 user_id
message_history = RedisChatMessageHistory(
    url=REDIS_URL,
    # ttl=3600,
    session_id=user_id,  # 1시간동안 DB에 저장. optional이라 없어도 됨.
)
memory = ConversationBufferMemory(
    return_messages=True,
    output_key="answer",
    input_key="question",
    memory_key="chat_history",
    chat_memory=message_history,
)
loaded_memory = RunnablePassthrough.assign(
    chat_history=RunnableLambda(memory.load_memory_variables)
    | itemgetter("chat_history"),
)

standalone_question = {
    "standalone_question": {
        "question": lambda x: x["question"],
        "chat_history": lambda x: get_buffer_string(x["chat_history"]),
    }
    | CONDENSE_QUESTION_PROMPT
    | ChatOpenAI(temperature=0)
    | StrOutputParser(),
}

retrieved_documents = {
    "docs": itemgetter("standalone_question") | retriever,
    "question": lambda x: x["standalone_question"],
}

final_inputs = {
    "context": lambda x: _combine_documents(x["docs"]),
    "question": itemgetter("question"),
}
answer = {
    "answer": final_inputs | ANSWER_PROMPT | ChatOpenAI(),
    "docs": itemgetter("docs"),
}

final_chain = loaded_memory | standalone_question | retrieved_documents | answer


# streaming
def make_stream(inputs: dict, questioner_channel):
    full_response = ""
    ans = ""
    i = 0

    for chunk in final_chain.stream(inputs):
        if chunk.get("answer"):
            ans += chunk.get("answer").content or ""
            i += 1
            if i > 30 and ans[-1] in [" ", ",", ".", "\n"]:
                # print(ans)
                slack_client.chat_postMessage(channel=questioner_channel, text=ans)
                full_response += ans
                i = 0
                ans = ""
    if ans != "":
        # print(ans)
        slack_client.chat_postMessage(channel=questioner_channel, text=ans)
        full_response += ans
    memory.save_context(inputs, {"answer": full_response})  # redis에 full_response로 저장


# example)
# inputs = {
#     "question": "데이터 엔지니어를 하려면 어떤 공부를 해야 해?",
# }
# make_stream(inputs=inputs)
