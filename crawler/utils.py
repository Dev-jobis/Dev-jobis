import boto3

ssm = boto3.client("ssm", region_name="ap-northeast-2")
parameter_name = "/SESAC/URL/RANGE"

response = ssm.get_parameter(Name=parameter_name, WithDecryption=False)
url_range_value = response["Parameter"]["Value"]

new_url_range_value = str(int(url_range_value) + 200)

response_put = ssm.put_parameter(
    Name=parameter_name,
    Value=new_url_range_value,
    Type="String",
    Overwrite=True,
)
