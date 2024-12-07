import boto3
import os
import json
import logging
from boto3.dynamodb.conditions import Key
from decimal import Decimal

# Configuración de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inicialización de recursos DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
OBTENER_URL_LAMBDA_NAME = os.environ['OBTENER_URL_LAMBDA_NAME']
table = dynamodb.Table(table_name)

# Función para convertir Decimal a float
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError("Type not serializable")

def lambda_handler(event, context):
    try:
        # Log event for debugging
        logger.info("Received event: %s", json.dumps(event))

        # Obtener los parámetros de la ruta
        tenant_id = event['pathParameters']['tenant_id']
        producto_id = event['pathParameters']['producto_id']

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

        # Invocar la Lambda para obtener la URL de la imagen
        lambda_client = boto3.client('lambda')
        img_object = {
            'object_name': item['img'],
        }

        invoke_obtener_url = lambda_client.invoke(
            FunctionName=OBTENER_URL_LAMBDA_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(img_object)
        )

        response_url = json.loads(invoke_obtener_url['Payload'].read().decode())
        logger.info("Image upload response: %s", response_url)

        if response_url['statusCode'] != 200:
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True, 
                },
                'body': json.dumps({
                    'error': 'Error al obtener imagen'
                })
            }

        # La URL que queremos incluir debe ser la URL completa con el parámetro de firma
        item['url_img'] = response_url['url']  # Suponiendo que esta URL contiene la firma de acceso

        # Formatear el objeto de respuesta según el formato exacto requerido
        response_body = {
            "producto": {
                "img": item.get("img"),
                "categoria_nombre": item.get("categoria_nombre"),
                "nombre": item.get("nombre"),
                "tenant_id": item.get("tenant_id"),
                "stock": float(item.get("stock", 0)),
                "producto_id": item.get("producto_id"),
                "precio": float(item.get("precio", 0)),
                "tenant_id#categoria_nombre": f"{item.get('tenant_id')}#{item.get('categoria_nombre')}",
                "url_img": item.get("url_img")  # Aquí ya está la URL completa con firma
            }
        }

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True, 
            },
            'body': json.dumps(response_body, default=decimal_default)
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
