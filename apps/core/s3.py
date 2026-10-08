import boto3

from apps.core.config import awscredentials


def build_s3_client():
    client = boto3.client("s3", region_name=awscredentials.aws_region)
    return client
