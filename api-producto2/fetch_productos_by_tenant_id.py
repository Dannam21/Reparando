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

        # Obtener el tenant_id de la ruta de la API
        path_params = event.get('pathParameters', {})
        tenant_id = path_params.get('tenant_id')

        # Validar tenant_id
        if not tenant_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True,
                },
                'body': json.dumps({'error': 'tenant_id es requerido'})
            }

        # Consultar los productos de DynamoDB por tenant_id
        response = table.query(
            KeyConditionExpression=Key('tenant_id').eq(tenant_id)
        )

        # Validar que haya productos
        if 'Items' not in response or len(response['Items']) == 0:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True,
                },
                'body': json.dumps({'error': 'No se encontraron productos para este tenant_id'})
            }

        # Procesar los productos y obtener la URL de la imagen
        productos = response['Items']
        lambda_client = boto3.client('lambda')

        productos_con_url = []
        for producto in productos:
            # Obtener la URL de la imagen usando el Lambda
            img_object = {
                'file_base64': producto['img'],  # Asumiendo que 'img' contiene la base64 de la imagen
                'directory': tenant_id
            }

            invoke_response_subir_imagen = lambda_client.invoke(
                FunctionName=OBTENER_URL_LAMBDA_NAME,
                InvocationType='RequestResponse',
                Payload=json.dumps(img_object)
            )

            response_img = json.loads(invoke_response_subir_imagen['Payload'].read().decode())
            logger.info("Image URL response: %s", response_img)

            # Agregar la URL de la imagen al producto
            if response_img['statusCode'] == 200:
                producto['url_img'] = response_img['body']  # Asumiendo que la URL está en 'body'
                productos_con_url.append(producto)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
            },
            'body': json.dumps({'productos': productos_con_url}, default=decimal_default)
        }

    except Exception as e:
        logger.error("Error obteniendo productos: %s", str(e))
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
            },
            'body': json.dumps({'error': f'Error obteniendo productos: {str(e)}'})
        }
