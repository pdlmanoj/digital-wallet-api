import boto3
from botocore.config import Config

from apps.core.config import awscredentials


def build_s3_client():
    client = boto3.client(
        "s3",
        region_name=awscredentials.aws_region,
        endpoint_url=awscredentials.aws_endpoint_url,
        aws_access_key_id=awscredentials.aws_access_key_id,
        aws_secret_access_key=awscredentials.aws_secret_access_key,
        config=Config(signature_version="s3v4"),
    )
    return client
