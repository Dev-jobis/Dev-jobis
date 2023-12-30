import boto3

ssm = boto3.client("ssm", region_name="ap-northeast-2")
parameter_name = "/SESAC/SLACK/SIGNING_SECRET"
response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)  # 복호화 옵션
SLACK_SIGNING_SECRET = response["Parameter"]["Value"]

parameter_name = "/SESAC/SLACK/BOT_TOKEN"
response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)  # 복호화 옵션
SLACK_BOT_TOKEN = response["Parameter"]["Value"]
