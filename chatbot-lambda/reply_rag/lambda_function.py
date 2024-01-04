import json
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
    logger.send_json_log("Start Lambda...")
    # TODO: logging - invoke 시 사용자 질문이 잘 넘어 왔는지, 누구로부터 넘어왔고, 언제 넘어왔고, 어떤 내용인지
    msg_info = event["event"]

    questioner_channel = msg_info.get("channel")
    questioner_message = msg_info.get("text")
    questioner_user_id = msg_info.get("user")
    questioner_timestamp = msg_info.get("ts")

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
        slack_client.chat_postMessage(
            channel=questioner_channel, text=ans
        )  # TODO: 마지막이 자연스럽게 나오려면?
    logger.send_json_log("Chatbot Answering Done.")
    return {"statusCode": 200, "body": json.dumps("Hello from Lambda!")}
