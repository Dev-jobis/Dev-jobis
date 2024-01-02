import boto3

ssm = boto3.client("ssm", region_name="ap-northeast-2")

parameter_name = "/SESAC/OPENAI/API_KEY"
response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
OPENAI_API_KEY = response["Parameter"]["Value"]

parameter_name = "/SESAC/PINECONE/API_KEY"
response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
PINECONE_API_KEY = response["Parameter"]["Value"]
