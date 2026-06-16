import os
os.environ["AWS_EC2_METADATA_DISABLED"] = "true"

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
        log("GET VPCS STARTED")
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

        log(f"Region: {region}")

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

        log("Calling describe_vpcs")

        result = ec2.describe_vpcs()

        vpcs = []

        for vpc in result.get("Vpcs", []):
            name = ""

            for tag in vpc.get("Tags", []):
                if tag.get("Key") == "Name":
                    name = tag.get("Value", "")
                    break

            vpcs.append({
                "vpc_id": vpc.get("VpcId"),
                "name": name,
                "cidr": vpc.get("CidrBlock"),
                "state": vpc.get("State"),
                "is_default": vpc.get("IsDefault", False)
            })

        log(f"Returning {len(vpcs)} VPCs")

        return response(200, vpcs)

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