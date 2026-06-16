import json
import boto3
from datetime import datetime, timezone

TABLE_NAME = "vpcmanager_prod"

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
        vpc_id = (event.get("pathParameters") or {}).get("vpc_id")

        if not vpc_id:
            return response(400, {"error": "Missing vpc_id"})

        ec2 = boto3.client("ec2", region_name=region)

        vpc_info = ec2.describe_vpcs(VpcIds=[vpc_id])["Vpcs"][0]
        cidr = vpc_info.get("CidrBlock", "")
        name = ""

        for tag in vpc_info.get("Tags", []):
            if tag.get("Key") == "Name":
                name = tag.get("Value", "")
                break

        ec2.delete_vpc(VpcId=vpc_id)

        item = {
            "resource_type": "VPC",
            "resource_id": vpc_id,
            "event_type": "DELETE",
            "username": username,
            "name": name,
            "cidr": cidr,
            "region": region,
            "event_time": now_utc()
        }

        table.put_item(Item=item)

        return response(200, item)

    except Exception as e:
        print(str(e), flush=True)
        return response(500, {"error": "InternalServerError", "message": str(e)})