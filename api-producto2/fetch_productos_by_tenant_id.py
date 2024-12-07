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
        # Log event for debugging
        logger.info("Received event: %s", json.dumps(event))

        # Obtener los parámetros de la ruta
        tenant_id = event['pathParameters'].get('tenant_id')
        producto_id = event['pathParameters'].get('producto_id')

        # Validar parámetros
        if not tenant_id or not producto_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True,
                },
                'body': json.dumps({'error': 'tenant_id y producto_id son requeridos'})
            }

        # Consultar el producto en DynamoDB
        response = table.get_item(
            Key={
                'tenant_id': tenant_id,
                'producto_id': producto_id
            }
        )

        # Verificar si se encontró el producto
        item = response.get('Item')
        if not item:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True,
                },
                'body': json.dumps({'error': 'Producto no encontrado'})
            }

        # Verificar que el producto tenga una imagen asociada
        img_name = item.get('img')
        if not img_name:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True,
                },
                'body': json.dumps({'error': 'Imagen no asociada al producto'})
            }

        # Invocar la Lambda para obtener la URL de la imagen
        lambda_client = boto3.client('lambda')
        invoke_response = lambda_client.invoke(
            FunctionName=OBTENER_URL_LAMBDA_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps({'object_name': img_name})
        )

        response_payload = json.loads(invoke_response['Payload'].read().decode())
        logger.info("Image URL response: %s", response_payload)

        if response_payload.get('statusCode') != 200:
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True,
                },
                'body': json.dumps({'error': 'Error al obtener la URL de la imagen'})
            }

        # Agregar la URL de la imagen al producto
        item['url_img'] = response_payload['url']

        # Retornar el producto con conversión de Decimal a float
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
            },
            'body': json.dumps({'producto': item}, default=decimal_default)
        }

    except Exception as e:
        logger.error("Error obteniendo el producto: %s", str(e))
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
            },
            'body': json.dumps({'error': f'Error obteniendo el producto: {str(e)}'})
        }
