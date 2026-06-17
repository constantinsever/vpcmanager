import json
import boto3
from datetime import datetime, timezone
import uuid
import os


TABLE_NAME = os.environ["TABLE_NAME"]
env = os.environ.get("env", "dev")


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "http://127.0.0.1:5500",
    "Access-Control-Allow-Headers": "authorization,content-type",
    "Access-Control-Allow-Methods": "DELETE,OPTIONS"
}

def response(status, body):
    return {
        "statusCode": status,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, default=str)
    }

def get_username(event):
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    return claims.get("email") or claims.get("cognito:username") or claims.get("username") or claims.get("sub") or "unknown"

def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def lambda_handler(event, context):
    try:
        method = event.get("requestContext", {}).get("http", {}).get("method", "DELETE")

        if method == "OPTIONS":
            return response(204, {})

        username = get_username(event)
        region = (event.get("queryStringParameters") or {}).get("region", "eu-central-1")
        subnet_id = (event.get("pathParameters") or {}).get("subnet_id")

        if not subnet_id:
            return response(400, {"error": "Missing subnet_id"})

        ec2 = boto3.client("ec2", region_name=region)

        subnet_info = ec2.describe_subnets(SubnetIds=[subnet_id])["Subnets"][0]

        cidr = subnet_info.get("CidrBlock", "")
        vpc_id = subnet_info.get("VpcId", "")
        availability_zone = subnet_info.get("AvailabilityZone", "")
        name = ""

        for tag in subnet_info.get("Tags", []):
            if tag.get("Key") == "Name":
                name = tag.get("Value", "")
                break

        ec2.delete_subnet(SubnetId=subnet_id)

        item = {
            "event_id": str(uuid.uuid4()),
            "resource_type": "SUBNET",
            "resource_id": subnet_id,
            "event_type": "DELETE",
            "environment": env,
            "username": username,
            "name": name,
            "cidr": cidr,
            "region": region,
            "vpc_id": vpc_id,
            "availability_zone": availability_zone,
            "event_time": now_utc()
        }


        table.put_item(Item=item)

        return response(200, item)

    except Exception as e:
        print(str(e), flush=True)
        return response(500, {"error": "InternalServerError", "message": str(e)})