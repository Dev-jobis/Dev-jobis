import json
import boto3
import hmac
import hashlib
from datetime import datetime


s3 = boto3.client("s3")


def get_s3_object(bucket, key, is_string=False):
    obj = s3.get_object(Bucket=bucket, Key=key)["Body"]  # byte object임에 유의할 것
    return obj.read().decode("utf-8").rstrip() if is_string else obj


def lambda_handler(event, context):
    print("CHAT RECEIVED EVENT: ", event)

    if "X-Slack-Signature" not in event["headers"]:
        print("not from slack")  # TODO: logging으로 교체
        return {
            "statusCode": 400,
            "headers": {"Content-type": "application/json", "X-Slack-No-Retry": "1"},
        }
    slack_signing_secret = get_s3_object(
        "project05-credentials", "slack_signing_secret", is_string=True
    )  # TODO: parameter store로 변경
    request_body = event["body"]
    time_stamp = event["headers"]["X-Slack-Request-Timestamp"]  # str

    # bot message not accept
    request_body_dict = json.loads(request_body)
    if (
        request_body_dict["event"].get("bot_id")
        and request_body_dict["event"].get("user") == "U06AHBG5DK4"
    ):  # bot user id
        return {
            "statusCode": 400,
            "headers": {"Content-type": "application/json", "X-Slack-No-Retry": "1"},
        }

    if abs(datetime.now().timestamp() - int(time_stamp)) > 60 * 5:
        # The request timestamp is more than five minutes from local time.
        # It could be a replay attack, so let's ignore it.
        print("time not match")  # TODO: logging으로 교체
        return {
            "statusCode": 400,
            "headers": {"Content-type": "application/json", "X-Slack-No-Retry": "1"},
        }

    sig_basestring = "v0:" + time_stamp + ":" + request_body
    byte_key = bytes(
        slack_signing_secret, "UTF-8"
    )  # key.encode() would also work in this case
    message = sig_basestring.encode()

    # now use the hmac.new function and the hexdigest method
    my_signature = "v0=" + hmac.new(byte_key, message, hashlib.sha256).hexdigest()
    x_slack_signature = event["headers"]["X-Slack-Signature"]
    if hmac.compare_digest(my_signature, x_slack_signature):
        print("match")  # TODO: logging으로 교체
        lambda_client = boto3.client("lambda")
        response = lambda_client.invoke(
            FunctionName="chat_to_slack",
            InvocationType="Event",  # async
            LogType="None",
            ClientContext="frompythontest",
            Payload=bytes(request_body, "utf-8"),
        )
        return {
            "statusCode": 200,
            "headers": {"Content-type": "application/json", "X-Slack-No-Retry": "1"},
            "body": "DONE",
        }
