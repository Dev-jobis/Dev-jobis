import boto3

ssm = boto3.client("ssm", region_name="ap-northeast-2")
parameter_name = "/SESAC/SLACK/SIGNING_SECRET"
response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)  # 복호화 옵션
SLACK_SIGNING_SECRET = response["Parameter"]["Value"]
