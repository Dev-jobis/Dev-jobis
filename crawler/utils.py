import boto3

ssm = boto3.client("ssm", region_name="ap-northeast-2")
parameter_name = "/SESAC/URL/RANGE"
response = ssm.get_parameter(Name=parameter_name, WithDecryption=False)  # 또는 생략 가능
URL_RANGE_value = response["Parameter"]["Value"]

print(URL_RANGE_value)
