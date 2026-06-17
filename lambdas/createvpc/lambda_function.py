import json
import boto3
import ipaddress
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
    "Access-Control-Allow-Methods": "POST,OPTIONS"
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
        method = event.get("requestContext", {}).get("http", {}).get("method", "POST")

        if method == "OPTIONS":
            return response(204, {})

        username = get_username(event)
        body = json.loads(event.get("body") or "{}")

        region = body.get("region", "eu-central-1")
        name = body.get("name")
        cidr = body.get("cidr")

        if not name or not cidr:
            return response(400, {"error": "Missing name or cidr"})

        ipaddress.ip_network(cidr)

        ec2 = boto3.client("ec2", region_name=region)
        result = ec2.create_vpc(CidrBlock=cidr)

        vpc_id = result["Vpc"]["VpcId"]

        ec2.create_tags(
            Resources=[vpc_id],
            Tags=[
                {"Key": "Name", "Value": name},
                {"Key": "ManagedBy", "Value": "VpcManager"},
                {"Key": "Username", "Value": username}
            ]
        )

        item = {
            "event_id": str(uuid.uuid4()),
            "resource_type": "VPC",
            "event_type": "CREATE",
            "environment": env,
            "username": username,
            "name": name,
            "cidr": cidr,
            "region": region,
            "vpc_id": vpc_id,
            "event_time": now_utc()
        }

        table.put_item(Item=item)

        return response(201, item)

    except Exception as e:
        print(str(e), flush=True)
        return response(500, {"error": "InternalServerError", "message": str(e)})