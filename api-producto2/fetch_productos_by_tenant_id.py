import boto3
import os
import json
import logging
from boto3.dynamodb.conditions import Key
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError("Type not serializable")

def lambda_handler(event, context):
    try:
        logger.info("Received event: %s", json.dumps(event, default=decimal_default))
        
        # Obtener el tenant_id desde los parámetros de la consulta
        tenant_id = event['queryStringParameters'].get('tenant_id')

        if not tenant_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True,
                },
                'body': json.dumps({'error': 'Missing tenant_id parameter'})
            }

        # Consultar DynamoDB utilizando el GSI si necesitas filtrar por categoría
        response = table.query(
            KeyConditionExpression=Key('tenant_id').eq(tenant_id)
        )
        
        productos = response.get('Items', [])
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
            },
            'body': json.dumps({
                'productos': productos
            }, default=decimal_default)
        }

    except Exception as e:
        logger.error("Error fetching products: %s", str(e))
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
            },
            'body': json.dumps({'error': f'Error fetching products: {str(e)}'})
        }
