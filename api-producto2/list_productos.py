import boto3
import os
import json
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    try:
        tenant_id = event['queryStringParameters'].get('tenant_id')
        limit = int(event['queryStringParameters'].get('limit', 10))

        if not tenant_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True,
                },
                'body': json.dumps({'error': 'tenantID es requerido'})
            }

        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('tenant_id').eq(tenant_id),
            Limit=limit
        )

        items = response.get('Items', [])

        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {key: decimal_to_float(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [decimal_to_float(item) for item in obj]
            else:
                return obj

        items = decimal_to_float(items)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
            },
            'body': json.dumps({
                'productos': items
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
            },
            'body': json.dumps({
                'error': f'Ocurrió un error al obtener los productos: {str(e)}'
            })
        }
