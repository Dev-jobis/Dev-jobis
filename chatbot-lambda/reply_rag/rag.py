import os
import logging
from datetime import datetime
import openai
import pinecone
from utils import OPENAI_API_KEY, PINECONE_API_KEY


os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
PINECONE_ENV = "gcp-starter"


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
        logger.info("%s pinecone init ...", datetime.utcnow())
        pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
        index_name = "test-metadata"
        index = pinecone.Index(index_name)
        print(index.describe_index_stats())
        logger.info("%s pinecone init ... DONE", datetime.utcnow())
        return index

    def get_related_contexts(self):
        query_to_vector = self.openai_client.embeddings.create(
            input=[self.query], model=self.embed_model
        )
        xq = query_to_vector.data[0].embedding
        res = self.pinecone_index.query(xq, top_k=self.k, include_metadata=True)
        # similarity 가 특정 threshold 를 넘는 것만 뽑아와야 할텐데
        related_contexts = [item["metadata"]["text"] for item in res["matches"]]
        logger.info(related_contexts)
        return related_contexts

    def make_augmented_query(self):
        augmented_query = (
            "\n\n---\n\n".join(self.context) + "\n\n-----\n\n" + self.query
        )
        logger.info("%s augmented query : %s", datetime.utcnow(), augmented_query)
        return augmented_query

    def make_answer(self):
        logger.info("%s making answer ... ", datetime.utcnow())
        stream = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": self.primer},
                {"role": "user", "content": self.augmented_query},
            ],
            stop="4",
            temperature=0,
            stream=True,
        )
        logger.info(stream)
        for chunk in stream:
            yield chunk.choices[0].delta.content or ""
