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
        tenant_id = event['queryStringParameters'].get('tenant_id')

        # Validar parámetros
        if not tenant_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True,
                },
                'body': json.dumps({'error': 'tenant_id es requerido'})
            }

        # Consultar los productos de DynamoDB para el tenant_id
        response = table.query(
            IndexName="GSI_TenantID_CategoriaNombre",  # Usamos el índice global por tenant_id
            KeyConditionExpression=Key('tenant_id').eq(tenant_id),
        )

        productos = response.get('Items', [])

        if not productos:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True,
                },
                'body': json.dumps({'error': 'No productos encontrados'})
            }

        # Obtener las URLs de las imágenes para cada producto
        lambda_client = boto3.client('lambda')
        for producto in productos:
            img_object = {
                'file_base64': producto.get('img'),
                'directory': tenant_id
            }

            invoke_response_subir_imagen = lambda_client.invoke(
                FunctionName=OBTENER_URL_LAMBDA_NAME,
                InvocationType='RequestResponse',
                Payload=json.dumps(img_object)
            )

            response_img = json.loads(invoke_response_subir_imagen['Payload'].read().decode())
            logger.info("Image URL response: %s", response_img)

            if response_img['statusCode'] == 200:
                producto['url_img'] = response_img['body']
            else:
                producto['url_img'] = None

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
        logger.error("Error obteniendo los productos: %s", str(e))
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
            },
            'body': json.dumps({
                'error': f'Error obteniendo los productos: {str(e)}'
            })
        }
