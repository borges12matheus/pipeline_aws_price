import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv()

#Testando conexão com a AWS
client = boto3.client("pricing", region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))

response = client.get_products(
    ServiceCode='AmazonEC2',
    Filters=[
        {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': 't3.micro'},
        {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': 'US East (N. Virginia)'},
        {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
        {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'}
    ],
    MaxResults=1
)

print(json.dumps(response, indent=2))