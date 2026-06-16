import json
import boto3
import traceback
from decimal import Decimal


TABLE_NAME = "vpcmanager_prod" 


CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "http://127.0.0.1:5500",
    "Access-Control-Allow-Headers": "authorization,content-type",
    "Access-Control-Allow-Methods": "GET,DELETE,OPTIONS"
}

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def json_default(value):
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)

    return str(value)


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, default=json_default)
    }


def lambda_handler(event, context):
    try:
        print("AUDIT EVENT:")
        print(json.dumps(event), flush=True)

        method = (
            event.get("requestContext", {})
                 .get("http", {})
                 .get("method", "GET")
        )

        if method == "OPTIONS":
            return response(204, {})

        if method == "GET":
            return list_events()

        if method == "DELETE":
            return clear_events()

        return response(405, {
            "error": "MethodNotAllowed",
            "message": f"Unsupported method: {method}"
        })

    except Exception as e:
        print("AUDIT ERROR:")
        print(str(e), flush=True)
        print(traceback.format_exc(), flush=True)

        return response(500, {
            "error": "InternalServerError",
            "message": str(e)
        })


def list_events():
    items = []
    scan_args = {}

    while True:
        result = table.scan(**scan_args)
        items.extend(result.get("Items", []))

        if "LastEvaluatedKey" not in result:
            break

        scan_args["ExclusiveStartKey"] = result["LastEvaluatedKey"]

    items.sort(
        key=lambda x: x.get("event_time", ""),
        reverse=True
    )

    return response(200, items)


def clear_events():
    deleted_count = 0
    scan_args = {}

    while True:
        result = table.scan(**scan_args)
        items = result.get("Items", [])

        with table.batch_writer() as batch:
            for item in items:
                resource_type = item.get("resource_type")
                resource_id = item.get("resource_id")

                if not resource_type or not resource_id:
                    print("Skipping item without key:")
                    print(json.dumps(item, default=json_default), flush=True)
                    continue

                batch.delete_item(
                    Key={
                        "resource_type": resource_type,
                        "resource_id": resource_id
                    }
                )

                deleted_count += 1

        if "LastEvaluatedKey" not in result:
            break

        scan_args["ExclusiveStartKey"] = result["LastEvaluatedKey"]

    return response(200, {
        "message": "Audit events cleared",
        "deleted_count": deleted_count
    })