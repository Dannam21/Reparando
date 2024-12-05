import boto3
import uuid
import os
import json
import logging
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
VALIDAR_TOKEN_LAMBDA_NAME = os.environ['VALIDAR_TOKEN_LAMBDA_NAME']
SUBIR_IMAGENES_LAMBDA_NAME = os.environ['SUBIR_IMAGENES_LAMBDA_NAME']
table = dynamodb.Table(table_name)

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError("Type not serializable")

def lambda_handler(event, context):
    try:
        logger.info("Received event: %s", json.dumps(event, default=decimal_default))

        body = json.loads(event['body'])
        token = event['headers'].get('Authorization')

        if not token:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Authorization token is missing'})
            }

        lambda_client = boto3.client('lambda')

        payload = {
            "token": token,
            "role": "admin"
        }

        invoke_response = lambda_client.invoke(
            FunctionName=VALIDAR_TOKEN_LAMBDA_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        response1 = json.loads(invoke_response['Payload'].read().decode())
        logger.info("Token validation response: %s", response1)

        if response1['statusCode'] != 200:
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Forbidden - Acceso No Autorizado'})
            }

        tenant_id = body.get('tenant_id')
        categoria_nombre = body.get('categoria_nombre')
        nombre = body.get('nombre')
        img = body.get('img')
        stock = body.get('stock')
        precio = body.get('precio')

        if not tenant_id or not categoria_nombre or not nombre or not img or stock is None or not precio:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required data (tenant_id, categoria_nombre, nombre, stock, precio)'
                })
            }

        try:
            stock = int(stock)
        except ValueError:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'El stock debe ser un número entero válido'
                })
            }

        try:
            precio = Decimal(precio)
        except ValueError:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'El precio debe ser un número válido'
                })
            }

        producto_id = str(uuid.uuid4())
        partition_key = f"{tenant_id}#{categoria_nombre}"

        img_object = {
            'file_base64': img,
            'directory': tenant_id
        }

        invoke_response_subir_imagen = lambda_client.invoke(
            FunctionName=SUBIR_IMAGENES_LAMBDA_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(img_object)
        )

        response_img = json.loads(invoke_response_subir_imagen['Payload'].read().decode())
        logger.info("Image upload response: %s", response_img)

        if response_img['statusCode'] != 200:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': f'Error al subir imagen: {str(e)}'
                })
            }

        img = response_img['body']
        producto = {
            'tenant_id#categoria_nombre': partition_key,
            'producto_id': producto_id,
            'tenant_id': tenant_id,
            'categoria_nombre': categoria_nombre,
            'nombre': nombre,
            'img': img,
            'stock': stock,
            'precio': precio
        }

        table.put_item(Item=producto)

        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'Producto creado',
                'producto': producto,
            }, default=decimal_default)
        }

    except Exception as e:
        logger.error("Error creando el producto: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Error creando el producto: {str(e)}'
            })
        }
