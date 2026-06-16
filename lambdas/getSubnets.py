import json
import boto3
import traceback
import time
from botocore.config import Config
from botocore.exceptions import ClientError


CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "http://127.0.0.1:5500",
    "Access-Control-Allow-Headers": "authorization,content-type",
    "Access-Control-Allow-Methods": "GET,OPTIONS"
}


def log(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body)
    }


def lambda_handler(event, context):
    try:
        log("GET SUBNETS STARTED")
        log(json.dumps(event))

        method = (
            event.get("requestContext", {})
                 .get("http", {})
                 .get("method", "GET")
        )

        if method == "OPTIONS":
            return response(200, {})

        query = event.get("queryStringParameters") or {}
        region = query.get("region", "eu-central-1")

        path_params = event.get("pathParameters") or {}
        vpc_id = path_params.get("vpc_id")

        if not vpc_id:
            return response(400, {
                "error": "Missing vpc_id"
            })

        log(f"Region: {region}")
        log(f"VPC ID: {vpc_id}")

        config = Config(
            connect_timeout=3,
            read_timeout=10,
            retries={"max_attempts": 1}
        )

        log("Creating EC2 client")

        ec2 = boto3.client(
            "ec2",
            region_name=region,
            config=config
        )

        log("Calling describe_subnets")

        result = ec2.describe_subnets(
            Filters=[
                {
                    "Name": "vpc-id",
                    "Values": [vpc_id]
                }
            ]
        )

        subnets = []

        for subnet in result.get("Subnets", []):
            name = ""

            for tag in subnet.get("Tags", []):
                if tag.get("Key") == "Name":
                    name = tag.get("Value", "")
                    break

            subnets.append({
                "subnet_id": subnet.get("SubnetId"),
                "vpc_id": subnet.get("VpcId"),
                "name": name,
                "cidr": subnet.get("CidrBlock"),
                "availability_zone": subnet.get("AvailabilityZone"),
                "state": subnet.get("State"),
                "available_ip_count": subnet.get("AvailableIpAddressCount")
            })

        log(f"Returning {len(subnets)} subnets")

        return response(200, subnets)

    except ClientError as e:
        log("AWS CLIENT ERROR")
        log(str(e))
        log(traceback.format_exc())

        return response(500, {
            "error": e.response["Error"]["Code"],
            "message": e.response["Error"]["Message"]
        })

    except Exception as e:
        log("GENERAL ERROR")
        log(str(e))
        log(traceback.format_exc())

        return response(500, {
            "error": "InternalServerError",
            "message": str(e)
        })