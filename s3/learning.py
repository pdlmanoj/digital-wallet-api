import pprint

import boto3
from dotenv import load_dotenv

load_dotenv()
import os

s3 = boto3.client(
    "s3",
    region_name=os.getenv("AWS_REGION"),
)

print(s3)
print("Listing all buckets:", s3.list_buckets())

pprint.pp(s3.list_objects_v2(Bucket="digitalwallet"), indent=4)

s3.upload_file(
    "/home/manoj/digital-wallet-api/s3/image.png",
    "digitalwallet",
    "user/s3/metadataimage.png",
    ExtraArgs={"ContentType": "image/png"},
)
print("Image uploaded successfully...........")

# s3.put_object(Bucket=, key=, Body=bytes) -> directly give actual data bytes instead of file path
# s3.upload_fileobj()  -> directly provide file object instead of converting it to bytes and then upload

with open("/home/manoj/digital-wallet-api/s3/image.png", "rb") as rb:
    image_bytes = rb.readline()
    print(image_bytes)


response = s3.get_object(Bucket="digitalwallet", Key="user/s3/metadataimage.png")
pprint.pp(response, indent=5)

print("*" * 10)
print(response.keys())
print("Content type:", response["ContentType"])
print("Content length:", response["ContentLength"])
print("Body:", response["Body"])

body = response["Body"]

image_byte = body.read()
print(len(image_byte))
print(type(image_byte))

with open("/home/manoj/digital-wallet-api/s3/image-copy.png", "wb") as wb:
    wb.write(body.read())

print("**" * 21)
bucket_list = s3.list_objects_v2(Bucket="digitalwallet")
print(bucket_list)
for _ in bucket_list["Contents"]:
    print(_)

delete = s3.delete_object(Bucket="digitalwallet", Key="user/s3/image.png")
print("Delete return response", delete)
print(bucket_list)

print("********" * 12 + "Inspecting object metadata")

print(s3.get_object(Bucket="digitalwallet", Key="user/s3/metadataimage.png"))
metadata = s3.head_object(Bucket="digitalwallet", Key="user/s3/metadataimage.png")
print(metadata)
