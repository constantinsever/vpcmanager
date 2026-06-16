import json
import boto3
import ipaddress
from datetime import datetime, timezone

TABLE_NAME = "vpcmanager_prod"

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
        vpc_id = (event.get("pathParameters") or {}).get("vpc_id")
        body = json.loads(event.get("body") or "{}")

        region = body.get("region", "eu-central-1")
        name = body.get("name")
        cidr = body.get("cidr")
        availability_zone = body.get("availability_zone")

        if not vpc_id or not name or not cidr or not availability_zone:
            return response(400, {"error": "Missing required fields"})

        subnet_network = ipaddress.ip_network(cidr)

        ec2 = boto3.client("ec2", region_name=region)

        vpc = ec2.describe_vpcs(VpcIds=[vpc_id])["Vpcs"][0]
        vpc_network = ipaddress.ip_network(vpc["CidrBlock"])

        if not subnet_network.subnet_of(vpc_network):
            return response(400, {"error": "Subnet CIDR is outside VPC CIDR"})

        existing = ec2.describe_subnets(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )

        for subnet in existing.get("Subnets", []):
            if subnet_network.overlaps(ipaddress.ip_network(subnet["CidrBlock"])):
                return response(400, {
                    "error": "Subnet CIDR overlaps existing subnet",
                    "existing_subnet_id": subnet["SubnetId"],
                    "existing_cidr": subnet["CidrBlock"]
                })

        result = ec2.create_subnet(
            VpcId=vpc_id,
            CidrBlock=cidr,
            AvailabilityZone=availability_zone
        )

        subnet_id = result["Subnet"]["SubnetId"]

        ec2.create_tags(
            Resources=[subnet_id],
            Tags=[
                {"Key": "Name", "Value": name},
                {"Key": "ManagedBy", "Value": "VpcManager"},
                {"Key": "Username", "Value": username}
            ]
        )

        item = {
            "resource_type": "SUBNET",
            "resource_id": subnet_id,
            "event_type": "CREATE",
            "username": username,
            "name": name,
            "cidr": cidr,
            "region": region,
            "vpc_id": vpc_id,
            "availability_zone": availability_zone,
            "event_time": now_utc()
        }

        table.put_item(Item=item)

        return response(201, item)

    except Exception as e:
        print(str(e), flush=True)
        return response(500, {"error": "InternalServerError", "message": str(e)})