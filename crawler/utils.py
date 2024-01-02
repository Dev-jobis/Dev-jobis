import boto3

ssm = boto3.client("ssm", region_name="ap-northeast-2")
parameter_name = "/SESAC/URL/RANGE"
response = ssm.get_parameter(Name=parameter_name, WithDecryption=False)
URL_RANGE_value = response["Parameter"]["Value"]
