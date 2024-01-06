import json
import boto3
import hmac
import hashlib
from datetime import datetime
import logging
from log_to_kafka import CustomLogger
from utils import SLACK_SIGNING_SECRET

logger = CustomLogger("lambda-slack-01")


def lambda_handler(event, context):
    if "X-Slack-Signature" not in event["headers"]:
        logger.send_json_log(
            message="Not from Slack",
            log_level=logging.WARNING,
            timestamp=datetime.utcnow(),
        )
        return {
            "statusCode": 400,
            "headers": {"Content-type": "application/json", "X-Slack-No-Retry": "1"},
        }
    request_body = event["body"]
    time_stamp = event["headers"]["X-Slack-Request-Timestamp"]  # str

    # bot message not accept
    request_body_dict = json.loads(request_body)
    if (
        request_body_dict["event"].get("bot_id")
        and request_body_dict["event"].get("user") == "U06CSU56FHA"
    ):  # bot user id
        return {
            "statusCode": 400,
            "headers": {"Content-type": "application/json", "X-Slack-No-Retry": "1"},
        }

    if abs(datetime.now().timestamp() - int(time_stamp)) > 60 * 5:
        # The request timestamp is more than five minutes from local time.
        # It could be a replay attack, so let's ignore it.
        logger.send_json_log(
            message="Time Not Match.",
            log_level=logging.WARNING,
            timestamp=datetime.utcnow(),
        )
        return {
            "statusCode": 400,
            "headers": {"Content-type": "application/json", "X-Slack-No-Retry": "1"},
        }

    sig_basestring = "v0:" + time_stamp + ":" + request_body
    byte_key = bytes(
        SLACK_SIGNING_SECRET, "UTF-8"
    )  # key.encode() would also work in this case
    message = sig_basestring.encode()

    # now use the hmac.new function and the hexdigest method
    my_signature = "v0=" + hmac.new(byte_key, message, hashlib.sha256).hexdigest()
    x_slack_signature = event["headers"]["X-Slack-Signature"]
    if hmac.compare_digest(my_signature, x_slack_signature):
        logger.send_json_log(
            message="Chatbot Get Query",
            log_level=logging.INFO,
            timestamp=datetime.utcnow(),
        )

        lambda_client = boto3.client("lambda")
        response = lambda_client.invoke(
            FunctionName="chat_to_slack",
            InvocationType="Event",  # async
            LogType="None",
            ClientContext="frompythontest",
            Payload=bytes(request_body, "utf-8"),
        )
        logger.send_json_log(
            message="Chatbot Lambda Invoke Done.", timestamp=datetime.utcnow()
        )
        return {
            "statusCode": 200,
            "headers": {"Content-type": "application/json", "X-Slack-No-Retry": "1"},
            "body": "DONE",
        }
