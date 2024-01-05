import os
import logging
from time import sleep
from datetime import datetime
import pinecone
import openai
import tiktoken
from tqdm.auto import tqdm
from langchain.text_splitter import RecursiveCharacterTextSplitter
import json_to_doc
from log_to_kafka import CustomLogger
from utils import OPENAI_API_KEY, PINECONE_API_KEY

logger = CustomLogger("embedding", default_level=logging.INFO)

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
PINECONE_ENV = "gcp-starter"


def define_text_splitter(
    llm_name="gpt-3.5-turbo-1106", chunk_size=300, chunk_overlap=0
):
    # 아래 둘 중 하나 고르면 됨
    # create the length function
    tokenizer = tiktoken.encoding_for_model(llm_name)  # 모델에 맞는 인코딩 고르기
    # tokenizer = tiktoken.get_encoding('cl100k_base')

    def tiktoken_len(text):
        tokens = tokenizer.encode(text, disallowed_special=())
        return len(tokens)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=tiktoken_len,
        separators=["\n\n", "\n", " ", "", "."],
    )
    return text_splitter


def split_text_into_chunks(docs, text_splitter):
    """
    doc = Document(
        page_content=" ".join(line_dict["contents"]),
        metadata={
            "title": line_dict["title"],
            "url": line_dict["url"],
            "job_category": line_dict["job_category"],
            "workplace": line_dict["workplace"],
            "technology_stack": line_dict["technology_stack"],
        }
    )
    docs: doc list
    """
    chunks = []
    for idx, doc in enumerate(docs):
        texts = text_splitter.split_text(
            doc.page_content
        )  # document 하나를 쪼개서 전체 리스트인 chunk에 넣는다.
        for i in range(len(texts)):
            chunks.extend(
                [
                    {
                        "id": f"{doc.metadata['url']}_{i}",
                        "text": texts[i],
                        "job_category": doc.metadata["job_category"],
                        "workplace": doc.metadata["workplace"],
                        "technology_stack": doc.metadata["technology_stack"],
                    }
                ]
            )
    return chunks


def upsert_chunks_to_index(
    pinecone_index,
    chunks,
    openai_client,
    embed_model="text-embedding-ada-002",
    batch_size=100,
):
    """
    batch_size: how many embeddings we create and insert at once

    """
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
                sleep(10)
                try:
                    res = openai_client.embeddings.create(
                        input=texts, model=embed_model
                    )
                    done = True
                except:
                    pass
        embeds = [record.embedding for record in res.data]
        # cleanup metadata
        meta_batch = [
            {
                "text": x["text"],
                "job_category": x["job_category"],
                "workplace": x["workplace"],
                "technology_stack": x["technology_stack"],
            }
            for x in meta_batch
        ]
        to_upsert = list(zip(ids_batch, embeds, meta_batch))
        # upsert to Pinecone
        pinecone_index.upsert(vectors=to_upsert)
        sleep(5)


def main():
    # 1. Pinecone Init
    index_name = "test-metadata"
    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)

    if pinecone.list_indexes():  # 인덱스를 하나밖에 못 만들기 때문에 기존 인덱스가 있다면 지운다. TODO: 옵션으로 수정
        for index in pinecone.list_indexes():
            pinecone.delete_index(index)
            print("delete index Done", index)

    if index_name not in pinecone.list_indexes():
        pinecone.create_index(
            name=index_name,
            dimension=1536,  # openAIEmbeddings의 dimension 크기 1536
            # metric='cosine'
            metric="dotproduct",
        )

    pinecone_index = pinecone.Index(index_name)
    print(pinecone_index.describe_index_stats())

    # 2. Connect to OpenAI
    openai_client = openai.OpenAI()

    # 3. Text to Chunks
    bucket_name = "project05-crawling"
    prefix = "job-data/20240105"  # For test
    # prefix = "test_json"  # For test

    docs = json_to_doc.S3_bucket_file_loader(bucket_name, prefix)
    text_splitter = define_text_splitter()
    chunks = split_text_into_chunks(docs, text_splitter)

    # 4. Upsert to Pinecone
    upsert_chunks_to_index(
        pinecone_index,
        chunks,
        openai_client=openai_client,
        embed_model="text-embedding-ada-002",
        batch_size=100,
    )
    logger.send_json_log(
        message="Pinecone Index Upsert Done.",
        log_level=logging.INFO,
        timestamp=datetime.utcnow(),
        extra_data={"docs_count": len(docs), "last_url": docs[-1].metadata["url"]},
    )


if __name__ == "__main__":
    main()
