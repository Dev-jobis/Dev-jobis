import boto3

ssm = boto3.client("ssm", region_name="ap-northeast-2")
parameter_name = "/SESAC/URL/RANGE"
response = ssm.get_parameter(Name=parameter_name, WithDecryption=False)
START_URL_NUMBER = int(response["Parameter"]["Value"])
URL_RANGE = 20


def update_start_url_number(update_value: str):
    response = ssm.put_parameter(
        Name=parameter_name,
        Value=update_value,
        Type="String",
        Overwrite=True,
    )
    return response
