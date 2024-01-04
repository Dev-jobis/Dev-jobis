import boto3
import json
from langchain.schema import Document
import tempfile


s3_resource = boto3.resource("s3")
s3_client = boto3.client("s3")
bucket_name = "project05-crawling"
prefix = "test_json"  # For test
bucket = s3_resource.Bucket(bucket_name)


def make_file_to_doc(file_path):
    """
    S3에서 다운로든 받은 파일을 파싱하여 Langchain Document로 만든다.
    Document는 텍스트인 page_content, 그 외 정보를 dictionary로 하는 metadata를 가지고 있다.
    """

    with open(file_path, "r") as f:
        lines = f.readlines()
        for line in lines:  # line 하나가 jsoon으로 된 공고 하나
            line_dict = json.loads(line)
            print(line_dict["title"])
            # print(line_dict["contents"])
            doc = Document(
                page_content=" ".join(line_dict["contents"]),
                metadata={
                    "title": line_dict["title"],
                    "url": line_dict["url"],
                    "job_category": line_dict["job_category"],
                    "workplace": line_dict["workplace"],
                    "technology_stack": line_dict["technology_stack"],
                },
            )
            yield doc


def S3_bucket_file_loader(bucket_name, prefix):
    """
    S3에서 임베딩할 파일들을 임시 디렉토리로 다운로드 받고, 해당 파일을 doc으로 만드는 과정을 포함한다.
    """
    docs = []
    with tempfile.TemporaryDirectory() as temp_dir:
        print("temporary directory : ", temp_dir)
        for obj in bucket.objects.filter(Prefix=prefix):
            file_path = f"{temp_dir}/{obj.key}"
            response = s3_client.download_file(
                Bucket=bucket_name, Key=obj.key, Filename=file_path
            )
            doc_generator = make_file_to_doc(file_path)
            for doc in doc_generator:
                docs.append(doc)

    return docs