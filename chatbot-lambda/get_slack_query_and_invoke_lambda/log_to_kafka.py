import json
from datetime import datetime
import logging
from kafka import KafkaProducer
import time

kafka_log_producer = KafkaProducer(
    bootstrap_servers=[
        "175.0.0.139:9092",  # TODO: parameter store로 대체
        "175.0.0.155:9092",
        "175.0.0.170:9092",
    ],
    value_serializer=str.encode,
)


class KafkaHandler(logging.Handler):
    def emit(self, record):
        log_data = self.format(record)
        kafka_log_producer.send("open-test", value=log_data)  # TODO: 재사용성
        time.sleep(0.05)


class JsonFormatter(logging.Formatter):  # TODO: 재사용성
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
        }
        return json.dumps(log_data)
