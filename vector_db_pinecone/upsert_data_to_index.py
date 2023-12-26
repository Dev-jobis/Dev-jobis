import os
from datetime import datetime
from time import sleep
import boto3
import pinecone
import openai
import tiktoken
from tqdm.auto import tqdm
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


s3 = boto3.client("s3")


def get_s3_object(bucket, key, is_string=False):
    obj = s3.get_object(Bucket=bucket, Key=key)["Body"]  # byte object
    return obj.read().decode("utf-8").rstrip() if is_string else obj


# TODO: parameter store로 대체
os.environ["OPENAI_API_KEY"] = get_s3_object(
    "project05-credentials", "openai_sojung", is_string=True
)
PINECONE_API_KEY = get_s3_object(
    "project05-credentials", "pinecone_sojung", is_string=True
)
PINECONE_ENV = "gcp-starter"


file_directory = "crawled_data"
docs = []

for txtfile in os.listdir(file_directory):
    with open(f"{file_directory}/{txtfile}", "r") as f:
        post_id = txtfile.split("_")[-1].split(".")[0]
        data = f.read()
        data = data.split("\n")
        post_title = data[0].split("|")[0]
        company_name = data[1]
        job_type = data[2].split(":")[1]
        company_address = data[3].split(":")[-1]
        page_content = str(data[4:])

    docs.append(
        Document(
            page_content=page_content,
            metadata={
                "post_id": post_id,
                "post_title": post_title,
                "company_name": company_name,
                "job_type": job_type,
                "company_address": company_address,
            },
        )
    )

# 아래 둘 중 하나 고르면 됨
tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")  # 모델에 맞는 인코딩 고르기
# tokenizer = tiktoken.get_encoding('cl100k_base')


# create the length function
def tiktoken_len(text):
    tokens = tokenizer.encode(text, disallowed_special=())
    return len(tokens)


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=0,
    length_function=tiktoken_len,
    separators=["\n\n", "\n", " ", "", "."],
)

chunks = []
for idx, doc in enumerate(docs):
    texts = text_splitter.split_text(
        doc.page_content
    )  # document 하나를 쪼개서 전체 리스트인 chunk에 넣는다.
    for i in range(len(texts)):
        chunks.extend(
            [
                {
                    "id": f"{doc.metadata['post_id']}_{i}",
                    "text": texts[i],
                    "chunk": i,
                    "post_title": doc.metadata["post_title"],
                    "company_name": doc.metadata["company_name"],
                    "job_type": doc.metadata["job_type"],
                    "company_address": doc.metadata["company_address"],
                }
            ]
        )


index_name = "test-metadata"
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)

if pinecone.list_indexes():  # 인덱스를 하나밖에 못 만들기 때문에 기존 인덱스가 있다면 지운다.
    for index in pinecone.list_indexes():
        pinecone.delete_index(index)

if index_name not in pinecone.list_indexes():
    pinecone.create_index(
        name=index_name,
        dimension=1536,  # openAIEmbeddings의 dimension 크기 1536
        # metric='cosine'
        metric="dotproduct",
    )
# connect to index
index = pinecone.Index(index_name)
# view index stats
print(index.describe_index_stats())

batch_size = 100  # how many embeddings we create and insert at once

openai_client = openai.OpenAI()
embed_model = "text-embedding-ada-002"

for i in tqdm(range(0, len(chunks), batch_size)):
    # find end of batch
    i_end = min(len(chunks), i + batch_size)
    meta_batch = chunks[i:i_end]
    # get ids
    ids_batch = [x["id"] for x in meta_batch]
    # get texts to encode
    texts = [x["text"] for x in meta_batch]
    # create embeddings (try-except added to avoid RateLimitError)
    try:
        res = openai_client.embeddings.create(input=texts, model=embed_model)
    except:
        done = False
        while not done:
            sleep(5)
            try:
                res = openai_client.embeddings.create(input=texts, model=embed_model)
                done = True
            except:
                pass
    embeds = [record.embedding for record in res.data]
    # cleanup metadata
    meta_batch = [
        {
            "text": x["text"],
            "chunk": x["chunk"],
            "post_title": x["post_title"],
            "company_name": x["company_name"],
            "job_type": x["job_type"],
            "company_address": x["company_address"],
        }
        for x in meta_batch
    ]
    to_upsert = list(zip(ids_batch, embeds, meta_batch))
    # upsert to Pinecone
    index.upsert(vectors=to_upsert)
