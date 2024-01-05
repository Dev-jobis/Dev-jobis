import json
from datetime import datetime
import logging
import time
from kafka import KafkaProducer

TOPIC = "embedding-log"  # 이 부분 수정하여 사용
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
        kafka_log_producer.send(TOPIC, value=log_data)
        time.sleep(0.1)


class CustomLogger:
    def __init__(self, service_name, default_level=logging.DEBUG):
        self.service_name = service_name
        self.default_level = default_level  # 기본으로 DEBUG로 세팅
        self.logger = self.define_logger()

    def define_logger(self):
        logger = logging.getLogger(self.service_name)
        logger.setLevel(self.default_level)
        logger.addHandler(KafkaHandler())
        return logger

    def send_json_log(
        self,
        message,
        timestamp,
        log_level=None,
        extra_data=None,
    ):
        if log_level is None:
            log_level = self.default_level

        log_data = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S.%f"),
            "level": logging.getLevelName(log_level),
            "message": message,
            "service_name": self.service_name,
            "extra_data": extra_data,
        }
        json_log_data = json.dumps(log_data, ensure_ascii=False)
        self.logger.log(log_level, json_log_data)
