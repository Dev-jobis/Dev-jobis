import boto3

ssm = boto3.client("ssm", region_name="ap-northeast-2")
dynamodb = boto3.resource("dynamodb")
dynamo_table = dynamodb.Table("wanted_url")

parameter_name = "/SESAC/URL/RANGE"
response = ssm.get_parameter(Name=parameter_name, WithDecryption=False)
URL_RANGE = 20  # int(response["Parameter"]["Value"])  # 3000


def update_start_url_number(update_value: str):
    response = ssm.put_parameter(
        Name=parameter_name,
        Value=update_value,
        Type="String",
        Overwrite=True,
    )
    return response


def put_url_to_dynamo_wanted_url(base_url: str, url_number: int):
    response = dynamo_table.put_item(
        Item={"base_url": base_url, "url_number": url_number}
    )
    return response


def check_url_in_dynamo_wanted_url(base_url: str, url_number: int):
    response = dynamo_table.get_item(
        Key={"base_url": base_url, "url_number": url_number}
    )
    if response["Items"]:
        return True
    else:
        return False


def get_max_url_from_dynamo_wanted_url():
    """
    wanted_url 테이블에 있는 url 중 가장 최신의 것 - url_number가 제일 큰 것을 리턴
    만약 테이블이 비어 있으면 None을 리턴
    """
    response = dynamo_table.query(
        IndexName="base_url-url_number-index",
        KeyConditionExpression=boto3.dynamodb.conditions.Key("base_url").eq(
            "https://www.wanted.co.kr/wd/"
        ),
        ScanIndexForward=False,  # 내림차순 정렬
        Limit=1,  # 최대값만 반환
    )
    if response["Items"]:
        max_item = response["Items"][0]
        return int(max_item["url_number"])
    else:
        return None
