import boto3
import uuid
import datetime
import os
import json  # Importar json para deserializar el cuerpo si es necesario
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    try:
        # Obtener el token de autorización del encabezado
        token = event['headers'].get('Authorization')
        if not token:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Authorization token is missing'})
            }

        # Validar el token y verificar el rol
        lambda_client = boto3.client('lambda')
        payload = {
            "token": token,
            "role": "admin"
        }

        # Invocar la función de validación de token
        invoke_response = lambda_client.invoke(
            FunctionName="api-usuarios-dev-ValidarTokenAcceso",  # Cambia al nombre correcto de tu función
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        # Leer la respuesta de la validación del token
        response1 = json.loads(invoke_response['Payload'].read().decode())
        
        # Log para depurar la respuesta
        logger.info(f"Respuesta de validación de token: {response1}")

        # Verificar si el token es válido
        if response1.get('statusCode') != 200:
            logger.error("El token no es válido o no tiene permisos de administrador")
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Forbidden - Solo los administradores pueden crear categorías'})
            }

        # Obtener el cuerpo de la solicitud
        body = event['body']
        
        # Verificar si 'body' es una cadena JSON, y si es así, convertirla a diccionario
        if isinstance(body, str):
            body = json.loads(body)  # Deserializar el string JSON en un diccionario
        
        # Extraer los datos del cuerpo deserializado
        tenant_id = body['tenant_id']
        categoria_id = str(uuid.uuid4())
        nombre = body['nombre']
        fecha_creacion = datetime.datetime.utcnow().isoformat()
        data = body.get('data')

        # Crear el objeto de categoría que se va a guardar en DynamoDB
        categoria = {
            'tenant_id': tenant_id,
            'categoria_id': categoria_id,
            'nombre': nombre,
            'data': data
        }

        # Guardar el objeto de categoría en DynamoDB
        response = table.put_item(Item=categoria)

        # Retornar una respuesta exitosa
        return {
            'statusCode': 201,
            'body': json.dumps({  # Asegurarse de que el cuerpo de la respuesta esté serializado en JSON
                'message': 'Categoría creada',
                'categoria_id': categoria_id
            })
        }

    except Exception as e:
        # Manejar errores de ejecución
        logger.error(f"Error creando la categoría: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Error creando la categoría: {str(e)}'})
        }
