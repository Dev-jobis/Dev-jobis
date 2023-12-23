import boto3

s3 = boto3.client("s3")


def get_s3_object(bucket, key, is_string=False):
    obj = s3.get_object(Bucket=bucket, Key=key)["Body"]  # byte object임에 유의할 것
    return obj.read().decode("utf-8").rstrip() if is_string else obj
