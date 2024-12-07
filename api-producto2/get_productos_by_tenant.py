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
        # Log del evento recibido
        logger.info("Received event: %s", json.dumps(event))

        # Obtener tenant_id de los parámetros de consulta
        tenant_id = event['queryStringParameters'].get('tenant_id') if event.get('queryStringParameters') else None

        if not tenant_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True,
                },
                'body': json.dumps({'error': 'tenant_id es requerido'})
            }

        # Consultar DynamoDB por tenant_id
        response = table.query(
            KeyConditionExpression=Key('tenant_id').eq(tenant_id)
        )

        productos = response.get('Items', [])

        # Inicializar cliente Lambda para obtener las URLs de las imágenes
        lambda_client = boto3.client('lambda')

        # Agregar URLs a los productos
        for producto in productos:
            try:
                # Payload para obtener la URL de la imagen
                payload = {
                    "directory": producto['tenant_id'],
                    "file_name": producto['img']
                }

                invoke_response = lambda_client.invoke(
                    FunctionName=OBTENER_URL_LAMBDA_NAME,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )

                response_img = json.loads(invoke_response['Payload'].read().decode())
                logger.info("Image URL response: %s", response_img)

                # Actualizar el producto con la URL de la imagen
                if response_img['statusCode'] == 200:
                    producto['url_img'] = response_img['body']
                else:
                    producto['url_img'] = None

            except Exception as e:
                logger.error("Error obteniendo la URL de la imagen: %s", str(e))
                producto['url_img'] = None

        # Respuesta final
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
        logger.error("Error listando productos: %s", str(e))
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
            },
            'body': json.dumps({
                'error': f'Error listando productos: {str(e)}'
            })
        }
