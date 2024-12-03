import boto3
import uuid
import os
import json
import logging
from decimal import Decimal

# Configuración de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inicialización de recursos DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
VALIDAR_TOKEN_LAMBDA_NAME = os.environ['VALIDAR_TOKEN_LAMBDA_NAME']
table = dynamodb.Table(table_name)

# Función para convertir Decimal a float
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)  # Convertir Decimal a float
    raise TypeError("Type not serializable")

def lambda_handler(event, context):
    try:
        # Log event with Decimal conversion to float
        logger.info("Received event: %s", json.dumps(event, default=decimal_default))

        # Obtener el cuerpo de la solicitud
        body = json.loads(event['body'])

        # Obtener el token de autorización
        token = event['headers'].get('Authorization')

        if not token:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Authorization token is missing'})
            }

        # Crear el cliente de Lambda para invocar la función de validación del token
        lambda_client = boto3.client('lambda')

        payload = {
            "token": token,
            "role": "admin"
        }

        invoke_response = lambda_client.invoke(
            FunctionName=VALIDAR_TOKEN_LAMBDA_NAME,  # Asegúrate de que el nombre de la función sea correcto
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        # Leer la respuesta de la validación del token
        response1 = json.loads(invoke_response['Payload'].read().decode())
        logger.info("Token validation response: %s", response1)

        if response1['statusCode'] != 200:
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Forbidden - Acceso No Autorizado'})
            }

        # Obtener los parámetros
        tenant_id = body.get('tenant_id')
        categoria_nombre = body.get('categoria_nombre')
        nombre = body.get('nombre')
        stock = body.get('stock')  # Se espera que 'stock' sea un número entero
        precio = body.get('precio')  # Se espera que 'precio' sea un número

        # Validación de parámetros obligatorios
        if not tenant_id or not categoria_nombre or not nombre or stock is None or not precio:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required data (tenant_id, categoria_nombre, nombre, stock, precio)'
                })
            }

        # Asegúrate de convertir el stock a int
        try:
            stock = int(stock)  # Convertir a entero
        except ValueError:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'El stock debe ser un número entero válido'
                })
            }

        # Asegúrate de convertir el precio a Decimal
        try:
            precio = Decimal(precio)  # Convertir a Decimal
        except ValueError:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'El precio debe ser un número válido'
                })
            }

        # Crear un nuevo ID de producto único
        producto_id = str(uuid.uuid4())

        # Crear la clave de partición utilizando tenant_id y categoria_nombre
        partition_key = f"{tenant_id}#{categoria_nombre}"

        # Crear el nuevo producto
        producto = {
            'tenant_id#categoria_nombre': partition_key,  # Clave de partición
            'producto_id': producto_id,  # Clave de ordenamiento
            'tenant_id': tenant_id,
            'categoria_nombre': categoria_nombre,
            'nombre': nombre,
            'stock': stock,  # Guardar como int
            'precio': precio  # Guardar como Decimal
        }

        # Insertar el producto en la base de datos
        table.put_item(Item=producto)

        # Responder con un mensaje de éxito, convirtiendo Decimal a float con decimal_default
        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'Producto creado',
                'producto': producto,
            }, default=decimal_default)  # Convert Decimal to float during JSON serialization
        }

    except Exception as e:
        logger.error("Error creando el producto: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Error creando el producto: {str(e)}'
            })
        }
