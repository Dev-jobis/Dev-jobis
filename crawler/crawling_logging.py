# 찬솔님이 만들어준 로깅 파일
import logging
import json
from datetime import datetime
from kafka import KafkaProducer
import time
import logging.config
from pythonjsonlogger import jsonlogger


def get_utc_now():
    return datetime.utcnow()


# 로깅 포매터 생성 (JSON 형식)
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": get_utc_now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
        }
        return json.dumps(log_data)


# Kafka 프로듀서 생성
producer = KafkaProducer(
    bootstrap_servers=[
        "13.125.213.220:9092",
        "54.180.81.131:9092",
        "54.180.91.234:9092",
    ],
    value_serializer=str.encode,
)


class KafkaHandler(logging.Handler):
    def emit(self, record):
        log_data = self.format(record)
        producer.send("open-test", value=log_data)
        time.sleep(0.05)


# 로거 생성
logger = logging.getLogger("crawling")
logger.setLevel(logging.INFO)
formatter = JsonFormatter()
testhandler = KafkaHandler()
testhandler.setFormatter(formatter)
logger.addHandler(testhandler)
# 로깅 메시지 작성
logger.debug("This is a debug message.")
logger.info("This is an info message.")
logger.warning("This is a warning message.")
logger.error("This is an error message.")
logger.critical("This is a critical message.")
logger.info("This is an info message.")


def log_crawling_start():
    extra_data = {"timestamp": datetime.utcnow()}
    logger.info("crawling start.", extra=extra_data)


def log_crawling_success(url):
    extra_data = {"timestamp": datetime.utcnow()}
    logger.info(f"success - URL: {url}", extra=extra_data)


def log_http_error(url, http_err):
    extra_data = {"timestamp": datetime.utcnow()}
    logger.error(f"Not found. {http_err}", extra=extra_data)


def log_request_error(url, req_err):
    extra_data = {"timestamp": datetime.utcnow()}
    logger.error(f"fail requests: {req_err}", extra=extra_data)


def log_crawling_error(error):
    extra_data = {"timestamp": datetime.utcnow()}
    logger.error(f"fail crawling: {error}", extra=extra_data)


def log_non_dev_related(url):
    extra_data = {"timestamp": datetime.utcnow()}
    logger.info(f"this url({url})is not for developer", extra=extra_data)
