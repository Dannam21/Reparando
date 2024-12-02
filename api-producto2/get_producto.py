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
                'body': json.dumps({'error': 'Producto no encontrado'})
            }

        # Retornar el producto con conversión de Decimal a float
        return {
            'statusCode': 200,
            'body': json.dumps({'producto': item}, default=decimal_default)  # Aquí se usa decimal_default
        }

    except Exception as e:
        logger.error("Error obteniendo el producto: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Error obteniendo el producto: {str(e)}'})
        }
