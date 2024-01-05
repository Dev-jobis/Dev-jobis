import os
from datetime import datetime
import time
import openai
import pinecone
from utils import OPENAI_API_KEY, PINECONE_API_KEY
from log_to_kafka import CustomLogger


os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
PINECONE_ENV = "gcp-starter"
logger = CustomLogger("lambda-slack-02")


class WantedChatBot:
    def __init__(self, index_name, query, primer, k):
        self.index_name = index_name
        self.pinecone_index = self.init_pinecone_index(self.index_name)
        self.query = query
        self.primer = primer
        self.k = k
        self.embed_model = "text-embedding-ada-002"
        self.openai_client = openai.OpenAI()
        self.context = self.get_related_contexts()
        self.augmented_query = self.make_augmented_query()
        self.answer = self.make_answer()  # generator

    def init_pinecone_index(self, index_name):
        init_time = time.time()
        pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
        index_name = "test-metadata"
        index = pinecone.Index(index_name)
        print(index.describe_index_stats())
        logger.send_json_log(
            "Pinecone INIT",
            timestamp=datetime.utcnow(),
            extra_data={"duration_sec": time.time() - init_time},
        )
        return index

    def get_related_contexts(self):
        init_time = time.time()
        query_to_vector = self.openai_client.embeddings.create(
            input=[self.query], model=self.embed_model
        )
        xq = query_to_vector.data[0].embedding
        res = self.pinecone_index.query(xq, top_k=self.k, include_metadata=True)
        # similarity 가 특정 threshold 를 넘는 것만 뽑아와야 할텐데
        related_contexts = [item["metadata"]["text"] for item in res["matches"]]
        logger.send_json_log(
            message="Related context is ready.",
            timestamp=datetime.utcnow(),
            extra_data={"duration_sec": time.time() - init_time},
        )
        return related_contexts

    def make_augmented_query(self):
        augmented_query = (
            "\n\n---\n\n".join(self.context) + "\n\n-----\n\n" + self.query
        )
        return augmented_query

    def make_answer(self):
        init_time = time.time()
        logger.send_json_log("start making answer ... ", timestamp=datetime.utcnow())
        stream = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": self.primer},
                {"role": "user", "content": self.augmented_query},
            ],
            stop="4",
            temperature=0,  # TODO: 수정 필요
            stream=True,
        )
        logger.send_json_log(
            "Answer is ready.",
            timestamp=datetime.utcnow(),
            extra_data={"duration_sec": time.time() - init_time},
        )
        for chunk in stream:
            yield chunk.choices[0].delta.content or ""
