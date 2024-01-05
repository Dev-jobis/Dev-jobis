import json
from datetime import datetime
import time
from slack_bolt import App
from rag import WantedChatBot
from log_to_kafka import CustomLogger
from utils import SLACK_SIGNING_SECRET, SLACK_BOT_TOKEN


app = App(
    token=SLACK_BOT_TOKEN,  # bot user token
    signing_secret=SLACK_SIGNING_SECRET,
)
slack_client = app.client

logger = CustomLogger("lambda-slack-02")


def lambda_handler(event, context):
    logger.send_json_log("Start Lambda...", timestamp=datetime.utcnow())
    msg_info = event["event"]

    questioner_channel = msg_info.get("channel")
    questioner_message = msg_info.get("text")
    questioner_user_id = msg_info.get("user")
    questioner_timestamp = int(event.get("event_time"))

    index_name = "test-metadata"
    primer = f"""
    You are Q&A bot. A highly intelligent system that answers
    user questions based on the information provided by the user above
    each question.
    Your task is to help Job seeker and applicants get information about jobs
    they are finding.
    If the information can not be found in the information
    provided by the user you truthfully say "I don't know".
    Your answer should be in Korean.
    """
    chatbot = WantedChatBot(index_name, questioner_message, primer, 3)
    response = chatbot.answer
    ans = ""
    i = 0
    for res in response:
        ans += res
        i += 1
        if i > 30 and ans[-1] in [" ", ",", ".", "\n"]:
            slack_client.chat_postMessage(channel=questioner_channel, text=ans)
            i = 0
            ans = ""
    if ans != "":
        slack_client.chat_postMessage(channel=questioner_channel, text=ans)
    logger.send_json_log(
        "Chatbot Answering Done.",
        timestamp=datetime.utcnow(),
        extra_data={
            "duration_sec": time.time() - questioner_timestamp,
            "user": questioner_user_id,
            "query": questioner_message,
        },
    )
    return {"statusCode": 200, "body": json.dumps("Hello from Lambda!")}
